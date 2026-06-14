"""
industry_agent.py — IncepifyAI Industry Intelligence Agent (Agent 5 of 8)
 
Uses Claude web search to research the applicant's industry sector.
No external APIs required — web search is built into the Claude API.
Pattern mirrors Agent 3 (kyc_agent.py): agentic loop until end_turn.
"""
 
import anthropic
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
_PROMPT_PATH = Path("system_prompt_industry.txt")
if not _PROMPT_PATH.exists():
    raise FileNotFoundError(
        "system_prompt_industry.txt not found. "
        "Ensure it is in the same directory as industry_agent.py."
    )
 
SYSTEM_PROMPT = _PROMPT_PATH.read_text()
MODEL         = "claude-sonnet-4-6"
client        = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
WEB_SEARCH    = {"type": "web_search_20250305", "name": "web_search"}
 
 
# ─────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS
# ─────────────────────────────────────────────────────
 
def analyze_industry(form_data: dict) -> dict:
    """
    Full live analysis: Claude runs web searches and returns structured JSON.
    form_data: dict from Streamlit form (see app_industry.py).
    """
    return _run_claude_analysis(form_data)
 
 
def get_mock_industry_result() -> dict:
    """
    Full mock: static dict matching exact Claude output structure.
    Zero API calls. Use for UI testing and suite integration testing.
    """
    return {
        "industry_profile": {
            "sector":                   "Manufacturing",
            "sub_sector":               "Food & Beverages",
            "cbn_sector_classification": "Manufacturing (MFG)",
            "geographic_scope":          "Nigeria",
        },
        "market_data": {
            "market_size_usd_bn":       24.5,
            "market_size_ngn_bn":       39200,
            "cagr_historical_5yr_pct":   8.2,
            "cagr_projected_5yr_pct":    9.5,
            "data_year":                "2024",
            "data_source_notes": (
                "Euromonitor Nigeria F&B report 2024; CBN Statistical Bulletin; "
                "NBS Annual Abstract of Statistics 2023"
            ),
        },
        "competitive_landscape": {
            "market_structure":            "OLIGOPOLISTIC",
            "number_of_significant_players": 12,
            "top_competitors": [
                "Dangote Foods", "Nestlé Nigeria", "Unilever Nigeria",
                "Flour Mills Nigeria", "Cadbury Nigeria"
            ],
            "barriers_to_entry":   "MEDIUM",
            "pricing_power":       "MEDIUM",
            "competitive_intensity": "HIGH",
        },
        "industry_trends": [
            {"trend": "Naira devaluation import cost pressure",
             "impact": "NEGATIVE",
             "detail": "FX-denominated raw material imports (wheat, sugar) have increased production costs by 30–40% since 2023 devaluation."},
            {"trend": "Rising domestic demand driven by population growth",
             "impact": "POSITIVE",
             "detail": "Nigeria's 220m+ population and urbanisation rate support consistent demand growth for packaged food products."},
            {"trend": "Government backward integration incentives",
             "impact": "POSITIVE",
             "detail": "CBN Anchor Borrowers Programme and NIRSAL support domestic sourcing, reducing FX dependency for qualifying companies."},
        ],
        "risk_factors": [
            {"risk": "FX volatility on imported inputs",
             "severity": "HIGH",
             "detail": "Heavy dependence on imported raw materials creates significant margin risk from Naira weakness."},
            {"risk": "Energy cost inflation",
             "severity": "MEDIUM",
             "detail": "Diesel and electricity costs represent 15–20% of production costs and remain volatile post fuel subsidy removal."},
        ],
        "obligor_position": {
            "company_name":               "Sunrise Manufacturing Ltd",
            "estimated_market_share_pct":  2.1,
            "competitive_position":        "CHALLENGER",
            "key_differentiators": [
                "Regional distribution network covering South-West Nigeria",
                "ISO 22000 food safety certification",
            ],
            "key_vulnerabilities": [
                "Heavy reliance on imported wheat flour",
                "Single production facility concentration risk",
            ],
        },
        "industry_assessment": {
            "outlook":                "STABLE",
            "cyclicality":            "LOW",
            "regulatory_risk":        "LOW",
            "industry_risk_rating":   "MEDIUM",
            "credit_risk_implication": "NEUTRAL",
            "outlook_commentary": "The Nigerian food and beverage manufacturing sector presents a stable credit environment supported by defensive demand characteristics and a large addressable domestic market. Near-term headwinds from FX-driven input cost inflation are partially offset by improving domestic sourcing options.",
        },
        "credit_memo_narrative": "Sunrise Manufacturing Ltd operates in the Nigerian food and beverage manufacturing sector, a MEDIUM industry risk environment with stable demand characteristics. The sector faces near-term headwinds from FX volatility on imported inputs, though the company challenger market position provides competitive insulation. The industry outlook is STABLE with a NEUTRAL credit risk implication.",
        "_metadata": {
            "mode":              "mock",
            "model":             None,
            "searches_conducted": [],
            "input_tokens":       0,
            "output_tokens":      0,
            "estimated_cost_usd": 0.0,
        },
    }
 
 
# ─────────────────────────────────────────────────────
# AGENTIC LOOP — mirrors kyc_agent.py pattern exactly
# ─────────────────────────────────────────────────────
 
