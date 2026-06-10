import anthropic
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
# Load the COLLATERAL system prompt (separate from financial agent)
SYSTEM_PROMPT = Path("system_prompt_collateral.txt").read_text()
 
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
 
 
def analyze_collateral(collateral_data: dict) -> dict:
    """
    Send structured collateral data to Claude and return security analysis.
 
    Args:
        collateral_data: dict matching the input format in system_prompt_collateral.txt
 
    Returns:
        dict: Full security adequacy report with coverage ratios and risk flags
    """
    user_message = f"""Assess the following collateral package and return the JSON analysis.
 
Return ONLY the JSON object — no other text.
 
--- COLLATERAL DATA ---
{json.dumps(collateral_data, indent=2)}
--- END DATA ---"""
 
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
 
    raw_text = response.content[0].text.strip()
 
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"Cannot parse JSON.\nRaw: {raw_text[:500]}")
 
    result["_metadata"] = {
        "model_used":         response.model,
        "input_tokens":       response.usage.input_tokens,
        "output_tokens":      response.usage.output_tokens,
        "estimated_cost_usd": round(
            (response.usage.input_tokens  * 0.000003) +
            (response.usage.output_tokens * 0.000015), 4
        )
    }
    return result
 
 
def get_mock_collateral_result() -> dict:
    """
    Hardcoded mock — use for UI development and demo testing.
    No API cost. Switch to analyze_collateral() for live use.
    """
    return {
        "company_name": "Sunrise Manufacturing Ltd",
        "facility_summary": {
            "facility_amount_000": 500000,
            "facility_type": "TERM_LOAN_3YR_PLUS",
            "facility_tenor_months": 60,
            "minimum_coverage_required_pct": 150
        },
        "collateral_analysis": [
            {
                "item_number": 1,
                "type": "REAL_PROPERTY_COFO",
                "description": "Industrial warehouse, Apapa, Lagos",
                "open_market_value_000": 620000,
                "advance_rate_pct": 65,
                "adjusted_value_000": 403000,
                "quality_tier": "TIER_2",
                "documentation_gaps": ["Governor's Consent not yet obtained"],
                "perfection_checklist": {
                    "title_document": "PRESENT",
                    "valuation_report": "PRESENT",
                    "insurance": "PRESENT",
                    "cac_registration": "PENDING",
                    "governors_consent": "REQUIRED_PENDING",
                    "encumbrance_status": "CLEAR"
                },
                "enforcement_risk": "MEDIUM",
                "enforcement_risk_narrative": "Real property enforcement requires court order; Governor's Consent must be obtained before legal mortgage can be registered."
            },
            {
                "item_number": 2,
                "type": "CASH_NGN",
                "description": "Fixed deposit — First Bank account",
                "open_market_value_000": 150000,
                "advance_rate_pct": 95,
                "adjusted_value_000": 142500,
                "quality_tier": "TIER_1",
                "documentation_gaps": [],
                "perfection_checklist": {
                    "title_document": "PRESENT",
                    "valuation_report": "NOT_APPLICABLE",
                    "insurance": "NOT_APPLICABLE",
                    "cac_registration": "NOT_APPLICABLE",
                    "governors_consent": "NOT_APPLICABLE",
                    "encumbrance_status": "CLEAR"
                },
                "enforcement_risk": "LOW",
                "enforcement_risk_narrative": "Cash collateral is immediately realisable; lowest enforcement risk."
            }
        ],
        "coverage_summary": {
            "total_open_market_value_000": 770000,
            "total_adjusted_value_000": 545500,
            "coverage_ratio_pct": 109.1,
            "minimum_required_pct": 150,
            "coverage_status": "SHORTFALL",
            "shortfall_or_surplus_000": -204500,
            "tier_1_pct_of_total": 26.1,
            "tier_2_pct_of_total": 73.9,
            "tier_3_pct_of_total": 0,
            "tier_4_pct_of_total": 0
        },
        "risk_flags": [
            {
                "flag": "Coverage Shortfall",
                "severity": "HIGH",
                "detail": "Adjusted security value of NGN 545.5m (109.1%) falls short of the 150% minimum required for a 5-year term loan. Additional security of NGN 204.5m required.",
                "legal_reference": "CBN Prudential Guidelines — minimum collateral coverage",
                "pre_disbursement_condition": True
            },
            {
                "flag": "Governor's Consent Pending",
                "severity": "HIGH",
                "detail": "Legal mortgage over warehouse cannot be registered without Governor's Consent under Land Use Act 1978 s.22. Security is unperfected.",
                "legal_reference": "Land Use Act 1978 s.22",
                "pre_disbursement_condition": True
            }
        ],
        "pre_disbursement_conditions": [
            "Additional security of NGN 204.5m minimum must be provided to bring coverage to 150%",
            "Governor's Consent obtained and legal mortgage registered over industrial warehouse"
        ],
        "credit_memo_narrative": "Sunrise Manufacturing Ltd has offered a collateral package with a total open market value of NGN 770m, comprising an industrial warehouse (CofO title, Lagos) and a cash fixed deposit. Applying standard advance rates, the adjusted security value of NGN 545.5m represents coverage of 109.1% against the 150% minimum required for the 5-year tenor, resulting in a shortfall of NGN 204.5m. Two pre-disbursement conditions are outstanding: provision of additional security to meet the 150% threshold and registration of a legal mortgage following receipt of Governor's Consent. The Tier 1 collateral component (26.1%) provides a solid liquid base.",
        "_metadata": {"model_used":"mock","input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0}
    }

