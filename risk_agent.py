"""
risk_agent.py — IncepifyAI Risk Assessment Agent (Agent 7 of 8)
 
Synthesises outputs of Agents 1-6 into a comprehensive risk matrix.
No web search. No external APIs. Single Claude API call.
Input: combined dict of all prior agent results.
Output: risk matrix, credit rating, covenants, Section 17 memo.
"""
 
import anthropic
import json
import os
import re
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
_PROMPT_PATH = Path("system_prompt_risk.txt")
if not _PROMPT_PATH.exists():
    raise FileNotFoundError(
        "system_prompt_risk.txt not found. "
        "Ensure it is in the same directory as risk_agent.py."
    )
 
SYSTEM_PROMPT = _PROMPT_PATH.read_text()
MODEL         = "claude-sonnet-4-6"
client        = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
 
 
# ─────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS
# ─────────────────────────────────────────────────────
 
def assess_risk(all_agent_outputs: dict) -> dict:
    """
    Synthesise all prior agent outputs into a risk assessment.
 
    Args:
        all_agent_outputs: dict with keys:
            financial_result, collateral_result, kyc_stored,
            revenue_result, industry_result, management_result
 
    Returns:
        dict: comprehensive risk matrix and credit recommendation
    """
    return _run_claude_analysis(all_agent_outputs)
 
 
def get_all_mock_inputs() -> dict:
    """
    Returns a combined mock input dict simulating all 6 prior agent outputs.
    Used in standalone app_risk.py when running without the suite.
    """
    return {
        "financial_result": {
            "credit_recommendation": {
                "overall_assessment": "SATISFACTORY",
                "primary_repayment_viability": "ADEQUATE",
                "narrative_summary": "DSCR of 1.38x in base case provides adequate coverage.",
            },
            "sensitivity_analysis": {
                "base_case": {"dscr_yr1": 1.38, "dscr_yr3": 1.21},
                "stress_case": {"dscr_yr1": 1.05, "dscr_yr3": 0.92},
            },
        },
        "collateral_result": {
            "coverage_summary": {
                "coverage_ratio_pct": 109.1,
                "coverage_status": "SHORTFALL",
                "minimum_required_pct": 150,
                "shortfall_or_surplus_000": -204500,
            },
            "pre_disbursement_conditions": [
                "Additional security of NGN 204.5m required to meet 150% coverage",
                "Governors Consent on real property must be obtained",
            ],
            "risk_flags": [{"flag":"Coverage Shortfall","severity":"HIGH"}],
        },
        "kyc_stored": {
            "aggregate_assessment": {
                "overall_kyc_risk_rating": "HIGH",
                "due_diligence_tier": "EDD",
                "senior_management_approval_required": True,
                "cbn_reporting_required": False,
            },
            "credit_memo_narrative": "HIGH KYC risk due to PEP-connected director.",
        },
        "revenue_result": {
            "revenue_analysis": {
                "ytd_gross_revenue_000": 7800,
                "yoy_growth_pct": 12.4,
                "plan_attainment_pct": 97.5,
                "roa_pct": 0.84,
                "revenue_trend": "GROWING",
            },
            "relationship_score": {"tier": "SILVER", "score": 7},
        },
        "industry_result": {
            "industry_assessment": {
                "outlook": "STABLE",
                "industry_risk_rating": "MEDIUM",
                "credit_risk_implication": "NEUTRAL",
                "cyclicality": "LOW",
            },
            "industry_profile": {"sector": "Manufacturing"},
        },
        "management_result": {
            "management_assessment": {
                "overall_management_score": 7,
                "management_quality": "SATISFACTORY",
                "key_man_risk_identified": True,
                "key_man_description": "MD is primary decision-maker with no succession plan.",
            },
            "management_overview": {"company_name": "Sunrise Manufacturing Ltd"},
        },
    }
 
 
