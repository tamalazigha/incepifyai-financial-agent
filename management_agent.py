"""
management_agent.py — IncepifyAI Management Assessment Agent (Agent 6 of 8)
 
Assesses management quality, board governance, and key man risk.
Uses Claude web search to research director backgrounds and verify
CAC registration. No external APIs beyond Claude.
Pattern mirrors Agents 3 and 5: agentic loop until end_turn.
"""
 
import anthropic
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
 
load_dotenv()
 
_PROMPT_PATH = Path("system_prompt_management.txt")
if not _PROMPT_PATH.exists():
    raise FileNotFoundError(
        "system_prompt_management.txt not found. "
        "Ensure it is in the same directory as management_agent.py."
    )
 
SYSTEM_PROMPT = _PROMPT_PATH.read_text()
MODEL         = "claude-sonnet-4-6"
client        = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
WEB_SEARCH    = {"type": "web_search_20250305", "name": "web_search"}
 
 
# ─────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS
# ─────────────────────────────────────────────────────
 
def assess_management(form_data: dict) -> dict:
    """
    Full live analysis: Claude researches each director and returns JSON.
    form_data: structured dict from Streamlit form (see app_management.py).
    """
    return _run_claude_analysis(form_data)
 
 
def get_mock_management_result() -> dict:
    """
    Full mock: static dict matching exact Claude output structure.
    Zero API calls. Use for UI testing and suite integration testing.
    """
    return {
        "management_overview": {
            "company_name":           "Sunrise Manufacturing Ltd",
            "total_directors":         3,
            "executive_directors":     2,
            "non_executive_directors": 1,
            "board_independence_pct":  33.3,
            "cac_rc_number":           "RC-482931",
            "cac_verification_status": "VERIFIED",
        },
        "director_profiles": [
            {
                "name":                     "Chidi Okonkwo",
                "role":                     "Managing Director / CEO",
                "years_of_experience":       18,
                "industry_experience_years": 15,
                "qualifications":            ["BSc Chemical Engineering (UNILAG)", "MBA (Lagos Business School)"],
                "professional_memberships":  ["COREN", "NIM"],
                "previous_companies":        ["Nestlé Nigeria (Production Manager)", "Dangote Industries (Operations Director)"],
                "track_record":              "EXCELLENT",
                "track_record_detail":       "Spent 12 years in senior roles at Tier 1 Nigerian manufacturers before founding Sunrise. Company has grown revenue 3x in 8 years under his leadership.",
                "key_man_risk":               True,
                "cac_registered":            "CONFIRMED",
                "web_search_findings":       "LinkedIn profile confirms prior Nestlé and Dangote roles. Featured in BusinessDay 2022 as one of emerging food manufacturing leaders. No adverse findings.",
                "individual_score":           8,
                "individual_score_narrative": "Strong track record in Tier 1 manufacturing environments with clear strategic leadership at Sunrise. Key man risk noted as operational decisions are heavily centralised.",
            },
            {
                "name":                     "Adaeze Nwosu",
                "role":                     "Executive Director, Finance",
                "years_of_experience":       14,
                "industry_experience_years": 10,
                "qualifications":            ["BSc Accounting (UNIBEN)", "ACA (ICAN Fellow)"],
                "professional_memberships":  ["ICAN"],
                "previous_companies":        ["PricewaterhouseCoopers Nigeria (Senior Manager)", "Access Bank (CFO, SME Division)"],
                "track_record":              "GOOD",
                "track_record_detail":       "Strong financial management background from Big 4 and commercial banking. Joined Sunrise 4 years ago and implemented financial controls that improved EBITDA margin by 4 percentage points.",
                "key_man_risk":               False,
                "cac_registered":            "CONFIRMED",
                "web_search_findings":       "ICAN membership confirmed via ICAN website. PwC Nigeria alumni records corroborate prior employment. No adverse findings.",
                "individual_score":           7,
                "individual_score_narrative": "Solid financial management credentials with Big 4 and banking background. ICAN fellowship provides technical credibility. Performance at Sunrise has been measurably positive.",
            },
            {
                "name":                     "Dr Emmanuel Adeyemi",
                "role":                     "Non-Executive Director",
                "years_of_experience":       25,
                "industry_experience_years": 20,
                "qualifications":            ["PhD Economics (University of Ibadan)", "MSc Finance (London Business School)"],
                "professional_memberships":  ["CIBN", "NIM"],
                "previous_companies":        ["First Bank Nigeria (Deputy MD)", "CBN (Deputy Director, Banking Supervision)"],
                "track_record":              "EXCELLENT",
                "track_record_detail":       "Distinguished career spanning CBN and First Bank. Brings regulatory and banking sector expertise as independent oversight to the board.",
                "key_man_risk":               False,
                "cac_registered":            "CONFIRMED",
                "web_search_findings":       "CBN records confirm prior employment as Deputy Director. First Bank annual reports list him as Deputy MD 2010-2017. Well-regarded in Nigerian banking circles.",
                "individual_score":           9,
                "individual_score_narrative": "Exceptional credentials combining CBN regulatory background with senior commercial banking leadership. Provides strong independent oversight to the Sunrise board.",
            },
        ],
        "board_assessment": {
            "governance_structure":   "ADEQUATE",
            "governance_commentary":  "The board has a 2:1 executive to non-executive ratio, meeting the minimum independence threshold. The presence of a former CBN Deputy Director as NED provides meaningful oversight. However, the board lacks a formal audit committee, which is a governance gap for a company of this credit size.",
            "audit_committee_present":  False,
            "ceo_chairman_separation":  True,
            "board_skills_diversity":   "MEDIUM",
        },
        "management_assessment": {
            "overall_management_score":  7,
            "management_quality":        "SATISFACTORY",
            "key_man_risk_identified":    True,
            "key_man_description":       "Mr Okonkwo (MD) is the primary operational decision-maker and holds the key client and supplier relationships. An incapacity event would create significant business disruption.",
            "succession_planning":       "INADEQUATE",
            "management_stability":      "STABLE",
            "team_depth":                "ADEQUATE",
        },
        "risk_flags": [
            {
                "flag":            "Key Person Dependency — MD",
                "severity":        "HIGH",
                "detail":          "Chidi Okonkwo (MD) is the primary operational decision-maker. No formal succession plan is documented.",
                "action_required": "Obtain key man life insurance policy with bank as beneficiary. Document succession plan as credit condition.",
            },
            {
                "flag":            "Audit Committee Absent",
                "severity":        "MEDIUM",
                "detail":          "The board has no formal audit committee. SEC governance code recommends audit committees for companies above a revenue threshold.",
                "action_required": "Recommend establishment of audit committee as a condition of the credit.",
            },
        ],
        "credit_memo_narrative": "Sunrise Manufacturing Ltd is led by a SATISFACTORY management team (composite score: 7/10). The MD brings 18 years of manufacturing experience supported by a Fellow ICAN finance director and a former CBN Deputy Director as NED. Key man risk is noted and key man insurance plus a succession plan are required as credit conditions. Board governance is ADEQUATE though an audit committee should be established.",
        "_metadata": {
            "mode":               "mock",
            "model":              None,
            "searches_conducted": [],
            "input_tokens":       0,
            "output_tokens":      0,
            "estimated_cost_usd": 0.0,
        },
    }
 
 
