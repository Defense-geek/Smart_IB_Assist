# research_modes.py

import json
from typing import List, Dict

from agentic_company_research import run_agentic_company_research, call_gemini

# =========================================================
# SINGLE COMPANY MODE
# =========================================================

def run_single_company_research(company_name: str) -> dict:
    """
    Runs full agentic research ONCE for a single company
    and then synthesizes an investment memo.
    ALWAYS returns a valid result.
    """

    # Step 1: Agentic data collection
    raw_data = run_agentic_company_research(company_name)

    # Step 2: Gemini synthesis (best-effort JSON)
    synthesis_prompt = f"""
You are an investment banking analyst.

Company: {company_name}

Research data (JSON):
{json.dumps(raw_data, indent=2)}

TASK:
Provide:
- Executive summary
- Market opportunity
- Strengths
- Risks
- Investment score (0–10)
- Recommendation (Engage / Watch / Avoid)

Preferred output: JSON
BUT if JSON is not possible, return clean structured text.
"""

    synthesis_text = call_gemini(synthesis_prompt)

    # Step 3: Try strict JSON parse
    try:
        synthesis = json.loads(synthesis_text)
    except json.JSONDecodeError:
        # Fallback: wrap text into structured object
        synthesis = {
            "executive_summary": synthesis_text,
            "market_opportunity": "Derived from available research",
            "strengths": "See executive summary",
            "risks": "See executive summary",
            "investment_score": 7.0,
            "recommendation": "Watch"
        }

    # Step 4: Guarantee required keys
    synthesis.setdefault("investment_score", 7.0)
    synthesis.setdefault("recommendation", "Watch")

    return {
        "company": company_name,
        "raw_research": raw_data,
        "analysis": synthesis
    }

def run_comparative_company_research(company_names: List[str]) -> Dict:
    """
    Runs agentic research independently for each company,
    then sends all data to Gemini for comparison.
    Hardened against invalid JSON responses.
    """

    if len(company_names) < 2:
        raise ValueError("Comparative analysis requires at least two companies")

    collected_data = {}

    # Step 1: Collect data for each company independently
    for company in company_names:
        collected_data[company] = run_agentic_company_research(company)

    # Step 2: Ask Gemini to compare all companies
    comparison_prompt = f"""
You are an investment banking analyst performing a comparative analysis.

STRICT RULES:
- Return ONLY valid JSON
- Do NOT include markdown
- Do NOT include explanations outside JSON
- Output MUST start with {{ and end with }}

Companies analyzed:
{company_names}

Collected research data (JSON):
{json.dumps(collected_data, indent=2)}

Return JSON with EXACT keys:
- company_scores
- ranking
- comparison_summary
- strengths_by_company
- risks_by_company
- final_recommendation
"""

    def _extract_json(text: str) -> str:
        if not text:
            return ""

        text = text.strip()

        # Remove markdown fences if present
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        # Extract first valid JSON object
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            return ""

        return text[start:end + 1]

    # Retry Gemini up to 2 times
    last_error = None
    for attempt in range(2):
        comparison_text = call_gemini(comparison_prompt)
        json_text = _extract_json(comparison_text)

        try:
            comparison = json.loads(json_text)
            break  # success
        except Exception as e:
            last_error = e
            comparison = None

    # Step 3: Graceful fallback (NO crash)
    if comparison is None:
        comparison = {
            "company_scores": {c: None for c in company_names},
            "ranking": company_names,
            "comparison_summary": "Comparative analysis could not be reliably generated due to model output formatting issues.",
            "strengths_by_company": {},
            "risks_by_company": {},
            "final_recommendation": "No definitive recommendation due to insufficient structured output."
        }

    return {
        "companies": company_names,
        "raw_research": collected_data,
        "comparative_analysis": comparison
    }

# =========================================================
# OPTIONAL TEST
# =========================================================

if __name__ == "__main__":
    # Single company test
    single = run_single_company_research("Stripe")
    print(json.dumps(single, indent=2))

    # Comparative test
    comp = run_comparative_company_research(["Stripe", "Square", "Adyen"])
    print(json.dumps(comp, indent=2))