def get_mock_risk_result() -> dict:
    """
    Full static mock of the Agent 7 output. Zero API calls.
    Use for UI testing.
    """
    return {
        "risk_summary": {
            "company_name":              "Sunrise Manufacturing Ltd",
            "assessment_date":            str(date.today()),
            "overall_credit_risk_rating": "WATCH",
            "credit_recommendation":      "APPROVE WITH CONDITIONS",
            "recommendation_rationale": (
                "Sunrise Manufacturing presents a WATCH risk profile with three resolvable conditions: "
                "collateral shortfall (requiring additional security), PEP-connected director "
                "(requiring EDD and SM sign-off), and key man risk (requiring insurance policy). "
                "Financial performance is satisfactory and the industry outlook is stable."
            ),
        },
        "risk_matrix": [
            {"risk_category":"Financial Risk","risk_description":"DSCR of 1.38x base case — adequate but stressed case dips to 1.05x in Year 1","likelihood":"LOW","impact":"MEDIUM","risk_rating":"LOW","key_driver":"Base DSCR 1.38x; stress DSCR 1.05x","mitigant":"Adequate base case coverage; stress testing within acceptable range","residual_risk":"LOW","source_agent":"Agent 1 — Financial Analysis"},
            {"risk_category":"Collateral Risk","risk_description":"Coverage at 109.1% against 150% minimum — shortfall of NGN 204.5m","likelihood":"HIGH","impact":"HIGH","risk_rating":"VERY_HIGH","key_driver":"Coverage ratio 109.1% vs 150% minimum required","mitigant":"Additional security to be provided as condition precedent before disbursement","residual_risk":"MEDIUM","source_agent":"Agent 2 — Collateral & Security"},
            {"risk_category":"Compliance / KYC Risk","risk_description":"PEP-connected director (ED Finance) — CBN EDD mandatory","likelihood":"MEDIUM","impact":"MEDIUM","risk_rating":"MEDIUM","key_driver":"ED Finance is sibling of State Commissioner — PEP under CBN KYC Manual","mitigant":"Enhanced Due Diligence completed; SM sign-off required and will be obtained","residual_risk":"LOW","source_agent":"Agent 3 — Reputation & KYC"},
            {"risk_category":"Revenue / Relationship Risk","risk_description":"ROA of 0.84% below 1.0% GOLD threshold — SILVER tier relationship","likelihood":"MEDIUM","impact":"LOW","risk_rating":"LOW","key_driver":"ROA 0.84%; YTD revenue NGN 7.8m; YoY growth 12.4%","mitigant":"Revenue growing 12.4% YoY; cross-sell plan to improve ROA above 1.0%","residual_risk":"LOW","source_agent":"Agent 4 — Relationship & Revenue"},
            {"risk_category":"Industry / Market Risk","risk_description":"FX input cost pressure in food manufacturing — moderate headwind","likelihood":"MEDIUM","impact":"MEDIUM","risk_rating":"MEDIUM","key_driver":"60% of raw materials imported; Naira devaluation increased input costs 30-40%","mitigant":"Industry outlook STABLE; domestic sourcing programme in place","residual_risk":"LOW","source_agent":"Agent 5 — Industry Intelligence"},
            {"risk_category":"Management Risk","risk_description":"Key man dependency on MD; board lacks audit committee","likelihood":"MEDIUM","impact":"HIGH","risk_rating":"HIGH","key_driver":"Management score 7/10; MD holds all operational relationships; no succession plan","mitigant":"Key man insurance required as condition; audit committee to be established","residual_risk":"MEDIUM","source_agent":"Agent 6 — Management Assessment"},
        ],
        "key_risks": [
            {"rank":1,"risk_title":"Collateral Shortfall","risk_detail":"Security package covers only 109.1% of the facility against a 150% policy minimum — a shortfall of NGN 204.5m.","mitigant":"Additional security to be pledged as a condition precedent to first drawdown. No disbursement permitted until coverage reaches 150%.","residual_risk_after_mitigant":"LOW"},
            {"rank":2,"risk_title":"Key Man Concentration — MD","risk_detail":"The Managing Director concentrates all operational decisions and key client/supplier relationships. No documented succession plan exists.","mitigant":"Key man life and disability insurance policy (bank as beneficiary, sum insured = facility amount) required as condition precedent. Board to formalise succession plan within 90 days of drawdown.","residual_risk_after_mitigant":"MEDIUM"},
            {"rank":3,"risk_title":"PEP-Connected Director","risk_detail":"Executive Director (Finance) is an immediate family member of a serving State Commissioner under the CBN KYC/AML Manual PEP definition.","mitigant":"Enhanced Due Diligence completed. Senior management sign-off required before approval. Quarterly monitoring of director changes for the credit tenor.","residual_risk_after_mitigant":"LOW"},
        ],
        "cross_dimensional_risks": [
            {"risk":"FX cost pressure compounds key man risk","agents_involved":["Agent 5","Agent 6"],"detail":"Naira-driven input cost inflation requires active hedging and supplier negotiation — skills currently concentrated in the MD. Incapacity of the MD during a FX stress period would be doubly damaging."},
        ],
        "conditions_precedent": [
            "Additional security of NGN 204.5m minimum pledged to bring coverage to 150%",
            "Governors Consent obtained and legal mortgage registered on warehouse property",
            "Key man life and disability insurance — bank as beneficiary for full facility amount",
            "Senior management sign-off on EDD for PEP-connected director",
        ],
        "financial_covenants": [
            "DSCR >= 1.20x measured semi-annually throughout the facility tenor",
            "Maximum leverage ratio: Total Debt / EBITDA <= 3.5x",
            "Minimum cash balance: 3 months of debt service to be maintained at all times",
            "Accounts domiciliation: primary operating accounts to be maintained with the bank",
        ],
        "structural_covenants": [
            "Negative pledge: no additional charge over collateral assets without bank consent",
            "Pari passu clause: no new senior unsecured borrowing without bank consent",
            "Audit committee to be established within 90 days of first drawdown",
            "Board succession plan for the MD to be submitted within 90 days",
        ],
        "monitoring_requirements": [
            "Semi-annual financial statements within 60 days of period end",
            "Collateral revaluation annually (CBN-approved valuer)",
            "Director change notification within 5 business days",
            "KYC refresh: full EDD review annually given PEP-connected director",
        ],
        "credit_memo_narrative": "Sunrise Manufacturing Ltd presents a WATCH credit risk profile — APPROVE WITH CONDITIONS. The collateral shortfall (109.1% vs 150%) is the primary risk, resolvable as a condition precedent. Secondary risks (key man dependency, PEP-connected director) are mitigated through insurance requirements and EDD. Financial performance is satisfactory (DSCR 1.38x, revenue +12.4% YoY) and the industry outlook is STABLE.",
        "_metadata": {
            "mode": "mock","model": None,
            "input_tokens": 0,"output_tokens": 0,"estimated_cost_usd": 0.0
        },
    }
 
 