# ─────────────────────────────────────────────────────
# AGENTIC LOOP — same pattern as kyc_agent.py
# ─────────────────────────────────────────────────────
 
def _run_claude_analysis(form_data: dict, max_rounds: int = 10) -> dict:
    """
    Call Claude with web search and loop until end_turn.
    More rounds than other agents because each director needs separate searches.
    """
    if client is None:
        r = _build_fallback(form_data)
        r["_metadata"]["error"] = "ANTHROPIC_API_KEY not set."
        return r
 
    company   = form_data.get("company_name", "the applicant")
    directors = form_data.get("directors", [])
    n_dirs    = len(directors)
 
    user_message = (
        f"Assess the management team of {company} for a credit application.\n\n"
        "MANAGEMENT DATA (from relationship manager):\n"
        f"{json.dumps(form_data, indent=2)}\n\n"
        "INSTRUCTIONS:\n"
        f"1. Search the web for each of the {n_dirs} director(s) listed above.\n"
        "2. Verify CAC registration for the company.\n"
        "3. Research previous companies and professional standing.\n"
        "4. After all searches, return ONLY the JSON object."
    )
 
    messages = [{"role": "user", "content": user_message}]
    searches = []
 
    try:
        for round_num in range(max_rounds):
            response = client.messages.create(
                model=MODEL,
                max_tokens=6000,
                system=SYSTEM_PROMPT,
                tools=[WEB_SEARCH],
                messages=messages,
            )
 
            if response.stop_reason == "end_turn":
                text = "\n".join(
                    b.text for b in response.content
                    if getattr(b, "type", None) == "text"
                ).strip()
                result = _parse_json(text)
                result["_metadata"] = {
                    "mode":               "claude",
                    "model":              MODEL,
                    "searches_conducted": searches,
                    "input_tokens":       response.usage.input_tokens,
                    "output_tokens":      response.usage.output_tokens,
                    "estimated_cost_usd": round(
                        response.usage.input_tokens  * 0.000003 +
                        response.usage.output_tokens * 0.000015,
                        4,
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
        result["_metadata"]["mode"]               = "fallback_max_rounds"
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
        raise ValueError("Unbalanced JSON braces.")
 
 
def _build_fallback(form_data: dict) -> dict:
    """Deterministic fallback when Claude cannot complete."""
    company   = form_data.get("company_name", "Unknown")
    directors = form_data.get("directors", [])
    rc        = form_data.get("rc_number") or "Not provided"
 
    profiles = []
    for d in directors:
        if not isinstance(d, dict): continue
        yrs = int(d.get("years_of_experience", 0) or 0)
        score = 8 if yrs >= 15 else 6 if yrs >= 10 else 4 if yrs >= 5 else 2
        profiles.append({
            "name":                     d.get("name","Unknown"),
            "role":                     d.get("role","Director"),
            "years_of_experience":       yrs,
            "industry_experience_years": yrs,
            "qualifications":            d.get("qualifications",[]),
            "professional_memberships":  [],
            "previous_companies":        [],
            "track_record":              "SATISFACTORY",
            "track_record_detail":       "Fallback — web search not completed.",
            "key_man_risk":               d.get("is_key_man",False),
            "cac_registered":            "NOT_CONFIRMED",
            "web_search_findings":       "Web search not run in fallback mode.",
            "individual_score":           score,
            "individual_score_narrative": f"Score based on {yrs} years experience (fallback).",
        })
 
    scores    = [p["individual_score"] for p in profiles] or [5]
    avg_score = round(sum(scores)/len(scores),1)
    quality   = "STRONG" if avg_score>=8 else "SATISFACTORY" if avg_score>=5 else "WEAK"
    key_man   = any(p["key_man_risk"] for p in profiles)
 
    flags = []
    if key_man:
        flags.append({"flag":"Key Person Dependency","severity":"HIGH",
            "detail":"Key man risk identified from form data.",
            "action_required":"Key man insurance and succession plan required."})
    if avg_score < 5:
        flags.append({"flag":"Management Quality Risk","severity":"HIGH",
            "detail":f"Average management score of {avg_score}/10 indicates WEAK management.",
            "action_required":"Additional due diligence on management capability required."})
 
    n_exec  = sum(1 for d in directors if isinstance(d,dict) and not d.get("is_non_executive",False))
    n_nexec = len(directors) - n_exec
    indep_pct = round(n_nexec/max(len(directors),1)*100,1)
 
    return {
        "management_overview": {
            "company_name":           company,
            "total_directors":         len(directors),
            "executive_directors":     n_exec,
            "non_executive_directors": n_nexec,
            "board_independence_pct":  indep_pct,
            "cac_rc_number":           rc,
            "cac_verification_status": "NOT_CONFIRMED",
        },
        "director_profiles": profiles,
        "board_assessment": {
            "governance_structure":    "ADEQUATE" if indep_pct>=33 else "WEAK",
            "governance_commentary":   "Fallback governance assessment based on form data.",
            "audit_committee_present":  form_data.get("audit_committee",False),
            "ceo_chairman_separation":  form_data.get("ceo_chairman_separate",True),
            "board_skills_diversity":   "MEDIUM",
        },
        "management_assessment": {
            "overall_management_score": avg_score,
            "management_quality":       quality,
            "key_man_risk_identified":   key_man,
            "key_man_description":      "Key man identified from form data." if key_man else None,
            "succession_planning":      "NOT_ASSESSED",
            "management_stability":     "STABLE",
            "team_depth":               "ADEQUATE",
        },
        "risk_flags": flags,
        "credit_memo_narrative": (
            f"{company} is managed by a team of {len(directors)} directors. "
            f"Average management score: {avg_score}/10 ({quality}). "
            "Manual verification of management credentials is recommended."
        ),
        "_metadata": {
            "mode":"fallback","model":None,"searches_conducted":[],
            "input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0
        },
    }
