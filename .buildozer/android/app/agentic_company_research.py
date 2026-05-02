# agentic_company_research.py

import os
import requests
import json
import time

# =========================================================
# CONFIG
# =========================================================

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "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")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA5lN6PK-7I9DfKMgyvawKLIgOZAWZ-qjQ")

PERPLEXITY_ENDPOINT = "https://api.perplexity.ai/chat/completions"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

# Required data fields before stopping
REQUIRED_FIELDS = [
    "company_overview",
    "business_model",
    "products_services",
    "founding_year",
    "founders",
    "funding_history",
    "revenue_model",
    "market_tam",
    "competitors",
    "recent_news",
    "regulatory_risks",
    "sources"
]

# =========================================================
# LOW-LEVEL API CALLS
# =========================================================

def call_perplexity(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "You are a financial research assistant. Always cite sources."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    r = requests.post(PERPLEXITY_ENDPOINT, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_gemini(prompt: str) -> str:
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    r = requests.post(GEMINI_ENDPOINT, params=params, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

# =========================================================
# PARSING / STATE
# =========================================================

def empty_state():
    return {k: None for k in REQUIRED_FIELDS}


def missing_fields(state: dict):
    return [k for k, v in state.items() if not v]


# =========================================================
# AGENTIC LOOP (CORE LOGIC)
# =========================================================
def run_agentic_company_research(company_name: str) -> dict:
    """
    Agentic research that ALWAYS converges:
    - Ground what is available via Perplexity
    - Let Gemini infer the rest
    - Never leave empty fields
    """

    # -------------------------
    # INITIAL STATE
    # -------------------------
    state = empty_state()
    print(f"[Research] Starting research for {company_name}")

    # -------------------------
    # STEP 1: PERPLEXITY (GROUNDING)
    # -------------------------
    search_prompt = f"""
Research the company "{company_name}" using ONLY these sources:
- Yahoo Search
- Yahoo Finance
- Google News
- Wikipedia
- Google Search

Return factual information about:
{REQUIRED_FIELDS}

Include sources where possible.
"""

    research_text = call_perplexity(search_prompt)

    # -------------------------
    # STEP 2: GEMINI EXTRACTION (BEST EFFORT)
    # -------------------------
    extraction_prompt = f"""
You are a financial data extraction engine.

STRICT RULES:
- Output MUST be JSON
- No explanations
- No markdown
- Use null if unknown
- Keys MUST match exactly

ALLOWED KEYS:
{REQUIRED_FIELDS}

Research text:
{research_text}

Return JSON ONLY.
"""

    extracted = {}
    try:
        extracted = json.loads(call_gemini(extraction_prompt))
    except json.JSONDecodeError:
        extracted = {}

    # Normalize + merge (force-fill partial data)
    for k in REQUIRED_FIELDS:
        if extracted.get(k) not in [None, ""]:
            state[k] = extracted[k]

    # -------------------------
    # STEP 3: GEMINI INFERENCE (FILL GAPS)
    # -------------------------
    missing = [k for k, v in state.items() if not v]

    if missing:
        fill_prompt = f"""
You are an investment banking analyst.

Company: {company_name}

Known information:
{json.dumps(state, indent=2)}

TASK:
Fill ALL missing fields realistically.
Assumptions are allowed.
Be consistent with similar companies.

Return JSON ONLY.
Keys to fill:
{missing}
"""

        try:
            inferred = json.loads(call_gemini(fill_prompt))
        except json.JSONDecodeError:
            inferred = {}

        for k in missing:
            state[k] = inferred.get(
                k,
                "Estimated / inferred based on comparable companies"
            )

    # -------------------------
    # FINAL GUARANTEE
    # -------------------------
    for k in REQUIRED_FIELDS:
        if not state[k]:
            state[k] = "Estimated / inferred based on comparable companies"

    print("✅ Research completed (grounded + inferred).")
    return state
# =========================================================
# OPTIONAL TEST
# =========================================================

if __name__ == "__main__":
    result = run_agentic_company_research("Stripe")
    print(json.dumps(result, indent=2))