# ─────────────────────────────────────────────────────
# CLAUDE API CALL — SINGLE CALL, NO AGENTIC LOOP
# ─────────────────────────────────────────────────────
 
def _run_claude_analysis(all_outputs: dict) -> dict:
    """Single Claude call — no web search, no agentic loop."""
    if client is None:
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = "ANTHROPIC_API_KEY not set."
        return r
 
    company = _extract_company_name(all_outputs)
 
    user_message = (
        f"Perform a comprehensive risk assessment for {company}.\n\n"
        "PRIOR AGENT OUTPUTS (all 6 agents):\n"
        f"{json.dumps(all_outputs, indent=2, default=str)}\n\n"
        "Synthesise these into the risk matrix JSON. Return ONLY the JSON — no other text.",
    )
 
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = next(
            (b.text for b in response.content if getattr(b,"type",None)=="text"),
            ""
        )
        result = _parse_json(text)
        result["_metadata"] = {
            "mode":               "claude",
            "model":              MODEL,
            "input_tokens":       response.usage.input_tokens,
            "output_tokens":      response.usage.output_tokens,
            "estimated_cost_usd": round(
                response.usage.input_tokens  * 0.000003 +
                response.usage.output_tokens * 0.000015, 4
            ),
        }
        return result
 
    except (ValueError, json.JSONDecodeError) as exc:
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = f"JSON parse error: {exc}"
        return r
    except anthropic.APIError as exc:
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = f"API error: {exc}"
        return r
    except Exception as exc:
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = f"{type(exc).__name__}: {exc}"
        return r
 
 
def _extract_company_name(all_outputs: dict) -> str:
    """Try to find the company name across any of the prior agent outputs."""
    for key in ["management_result","financial_result","collateral_result",
                "kyc_stored","revenue_result","industry_result"]:
        result = all_outputs.get(key, {})
        for sub in ["management_overview","credit_recommendation",
                    "coverage_summary","screening_metadata",
                    "relationship_profile","industry_profile"]:
            name = result.get(sub, {}).get("company_name")
            if name and name != "Unknown":
                return name
    return "The Applicant"
 
 
def _parse_json(text: str) -> dict:
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
        raise ValueError("Unbalanced JSON.")
 
 
def _build_fallback(all_outputs: dict) -> dict:
    """Minimal fallback if Claude fails."""
    company = _extract_company_name(all_outputs)
    return {
        "risk_summary": {
            "company_name":              company,
            "assessment_date":            str(date.today()),
            "overall_credit_risk_rating": "WATCH",
            "credit_recommendation":      "REFER TO CREDIT COMMITTEE",
            "recommendation_rationale":   "Fallback: full AI synthesis not completed. Manual review required.",
        },
        "risk_matrix": [],
        "key_risks": [],
        "cross_dimensional_risks": [],
        "conditions_precedent": ["Full risk assessment must be re-run before approval."],
        "financial_covenants": [],
        "structural_covenants": [],
        "monitoring_requirements": [],
        "credit_memo_narrative": f"Risk assessment for {company} could not be completed automatically. Manual credit committee review is required.",
        "_metadata": {"mode":"fallback","model":None,"input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0},
    }
