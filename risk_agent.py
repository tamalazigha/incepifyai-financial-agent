"""
risk_agent.py — IncepifyAI Risk Assessment Agent (Agent 7 of 8)
FIXED VERSION — resolves silent fallback caused by max_tokens truncation.

Synthesises outputs of Agents 1-6 into a comprehensive risk matrix.
No web search. No external APIs. Single Claude API call.
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

# FIX #1: Increased from 8000 → 12000.
# The risk matrix JSON (6 dimensions x 8 fields + key risks + covenants +
# conditions + narrative) routinely needs 9,000-11,000 output tokens.
# At 8000 the response was being truncated mid-JSON, which threw a
# JSONDecodeError and silently degraded to the empty fallback object —
# this is what was causing risk_matrix / key_risks / covenants to be empty.
MAX_TOKENS = 12000


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
            "risk_flags": [{"flag": "Coverage Shortfall", "severity": "HIGH"}],
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
    """Full static mock of the Agent 7 output. Zero API calls."""
    return {
        "risk_summary": {
            "company_name":              "Sunrise Manufacturing Ltd",
            "assessment_date":            str(date.today()),
            "overall_credit_risk_rating": "WATCH",
            "credit_recommendation":      "APPROVE WITH CONDITIONS",
            "recommendation_rationale": (
                "Sunrise Manufacturing presents a WATCH risk profile with three "
                "resolvable conditions: collateral shortfall, PEP-connected director, "
                "and key man risk. Financial performance is satisfactory and the "
                "industry outlook is stable."
            ),
        },
        "risk_matrix": [
            {"risk_category":"Financial Risk","risk_description":"DSCR of 1.38x base case — adequate but stress case dips to 1.05x","likelihood":"LOW","impact":"MEDIUM","risk_rating":"LOW","key_driver":"Base DSCR 1.38x; stress DSCR 1.05x","mitigant":"Adequate base case coverage","residual_risk":"LOW","source_agent":"Agent 1"},
            {"risk_category":"Collateral Risk","risk_description":"Coverage at 109.1% against 150% minimum","likelihood":"HIGH","impact":"HIGH","risk_rating":"VERY_HIGH","key_driver":"Coverage ratio 109.1% vs 150%","mitigant":"Additional security as condition precedent","residual_risk":"MEDIUM","source_agent":"Agent 2"},
            {"risk_category":"Compliance Risk","risk_description":"PEP-connected director","likelihood":"MEDIUM","impact":"MEDIUM","risk_rating":"MEDIUM","key_driver":"ED Finance is PEP-connected","mitigant":"EDD completed; SM sign-off required","residual_risk":"LOW","source_agent":"Agent 3"},
            {"risk_category":"Revenue Risk","risk_description":"ROA below GOLD threshold","likelihood":"MEDIUM","impact":"LOW","risk_rating":"LOW","key_driver":"ROA 0.84%; growth 12.4%","mitigant":"Cross-sell plan","residual_risk":"LOW","source_agent":"Agent 4"},
            {"risk_category":"Industry Risk","risk_description":"FX input cost pressure","likelihood":"MEDIUM","impact":"MEDIUM","risk_rating":"MEDIUM","key_driver":"60% imported inputs","mitigant":"Domestic sourcing programme","residual_risk":"LOW","source_agent":"Agent 5"},
            {"risk_category":"Management Risk","risk_description":"Key man dependency","likelihood":"MEDIUM","impact":"HIGH","risk_rating":"HIGH","key_driver":"MD holds all relationships","mitigant":"Key man insurance required","residual_risk":"MEDIUM","source_agent":"Agent 6"},
        ],
        "key_risks": [
            {"rank":1,"risk_title":"Collateral Shortfall","risk_detail":"Security covers only 109.1% against 150% required.","mitigant":"Additional security as condition precedent.","residual_risk_after_mitigant":"LOW"},
            {"rank":2,"risk_title":"Key Man Concentration","risk_detail":"MD concentrates all operational decisions.","mitigant":"Key man insurance required.","residual_risk_after_mitigant":"MEDIUM"},
            {"rank":3,"risk_title":"PEP-Connected Director","risk_detail":"ED Finance is PEP-connected.","mitigant":"EDD completed; SM sign-off required.","residual_risk_after_mitigant":"LOW"},
        ],
        "cross_dimensional_risks": [
            {"risk":"FX pressure compounds key man risk","agents_involved":["Agent 5","Agent 6"],"detail":"Input cost management currently concentrated in the MD."},
        ],
        "conditions_precedent": [
            "Additional security of NGN 204.5m minimum pledged",
            "Governors Consent obtained on warehouse property",
            "Key man life and disability insurance required",
            "Senior management sign-off on EDD for PEP-connected director",
        ],
        "financial_covenants": [
            "DSCR >= 1.20x measured semi-annually",
            "Maximum leverage: Total Debt / EBITDA <= 3.5x",
            "Minimum cash balance: 3 months debt service",
            "Accounts domiciliation with the bank",
        ],
        "structural_covenants": [
            "Negative pledge on collateral assets",
            "Pari passu clause on additional borrowing",
            "Audit committee within 90 days",
            "Board succession plan within 90 days",
        ],
        "monitoring_requirements": [
            "Semi-annual financial statements within 60 days",
            "Annual collateral revaluation",
            "Director change notification within 5 business days",
            "Annual EDD review",
        ],
        "credit_memo_narrative": (
            "Sunrise Manufacturing Ltd presents a WATCH credit risk profile — "
            "APPROVE WITH CONDITIONS. The collateral shortfall is the primary risk, "
            "resolvable as a condition precedent. Secondary risks (key man dependency, "
            "PEP-connected director) are mitigated through insurance and EDD. "
            "Financial performance is satisfactory and the industry outlook is STABLE."
        ),
        "_metadata": {
            "mode": "mock", "model": None,
            "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
            "stop_reason": "end_turn",
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
        "Synthesise these into the risk matrix JSON. Return ONLY the JSON — no other text."
    )

    raw_text_for_debug = ""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        # FIX #2: Explicitly check stop_reason BEFORE attempting to parse.
        # If Claude was cut off mid-JSON, stop_reason will be "max_tokens"
        # and the JSON will be incomplete — fail fast with a clear error
        # instead of letting json.loads() throw a confusing exception.
        stop_reason = response.stop_reason

        text = "\n".join(
            b.text for b in response.content
            if getattr(b, "type", None) == "text"
        ).strip()
        raw_text_for_debug = text

        if stop_reason == "max_tokens":
            # The response was truncated. Don't even try to parse —
            # we know it will fail. Surface this clearly instead of
            # falling through to a generic JSON error.
            r = _build_fallback(all_outputs)
            r["_metadata"]["error"] = (
                f"Response truncated at {MAX_TOKENS} max_tokens "
                f"(stop_reason=max_tokens). The JSON was cut off mid-structure. "
                f"Increase MAX_TOKENS in risk_agent.py if this recurs."
            )
            r["_metadata"]["stop_reason"]       = stop_reason
            r["_metadata"]["raw_text_preview"]  = text[-500:]  # tail end shows the cutoff point
            r["_metadata"]["input_tokens"]      = response.usage.input_tokens
            r["_metadata"]["output_tokens"]     = response.usage.output_tokens
            return r

        result = _parse_json(text)
        result["_metadata"] = {
            "mode":               "claude",
            "model":              MODEL,
            "stop_reason":        stop_reason,
            "input_tokens":       response.usage.input_tokens,
            "output_tokens":      response.usage.output_tokens,
            "estimated_cost_usd": round(
                response.usage.input_tokens  * 0.000003 +
                response.usage.output_tokens * 0.000015, 4
            ),
        }
        return result

    except (ValueError, json.JSONDecodeError) as exc:
        # FIX #3: Surface the actual parse error AND a preview of what
        # Claude returned, so the credit officer / developer can see
        # exactly what went wrong instead of a silent empty fallback.
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = f"JSON parse error: {exc}"
        r["_metadata"]["raw_text_preview"] = raw_text_for_debug[-500:] if raw_text_for_debug else "(no text captured)"
        return r
    except anthropic.APIError as exc:
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = f"Anthropic API error: {exc}"
        return r
    except Exception as exc:
        r = _build_fallback(all_outputs)
        r["_metadata"]["error"] = f"{type(exc).__name__}: {exc}"
        r["_metadata"]["raw_text_preview"] = raw_text_for_debug[-500:] if raw_text_for_debug else "(no text captured)"
        return r


def _extract_company_name(all_outputs: dict) -> str:
    """Try to find the company name across any of the prior agent outputs."""
    for key in ["management_result", "financial_result", "collateral_result",
                "kyc_stored", "revenue_result", "industry_result"]:
        result = all_outputs.get(key, {})
        if not isinstance(result, dict):
            continue
        for sub in ["management_overview", "credit_recommendation",
                    "coverage_summary", "screening_metadata",
                    "relationship_profile", "industry_profile"]:
            sub_dict = result.get(sub, {})
            if isinstance(sub_dict, dict):
                name = sub_dict.get("company_name")
                if name and name != "Unknown":
                    return name
    return "The Applicant"


def _parse_json(text: str) -> dict:
    """
    Strip markdown fences and parse JSON reliably.
    FIX #4: Also attempts a light repair pass for common truncation-adjacent
    issues (trailing commas before closing brackets) before giving up.
    """
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip()).strip()

    # First attempt: parse as-is
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Second attempt: strip trailing commas before } or ] (common LLM artifact)
    repaired = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Third attempt: brace-counting extraction of the first complete object
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in response. First 200 chars: {text[:200]}")

    depth = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(cleaned[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[start:i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Found a complete-looking JSON object but it failed to parse: {exc}. "
                        f"This usually means the response was truncated mid-string. "
                        f"Last 200 chars before failure point: ...{candidate[-200:]}"
                    )

    # We reached the end without depth returning to 0 — definitely truncated
    raise ValueError(
        f"JSON object was never closed (brace depth never returned to 0) — "
        f"the response was truncated. Last 300 chars received: ...{cleaned[-300:]}"
    )


def _build_fallback(all_outputs: dict) -> dict:
    """Minimal fallback if Claude fails. Includes _metadata.error when set by caller."""
    company = _extract_company_name(all_outputs)
    return {
        "risk_summary": {
            "company_name":              company,
            "assessment_date":            str(date.today()),
            "overall_credit_risk_rating": "WATCH",
            "credit_recommendation":      "REFER TO CREDIT COMMITTEE",
            "recommendation_rationale":   "Automated risk synthesis could not be completed — see _metadata.error for details. Manual review required.",
        },
        "risk_matrix": [],
        "key_risks": [],
        "cross_dimensional_risks": [],
        "conditions_precedent": ["Full risk assessment must be re-run before approval — see _metadata.error."],
        "financial_covenants": [],
        "structural_covenants": [],
        "monitoring_requirements": [],
        "credit_memo_narrative": f"Risk assessment for {company} could not be completed automatically. Manual credit committee review is required.",
        "_metadata": {
            "mode": "fallback", "model": None,
            "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        },
    }

