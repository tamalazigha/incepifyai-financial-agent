"""
revenue_agent.py — IncepifyAI Relationship & Revenue Agent (Agent 4 of 8)
 
Design: Python computes all financial metrics first, then Claude
interprets, scores, and narrates. No external API calls required.
No new libraries needed — runs on the existing venv.
"""
 
import anthropic
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
_PROMPT_PATH = Path("system_prompt_revenue.txt")
if not _PROMPT_PATH.exists():
    raise FileNotFoundError(
        "system_prompt_revenue.txt not found. "
        "Make sure it is in the same folder as revenue_agent.py."
    )
 
SYSTEM_PROMPT = _PROMPT_PATH.read_text()
MODEL         = "claude-sonnet-4-6"
client        = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
 
 
# ─────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS
# ─────────────────────────────────────────────────────
 
def analyze_relationship(form_data: dict) -> dict:
    """
    Full live analysis: compute metrics in Python, then call Claude.
    form_data: structured dict from the Streamlit form (see app_revenue.py).
    """
    metrics = calculate_metrics(form_data)
    return _call_claude(form_data, metrics)
 
 
def get_mock_revenue_result() -> dict:
    """
    Full mock: static dict matching the Claude output structure exactly.
    Zero API calls. Use for UI testing.
    """
    return {
        "relationship_profile": {
            "company_name":               "Sunrise Manufacturing Ltd",
            "relationship_length_years":   8,
            "relationship_quality":        "STRONG",
            "number_of_products":          4,
            "payment_history_assessment":  "GOOD",
            "payment_history_commentary":  "No payment defaults recorded over the 8-year relationship. Two minor excesses in 2022 were regularised within 30 days.",
        },
        "revenue_analysis": {
            "ytd_gross_revenue_000":   7800,
            "prior_year_revenue_000":  6940,
            "planned_revenue_000":     8000,
            "yoy_growth_pct":          12.4,
            "plan_attainment_pct":     97.5,
            "net_revenue_000":         4200,
            "roa_pct":                 0.84,
            "revenue_trend":           "GROWING",
            "revenue_commentary":      "The relationship has delivered consistent revenue growth of 12.4% year-on-year, reflecting deepening product penetration and increased FX transaction volumes. YTD performance of 97.5% against plan is on track for full-year target achievement.",
        },
        "relationship_score": {
            "score":                9,
            "tier":                "SILVER",
            "strategic_importance": "HIGH",
            "cross_sell_potential": "MEDIUM",
            "cross_sell_opportunities": [
                "Cash management and payment processing platform",
                "Trade finance lines for import activities",
            ],
        },
        "risk_flags": [
            {
                "flag":            "Revenue Slightly Below Plan",
                "severity":        "LOW",
                "detail":          "YTD revenue is 97.5% of plan — a minor shortfall of NGN 200k.",
                "action_required": "Monitor Q4 performance; cross-sell action plan to close gap.",
            }
        ],
        "credit_memo_narrative": "Sunrise Manufacturing Ltd has maintained a strong 8-year banking relationship with consistent revenue growth of 12.4% year-on-year, generating a YTD gross revenue of NGN 7.8m against a plan of NGN 8.0m (97.5% attainment). The relationship ROA of 0.84% classifies this as a SILVER-tier relationship, approaching the GOLD threshold. Cross-sell opportunities in cash management and trade finance are identified to deepen the relationship and improve ROA in the medium term.",
        "_metadata": {
            "mode": "mock", "model": None,
            "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        },
    }
 
 
# ─────────────────────────────────────────────────────
# PYTHON FINANCIAL CALCULATIONS
# ─────────────────────────────────────────────────────
 
def calculate_metrics(data: dict) -> dict:
    """
    Compute all financial metrics in Python before sending to Claude.
    This keeps the Claude prompt focused on interpretation, not arithmetic.
    All monetary values are in NGN thousands (000).
    """
    items      = data.get("revenue_items", [])
    ytd_total  = sum(float(i.get("ytd",   0)) for i in items)
    py_total   = sum(float(i.get("prior_year", 0)) for i in items)
    plan_total = sum(float(i.get("plan",  0)) for i in items)
 
    # Year-on-year growth
    yoy_growth = ((ytd_total - py_total) / py_total * 100) if py_total else 0
 
    # Plan attainment
    plan_attainment = (ytd_total / plan_total * 100) if plan_total else 0
 
    # Net revenue after cost of funds and operating costs
    cof  = float(data.get("cost_of_funds_000",          0))
    opex = float(data.get("operating_costs_allocated_000", 0))
    net_revenue = ytd_total - cof - opex
 
    # ROA on relationship
    exposure = float(data.get("total_credit_exposure_000", 0))
    roa_pct  = (net_revenue / exposure * 100) if exposure else 0
 
    # Revenue per facility
    n_facilities = max(int(data.get("number_of_facilities", 1)), 1)
    rev_per_fac  = ytd_total / n_facilities
 
    # Breakdown by category
    breakdown = {}
    for item in items:
        cat = item.get("category", "Other")
        breakdown[cat] = {
            "ytd":        float(item.get("ytd",        0)),
            "prior_year": float(item.get("prior_year", 0)),
            "plan":       float(item.get("plan",       0)),
        }
 
    return {
        "ytd_gross_revenue_000":    round(ytd_total,     2),
        "prior_year_revenue_000":   round(py_total,      2),
        "planned_revenue_000":      round(plan_total,    2),
        "yoy_growth_pct":           round(yoy_growth,    2),
        "plan_attainment_pct":      round(plan_attainment, 2),
        "cost_of_funds_000":        round(cof,           2),
        "operating_costs_000":      round(opex,          2),
        "net_revenue_000":          round(net_revenue,   2),
        "roa_pct":                  round(roa_pct,       4),
        "revenue_per_facility_000": round(rev_per_fac,   2),
        "breakdown_by_category":    breakdown,
    }
 
 
# ─────────────────────────────────────────────────────
# CLAUDE API CALL
# ─────────────────────────────────────────────────────
 
def _call_claude(form_data: dict, metrics: dict) -> dict:
    """Call Claude with pre-computed metrics and return structured JSON."""
    user_message = (
        "Score and narrate the following relationship.\n\n"
        "FORM DATA (from relationship manager):\n"
        f"{json.dumps(form_data, indent=2)}\n\n"
        "PRE-COMPUTED FINANCIAL METRICS (Python-calculated, precise):\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        "Return ONLY the JSON object — no other text."
    )
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text   = next((b.text for b in response.content if b.type=="text"), "")
        result = _parse_json(text)
        result["_metadata"] = {
            "mode":              "claude",
            "model":             MODEL,
            "input_tokens":      response.usage.input_tokens,
            "output_tokens":     response.usage.output_tokens,
            "estimated_cost_usd": round(
                response.usage.input_tokens  * 0.000003 +
                response.usage.output_tokens * 0.000015, 4
            ),
        }
        return result
    except Exception as exc:
        fallback = _build_deterministic_result(form_data, metrics)
        fallback["_metadata"]["error"] = f"{type(exc).__name__}: {exc}"
        return fallback
 
 
def _parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON reliably."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip()).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        if start == -1:
            raise ValueError(f"No JSON found in: {text[:200]}")
        depth = 0
        for i, ch in enumerate(cleaned[start:], start=start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(cleaned[start:i+1])
        raise ValueError("Unbalanced JSON braces")
 
 
def _build_deterministic_result(form_data: dict, metrics: dict) -> dict:
    """Fallback when Claude is unavailable — deterministic from metrics."""
    roa = metrics.get("roa_pct", 0)
    plan = metrics.get("plan_attainment_pct", 0)
    yoy  = metrics.get("yoy_growth_pct", 0)
 
    tier = ("PLATINUM" if roa >= 3.0 else "GOLD" if roa >= 2.0
            else "SILVER" if roa >= 1.0 else "BRONZE" if roa >= 0.5
            else "BELOW_HURDLE")
    score = (10 if roa >= 3.0 else 8 if roa >= 2.0
             else 6 if roa >= 1.0 else 4 if roa >= 0.5 else 2)
    importance = "HIGH" if roa >= 2.0 else "MEDIUM" if roa >= 0.5 else "LOW"
 
    flags = []
    if roa < 0.5:
        flags.append({"flag":"Sub-Economic Relationship","severity":"HIGH",
            "detail":f"ROA of {roa:.2f}% is below the 0.5% minimum hurdle.",
            "action_required":"Exception approval from senior credit committee required."})
    if plan < 75:
        flags.append({"flag":"Revenue Significantly Below Plan","severity":"MEDIUM",
            "detail":f"Plan attainment of {plan:.1f}% is materially below target.",
            "action_required":"Cross-sell remediation plan required before credit approval."})
    if yoy < -10:
        flags.append({"flag":"Revenue Declining","severity":"MEDIUM",
            "detail":f"YoY revenue declined {abs(yoy):.1f}%.",
            "action_required":"Relationship management plan required."})
 
    company = form_data.get("company_name","Unknown")
    years   = form_data.get("relationship_length_years", 0)
    ytd     = metrics.get("ytd_gross_revenue_000", 0)
    py      = metrics.get("prior_year_revenue_000", 0)
 
    narrative = (
        f"{company} has a {years}-year banking relationship generating YTD gross "
        f"revenue of NGN {ytd:,.0f}k (prior year: NGN {py:,.0f}k, "
        f"YoY growth: {yoy:+.1f}%). "
        f"The relationship ROA of {roa:.2f}% classifies this as a {tier}-tier "
        f"relationship with {importance.lower()} strategic importance."
    )
 
    return {
        "relationship_profile": {
            "company_name":               company,
            "relationship_length_years":   years,
            "relationship_quality":        "SATISFACTORY",
            "number_of_products":          form_data.get("number_of_facilities",1),
            "payment_history_assessment":  "GOOD",
            "payment_history_commentary":  "Payment history assessed from form data.",
        },
        "revenue_analysis": {**metrics, "revenue_trend":"STABLE","revenue_commentary":"Computed deterministically."},
        "relationship_score": {
            "score": score, "tier": tier,
            "strategic_importance": importance,
            "cross_sell_potential": "MEDIUM",
            "cross_sell_opportunities": [],
        },
        "risk_flags":            flags,
        "credit_memo_narrative": narrative,
        "_metadata": {"mode":"deterministic","model":None,
                      "input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0},
    }