def _run_claude_analysis(form_data: dict, max_rounds: int = 8) -> dict:
    """
    Call Claude with web search enabled and loop until end_turn.
    Claude decides its own search queries based on the sector and company.
    """
    if client is None:
        result = _build_fallback(form_data)
        result["_metadata"]["error"] = "ANTHROPIC_API_KEY not set."
        return result
 
    sector  = form_data.get("sector", "Unknown")
    company = form_data.get("company_name", "the applicant")
    country = form_data.get("country", "Nigeria")
 
    user_message = (
        f"Research the {sector} industry in {country} for a credit application "
        f"from {company}.\n\n"
        "APPLICANT CONTEXT:\n"
        f"{json.dumps(form_data, indent=2)}\n\n"
        "INSTRUCTIONS:\n"
        "1. Use web_search to find current market data, competitors, and trends.\n"
        "2. Run at least 3 searches — more if needed for completeness.\n"
        "3. After all searches, return ONLY the JSON object."
    )
 
    messages = [{"role": "user", "content": user_message}]
    searches = []
 
    try:
        for round_num in range(max_rounds):
            response = client.messages.create(
                model=MODEL,
                max_tokens=5000,
                system=SYSTEM_PROMPT,
                tools=[WEB_SEARCH],
                messages=messages,
            )
 
            if response.stop_reason == "end_turn":
                text   = "\n".join(
                    b.text for b in response.content
                    if getattr(b, "type", None) == "text"
                ).strip()
                result = _parse_json(text)
                result["_metadata"] = {
                    "mode":              "claude",
                    "model":             MODEL,
                    "searches_conducted": searches,
                    "input_tokens":      response.usage.input_tokens,
                    "output_tokens":     response.usage.output_tokens,
                    "estimated_cost_usd": round(
                        response.usage.input_tokens  * 0.000003 +
                        response.usage.output_tokens * 0.000015, 4
                    ),
                }
                return result
 
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if getattr(block, "type", None) == "tool_use":
                        if block.name == "web_search":
                            searches.append(block.input.get("query", ""))
                        tool_results.append({
                            "type":        "tool_result",
                            "tool_use_id": block.id,
                            "content":     "Search executed.",
                        })
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue
            break
 
        result = _build_fallback(form_data)
        result["_metadata"]["mode"]    = "fallback_max_rounds"
        result["_metadata"]["searches_conducted"] = searches
        return result
 
    except (ValueError, json.JSONDecodeError) as exc:
        result = _build_fallback(form_data)
        result["_metadata"]["error"] = f"JSON parse error: {exc}"
        return result
    except anthropic.APIError as exc:
        result = _build_fallback(form_data)
        result["_metadata"]["error"] = f"API error: {exc}"
        return result
    except Exception as exc:
        result = _build_fallback(form_data)
        result["_metadata"]["error"] = f"{type(exc).__name__}: {exc}"
        return result
 
 
def _parse_json(text: str) -> dict:
    """Strip markdown fences and parse JSON reliably."""
    cleaned = re.sub(r"^```(?:json)?\s*","",text.strip(),flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$","",cleaned.strip()).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        if start == -1:
            raise ValueError(f"No JSON in response: {text[:200]}")
        depth = 0
        for i, ch in enumerate(cleaned[start:], start=start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(cleaned[start:i+1])
        raise ValueError("Unbalanced JSON braces")
 
 
def _build_fallback(form_data: dict) -> dict:
    """Minimal deterministic fallback when Claude cannot complete."""
    sector  = form_data.get("sector", "Unknown")
    company = form_data.get("company_name", "Unknown")
    high_risk = ["Oil & Gas","Mining","Real Estate","Construction"]
    low_risk  = ["Healthcare","Education","ICT","Financial Services","FMCG","Retail"]
    if sector in high_risk:
        rating,outlook,implication = "HIGH","CAUTIOUS","CONSTRAINS"
    elif sector in low_risk:
        rating,outlook,implication = "LOW","POSITIVE","SUPPORTS"
    else:
        rating,outlook,implication = "MEDIUM","STABLE","NEUTRAL"
    return {
        "industry_profile": {
            "sector": sector, "sub_sector": None,
            "cbn_sector_classification": sector,
            "geographic_scope": form_data.get("country","Nigeria"),
        },
        "market_data": {
            "market_size_usd_bn": None,"market_size_ngn_bn": None,
            "cagr_historical_5yr_pct": None,"cagr_projected_5yr_pct": None,
            "data_year": "N/A",
            "data_source_notes": "Web search not completed — using fallback.",
        },
        "competitive_landscape": {
            "market_structure": "FRAGMENTED","number_of_significant_players": None,
            "top_competitors": [],"barriers_to_entry": "MEDIUM",
            "pricing_power": "MEDIUM","competitive_intensity": "MEDIUM",
        },
        "industry_trends": [],
        "risk_factors": [],
        "obligor_position": {
            "company_name": company,"estimated_market_share_pct": None,
            "competitive_position": "FOLLOWER",
            "key_differentiators": [],"key_vulnerabilities": [],
        },
        "industry_assessment": {
            "outlook": outlook,"cyclicality": "MEDIUM",
            "regulatory_risk": "MEDIUM","industry_risk_rating": rating,
            "credit_risk_implication": implication,
            "outlook_commentary": f"Fallback assessment for {sector} sector.",
        },
        "credit_memo_narrative": (
            f"{company} operates in the {sector} sector. "
            f"A {rating} industry risk rating is applied based on sector classification. "
            "Full industry intelligence web search was not completed — "
            "manual review of industry conditions is recommended."
        ),
        "_metadata": {
            "mode": "fallback","model": None,
            "searches_conducted": [],"input_tokens": 0,
            "output_tokens": 0,"estimated_cost_usd": 0.0,
        },
    }
