# investor_guided_discovery.py

import json
from typing import Dict, List

from agentic_company_research import (
    run_agentic_company_research,
    call_gemini,
    call_perplexity
)

# =========================================================
# HELPERS (DEFENSIVE PARSING)
# =========================================================

def safe_json(text: str, default):
    if not text:
        return default

    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except Exception:
        return default


def extract_list(text: str) -> List[str]:
    if not text:
        return []

    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(x).strip() for x in data if x]
    except Exception:
        pass

    # fallback: bullets / lines
    items = []
    for line in text.splitlines():
        line = line.strip("•- ").strip()
        if 2 <= len(line) <= 60:
            items.append(line)

    return items


# =========================================================
# INVESTOR-GUIDED DISCOVERY (NEW, NATURAL VERSION)
# =========================================================

def investor_guided_discovery(
    confidence_threshold: float = 0.75,
    max_turns: int = 5,
    auto_research_limit: int = 3
) -> Dict:
    """
    Conversational, free-flowing investor discovery agent.
    """

    conversation = []
    investor_thesis = {
        "summary": "",
        "constraints": {},
        "preferences": {},
        "confidence": 0.0
    }

    # =====================================================
    # CONVERSATIONAL DISCOVERY LOOP
    # =====================================================
    for turn in range(1, max_turns + 1):

        prompt = f"""
You are a senior investment advisor speaking to an investor.

Conversation so far:
{json.dumps(conversation, indent=2)}

Current investor thesis:
{json.dumps(investor_thesis, indent=2)}

TASK:
1. Ask ONE natural, conversational question.
2. Adapt to previous answers.
3. Sound human, not like a form.
4. Output ONLY the question text.
"""

        question = call_gemini(prompt).strip()
        print(f"\n[Advisor]: {question}")
        answer = input("Investor: ").strip()

        conversation.append({
            "question": question,
            "answer": answer
        })

        # ---- Update thesis ----
        update_prompt = f"""
You are refining an investor thesis.

Conversation:
{json.dumps(conversation, indent=2)}

Current thesis:
{json.dumps(investor_thesis, indent=2)}

TASK:
1. Update the thesis summary in natural language.
2. Extract constraints and preferences if evident.
3. Estimate confidence (0–1).

Return VALID JSON with keys:
- summary
- constraints
- preferences
- confidence
"""

        updated = safe_json(
            call_gemini(update_prompt),
            investor_thesis
        )

        investor_thesis.update(updated)

        if investor_thesis.get("confidence", 0) >= confidence_threshold:
            break

    # =====================================================
    # MARKET GROUNDING (PERPLEXITY)
    # =====================================================
    grounding_prompt = f"""
Given this investor thesis, identify realistic categories of companies
that exist in the current market.

Investor thesis:
{json.dumps(investor_thesis, indent=2)}

Focus on:
- Stability vs growth
- Sector fit
- Time horizon
- Risk profile
"""

    market_context = call_perplexity(grounding_prompt)

    # =====================================================
    # COMPANY SHORTLISTING
    # =====================================================
    shortlist_prompt = f"""
You are an investment sourcing analyst.

Investor thesis:
{json.dumps(investor_thesis, indent=2)}

Market context:
{market_context}

TASK:
Propose {auto_research_limit} REAL companies that strongly match.
Return ONLY a list of company names.
"""

    companies = extract_list(call_gemini(shortlist_prompt))

    if not companies:
        raise RuntimeError("Failed to identify suitable companies")

    # =====================================================
    # AGENTIC RESEARCH (UNCHANGED)
    # =====================================================
    research = {}
    for company in companies[:auto_research_limit]:
        research[company] = run_agentic_company_research(company)

    # =====================================================
    # NORMALIZE RESEARCH (HIDE INTERNAL INFERENCE LANGUAGE)
    # =====================================================
    clean_research = normalize_research_dict(research)

    # =====================================================
    # FINAL SYNTHESIS (BEST-EFFORT, DECISIVE)
    # =====================================================
    synthesis_prompt = f"""
IMPORTANT:
- Do NOT refuse to rank companies solely due to inferred data.
- Assume inferred data is acceptable for exploratory analysis.
- Focus on RELATIVE fit, not absolute certainty.
- Provide a best-effort recommendation.
- Do NOT mention data quality disclaimers.
- Do NOT mention inferred or missing data.

Investor thesis:
{json.dumps(investor_thesis, indent=2)}

Company research:
{json.dumps(clean_research, indent=2)}

TASK:
1. Rank companies by suitability.
2. Score each (0–10).
3. Explain reasoning.
4. Recommend next actions.

Return VALID JSON with keys:
- ranking
- company_scores
- rationale
- next_actions
"""


    # =====================================================
    # FINAL SYNTHESIS
    # ==================================================

    final_analysis = safe_json(
        call_gemini(synthesis_prompt),
        {}
    )

    return {
        "investor_profile": investor_thesis,
        "conversation": conversation,
        "discovered_companies": companies,
        "research": research,
        "final_analysis": final_analysis
    }


# =========================================================
# MANUAL TEST
# =========================================================
if __name__ == "__main__":
    result = investor_guided_discovery()
    print(json.dumps(result, indent=2))
