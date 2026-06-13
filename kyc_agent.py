import anthropic
import json
import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from screening_apis import screen_all, get_mock_screening_results

# ─────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Bug 6 fix: raise immediately if the system prompt file is missing
# so the problem is obvious on startup rather than silently degrading.
_SYSTEM_PROMPT_PATH = Path("system_prompt_kyc.txt")
if not _SYSTEM_PROMPT_PATH.exists():
    raise FileNotFoundError(
        "system_prompt_kyc.txt not found in the working directory.\n"
        "Make sure the file is present alongside kyc_agent.py before running."
    )

SYSTEM_PROMPT = _SYSTEM_PROMPT_PATH.read_text()

# Bug 4 fix: use Sonnet, not Opus (~15x cheaper with equal capability here).
MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
}


# ─────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINTS — three clean modes for Streamlit
# ─────────────────────────────────────────────────────────────

def run_full_kyc(kyc_data: dict) -> dict:
    """
    Full live mode: calls OpenSanctions + OFAC APIs with real form data,
    then calls Claude with the web_search tool for adverse media research.
    This is the production path for real credit applications.

    Streamlit usage: run_full_kyc(payload)
    Cost: ~$0.03–0.06 per screening (Sonnet + web search tokens).
    """
    screening_results = _fetch_screening_results(kyc_data)
    return _run_claude_analysis(kyc_data, screening_results)


def run_kyc_with_mock_apis(kyc_data: dict) -> dict:
    """
    Bug 5 fix — Middle mode: calls real OpenSanctions + OFAC APIs with the
    actual form data, but skips the Claude web search step entirely.

    Useful for testing API connectivity and verifying your OPENSANCTIONS_API_KEY
    is working without spending any Claude API credits. The result is built
    deterministically from the real API screening data.

    Streamlit usage: run_kyc_with_mock_apis(payload)
    Cost: OpenSanctions API calls only (~free on the free tier).
    """
    screening_results = _fetch_screening_results(kyc_data)
    return _build_deterministic_result(kyc_data, screening_results)


def get_mock_kyc_result() -> dict:
    """
    Full mock mode: returns a static hardcoded dict. Zero API calls.

    Bug 9 fix: the old version called build_deterministic_kyc_result() which
    produced a simpler structure than real Claude output, meaning the Streamlit
    UI was tested against the wrong data shape. This version returns a static
    dict that exactly mirrors the full Claude output structure defined in
    system_prompt_kyc.txt, so all UI paths are exercised in mock mode.

    Streamlit usage: get_mock_kyc_result()
    Cost: $0.00
    """
    return {
        "screening_metadata": {
            "company_name": "Sunrise Manufacturing Ltd",
            "rc_number": "RC-482931",
            "screening_date": str(date.today()),
            "sources_checked": [
                "OpenSanctions",
                "OFAC SDN",
                "Claude Web Search",
                "CAC Nigeria",
            ],
            "web_searches_conducted": [
                "Chidi Okonkwo fraud Nigeria EFCC",
                "Adaeze Nwosu court case money laundering",
                "Sunrise Manufacturing Ltd legal dispute Nigeria",
            ],
        },
        "company_screening": {
            "cac_status": "REGISTERED",
            "cac_rc_number": "RC-482931",
            "cac_date_incorporated": "March 2008",
            "company_type": "Private Limited Company",
            "company_sanctions_match": False,
            "company_sanctions_detail": None,
            "company_adverse_media": "MINOR",
            "company_adverse_media_summary": (
                "One unresolved trade dispute reported in a 2021 Business Day article. "
                "No criminal allegations — matter settled out of court per public record."
            ),
        },
        "director_screenings": [
            {
                "director_name": "Chidi Okonkwo",
                "position": "Managing Director / CEO",
                "pep_status": False,
                "pep_detail": None,
                "sanctions_match": False,
                "sanctions_detail": None,
                "ofac_match": False,
                "adverse_media": "NONE",
                "adverse_media_summary": (
                    "No adverse media found across multiple web search queries. "
                    "No EFCC, court case, or regulatory mention identified."
                ),
                "individual_risk_rating": "LOW",
                "individual_risk_narrative": (
                    "Mr Okonkwo presents a low individual risk profile. "
                    "No sanctions matches, no PEP status, and no adverse media found."
                ),
            },
            {
                "director_name": "Adaeze Nwosu",
                "position": "Executive Director, Finance",
                "pep_status": True,
                "pep_detail": (
                    "Sibling of serving Anambra State Commissioner for Finance — "
                    "immediate family member of PEP under CBN KYC/AML Manual definition."
                ),
                "sanctions_match": False,
                "sanctions_detail": None,
                "ofac_match": False,
                "adverse_media": "NONE",
                "adverse_media_summary": (
                    "No adverse media found. PEP connection is by family relationship only."
                ),
                "individual_risk_rating": "HIGH",
                "individual_risk_narrative": (
                    "Ms Nwosu is flagged as PEP-connected under the CBN KYC/AML Manual "
                    "by virtue of her sibling relationship with a serving State Commissioner. "
                    "Enhanced Due Diligence and senior management approval are mandatory "
                    "regardless of personal conduct."
                ),
            },
        ],
        "aggregate_assessment": {
            "overall_kyc_risk_rating": "HIGH",
            "due_diligence_tier": "EDD",
            "highest_individual_risk": "Adaeze Nwosu (PEP connection)",
            "cbn_reporting_required": False,
            "nfiu_str_required": False,
            "senior_management_approval_required": True,
        },
        "risk_flags": [
            {
                "flag": "PEP-Connected Director",
                "severity": "HIGH",
                "detail": (
                    "Adaeze Nwosu (ED Finance) is an immediate family member of a "
                    "serving State Commissioner — PEP-connected under CBN KYC/AML Manual."
                ),
                "regulatory_reference": "CBN KYC/AML Manual 2023 — PEP Enhanced Due Diligence",
                "action_required": (
                    "Obtain source of funds declaration, enhanced beneficial ownership "
                    "mapping, and senior management sign-off before credit approval."
                ),
            },
            {
                "flag": "Minor Adverse Media — Company",
                "severity": "LOW",
                "detail": "Unresolved trade dispute reported 2021 — settled out of court.",
                "regulatory_reference": "CBN KYC Reputation Assessment",
                "action_required": "Obtain settlement confirmation for the credit file.",
            },
        ],
        "required_documentation": [
            "Source of funds declaration — Adaeze Nwosu (EDD requirement)",
            "Enhanced beneficial ownership form — all directors with >5% economic interest",
            "Senior management sign-off — CCO or MD approval required",
            "Trade dispute settlement confirmation (2021 matter)",
            "Standard CBN KYC forms — all directors",
        ],
        "credit_memo_narrative": (
            "Sunrise Manufacturing Ltd presents a HIGH KYC risk rating driven by the "
            "PEP-connected status of Executive Director (Finance) Adaeze Nwosu, who is "
            "an immediate family member of a serving Anambra State Commissioner under "
            "the CBN KYC/AML Manual definition. No sanctions matches were identified "
            "for any director or the company across OpenSanctions and OFAC databases. "
            "Enhanced Due Diligence is required, including a source of funds declaration, "
            "enhanced beneficial ownership mapping, and senior management approval before "
            "the credit can proceed."
        ),
        "_metadata": {
            "mode": "mock",
            "model": None,
            "rounds": 0,
            "queries": [],
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _extract_director_names(kyc_data: dict) -> list:
    """
    Safely pull non-empty director names from the payload regardless of
    whether directors is a list of dicts (Streamlit form) or strings.
    """
    directors = kyc_data.get("directors", [])
    names = []

    if isinstance(directors, list):
        for d in directors:
            if isinstance(d, dict):
                name = (d.get("name") or d.get("director_name") or "").strip()
                if name:
                    names.append(name)
            elif isinstance(d, str) and d.strip():
                names.append(d.strip())

    return names


def _fetch_screening_results(kyc_data: dict) -> dict:
    """
    Call OpenSanctions + OFAC for the company and all directors.
    Catches all API errors so a network or key failure never crashes the app.
    Returns a flat dict keyed by entity name.
    """
    company_name   = kyc_data.get("company_name", "").strip()
    director_names = _extract_director_names(kyc_data)

    results = {}

    try:
        if company_name:
            results.update(screen_all([company_name], is_company=True))
    except Exception as exc:
        results["_company_api_error"] = str(exc)

    try:
        if director_names:
            results.update(screen_all(director_names, is_company=False))
    except Exception as exc:
        results["_director_api_error"] = str(exc)

    return results


def _extract_text(response) -> str:
    """Collect all text blocks from a Claude API response into one string."""
    return "\n".join(
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    ).strip()


def _extract_json(text: str) -> dict:
    """
    Bug 7 fix:
      - Strip markdown code fences (```json ... ```) before parsing.
      - Use json.JSONDecodeError, not a bare except.
      - Use brace-counting to find the outermost JSON object safely.
    """
    # Strip ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip()).strip()

    # First attempt: parse the whole cleaned string directly
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Second attempt: find the outermost JSON object using brace counting
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(
            f"No JSON object found in Claude response.\n"
            f"First 300 chars: {text[:300]}"
        )

    depth = 0
    for i, ch in enumerate(cleaned[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start : i + 1])
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Found JSON-like block but could not parse it: {exc}\n"
                        f"Block (first 300 chars): {cleaned[start : i + 1][:300]}"
                    ) from exc

    raise ValueError(
        f"Unbalanced braces in Claude response.\n"
        f"First 300 chars: {text[:300]}"
    )


# ─────────────────────────────────────────────────────────────
# CORE CLAUDE ANALYSIS — AGENTIC LOOP
# ─────────────────────────────────────────────────────────────

def _run_claude_analysis(
    kyc_data: dict,
    screening_results: dict,
    max_rounds: int = 6,
) -> dict:
    """
    Call Claude with the web_search tool and loop until stop_reason == 'end_turn'.
    Falls back to the deterministic result if Claude fails or the response is
    unparseable, with the error recorded in _metadata so it is visible in the UI.
    """
    if client is None:
        result = _build_deterministic_result(kyc_data, screening_results)
        result["_metadata"]["error"] = (
            "ANTHROPIC_API_KEY is not set — using deterministic fallback. "
            "Add your key to the .env file and restart."
        )
        return result

    director_names = _extract_director_names(kyc_data)

    # Bug 8 fix: surface a clear warning when no director names were provided
    if not director_names:
        result = _build_deterministic_result(kyc_data, screening_results)
        result["_metadata"]["warning"] = (
            "No director names were entered on the form. "
            "Screening results will be incomplete. "
            "Please add at least one director's full name and rerun."
        )
        return result

    user_message = (
        "Perform full KYC and reputation screening for this entity.\n\n"
        "ENTITY DATA:\n"
        f"{json.dumps(kyc_data, indent=2)}\n\n"
        "PRE-FETCHED API SCREENING RESULTS (OpenSanctions + OFAC):\n"
        f"{json.dumps(screening_results, indent=2)}\n\n"
        "INSTRUCTIONS:\n"
        "1. Use the web_search tool to search for adverse media on each director "
        "and the company — EFCC cases, court records, regulatory sanctions, fraud allegations.\n"
        "2. Complete all searches before producing your final answer.\n"
        "3. Return ONLY the final JSON object — no text before or after it."
    )

    messages = [{"role": "user", "content": user_message}]
    queries = []

    try:
        for round_num in range(max_rounds):

            response = client.messages.create(
                model=MODEL,
                max_tokens=6000,
                system=SYSTEM_PROMPT,
                tools=[WEB_SEARCH_TOOL],
                messages=messages,
            )

            # Claude finished — extract and return the JSON result
            if response.stop_reason == "end_turn":
                text   = _extract_text(response)
                result = _extract_json(text)
                result["_metadata"] = {
                    "mode":              "claude",
                    "model":             MODEL,
                    "rounds":            round_num + 1,
                    "queries":           queries,
                    "input_tokens":      response.usage.input_tokens,
                    "output_tokens":     response.usage.output_tokens,
                    "estimated_cost_usd": round(
                        response.usage.input_tokens  * 0.000003 +
                        response.usage.output_tokens * 0.000015,
                        4,
                    ),
                }
                return result

            # Claude called a tool — add the response and send back tool results
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if getattr(block, "type", None) == "tool_use":
                        if block.name == "web_search":
                            queries.append(block.input.get("query", ""))
                        tool_results.append({
                            "type":        "tool_result",
                            "tool_use_id": block.id,
                            "content":     "Search executed.",
                        })

                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason — break and use fallback
            break

        # Bug 3 fix: final fallback is inside the try/except and uses safe dict access
        result = _build_deterministic_result(kyc_data, screening_results)
        result["_metadata"]["mode"]    = "fallback_max_rounds"
        result["_metadata"]["queries"] = queries
        return result

    except (ValueError, json.JSONDecodeError) as exc:
        result = _build_deterministic_result(kyc_data, screening_results)
        result["_metadata"]["error"]   = f"JSON parse error: {exc}"
        result["_metadata"]["queries"] = queries
        return result

    except anthropic.APIError as exc:
        result = _build_deterministic_result(kyc_data, screening_results)
        result["_metadata"]["error"] = f"Anthropic API error: {exc}"
        return result

    except Exception as exc:
        result = _build_deterministic_result(kyc_data, screening_results)
        result["_metadata"]["error"] = (
            f"Unexpected error: {type(exc).__name__}: {exc}"
        )
        return result


# ─────────────────────────────────────────────────────────────
# SCREENING RESULT HELPERS
# ─────────────────────────────────────────────────────────────

def _is_pep_from_screening(screening_results: dict, name: str) -> bool:
    """
    Check whether OpenSanctions flagged this person as a PEP by inspecting
    the topics and datasets fields of each matching result.
    """
    entity  = screening_results.get(name, {})
    matches = entity.get("opensanctions", {}).get("matches", [])
    for match in matches:
        if match.get("is_pep"):
            return True
        topics   = match.get("topics", [])
        datasets = match.get("datasets", [])
        if any("pep" in str(item).lower() for item in topics + datasets):
            return True
    return False


def _has_sanctions_match(screening_results: dict, name: str) -> bool:
    entity = screening_results.get(name, {})
    os_    = entity.get("opensanctions", {})
    return bool(
        os_.get("high_confidence_match", False)
        or os_.get("matches_found", 0) > 0
    )


def _has_ofac_match(screening_results: dict, name: str) -> bool:
    entity = screening_results.get(name, {})
    return entity.get("ofac", {}).get("matches_found", 0) > 0


# ─────────────────────────────────────────────────────────────
# DETERMINISTIC FALLBACK — COMPLETE RESULT STRUCTURE
# ─────────────────────────────────────────────────────────────

def _build_deterministic_result(
    kyc_data: dict,
    screening_results: dict,
) -> dict:
    """
    Build a complete KYC result without calling Claude.
    Used by run_kyc_with_mock_apis() and as the error fallback in
    _run_claude_analysis() when Claude fails or returns unparseable output.

    Bug 1 fix: PEP detection reads self_declared_pep and family_pep_connection
    from the Streamlit form payload, plus the is_pep flag from OpenSanctions.
    keyword_match() on director name strings has been removed.

    Bug 2 fix: result includes every field the Streamlit UI accesses:
    company_screening, risk_flags, required_documentation,
    credit_memo_narrative, position, pep_detail, individual_risk_narrative.
    """
    company = kyc_data.get("company_name", "Unknown").strip()
    rc      = kyc_data.get("rc_number") or "Not provided"
    today   = str(date.today())

    directors = kyc_data.get("directors", [])
    if not directors:
        directors = [{"name": "Not provided", "position": "Unknown"}]

    director_screenings = []
    risk_flags          = []
    required_docs       = ["Standard CBN KYC forms — all directors and the company"]

    for d in directors:
        if not isinstance(d, dict):
            continue

        name     = (d.get("name") or d.get("director_name") or "Unknown").strip()
        position = d.get("position") or "Director"

        # Bug 1 fix: read PEP flags from the form, not from the name string
        self_pep   = bool(d.get("self_declared_pep", False))
        family_pep = bool(d.get("family_pep_connection", False))
        api_pep    = _is_pep_from_screening(screening_results, name)

        is_pep = self_pep or family_pep or api_pep

        if self_pep:
            pep_detail = (
                f"{name} self-declared as currently or previously holding public office."
            )
        elif family_pep:
            pep_detail = (
                f"{name} declared a family member holding public office — "
                "PEP-connected under CBN KYC/AML Manual definition."
            )
        elif api_pep:
            pep_detail = (
                f"{name} flagged as PEP by OpenSanctions database."
            )
        else:
            pep_detail = None

        sanctions = _has_sanctions_match(screening_results, name)
        ofac      = _has_ofac_match(screening_results, name)

        # Individual risk rating
        if sanctions or ofac:
            individual_rating     = "VERY_HIGH"
            individual_narrative  = (
                f"{name} has a confirmed match on one or more sanctions lists. "
                "This is a mandatory decline condition — do not proceed without "
                "written compliance officer sign-off."
            )
        elif is_pep:
            individual_rating     = "HIGH"
            individual_narrative  = (
                f"{name} holds or is connected to a PEP status. "
                "Enhanced Due Diligence is mandatory under the CBN KYC/AML Manual. "
                "Source of funds documentation and senior management sign-off are required."
            )
        else:
            individual_rating     = "LOW"
            individual_narrative  = (
                f"{name} presents a low individual risk profile based on available "
                "screening data. Standard Due Diligence documentation is sufficient."
            )

        director_screenings.append({
            "director_name":             name,
            "position":                  position,
            "pep_status":                is_pep,
            "pep_detail":                pep_detail,
            "sanctions_match":           sanctions,
            "sanctions_detail":          "Match found on OpenSanctions" if sanctions else None,
            "ofac_match":                ofac,
            "adverse_media":             "NONE",
            "adverse_media_summary":     "Web search not run in deterministic mode.",
            "individual_risk_rating":    individual_rating,
            "individual_risk_narrative": individual_narrative,
        })

        # Accumulate risk flags and required docs
        if sanctions or ofac:
            list_name = "OFAC SDN" if ofac else "OpenSanctions"
            risk_flags.append({
                "flag":                 f"Sanctions Match — {name}",
                "severity":             "HIGH",
                "detail":               f"{name} matched on {list_name}. Mandatory decline.",
                "regulatory_reference": "CBN KYC/AML Manual — Sanctions Screening",
                "action_required":      (
                    "Do not proceed. Escalate to compliance officer immediately."
                ),
            })
            required_docs.append(
                f"Compliance officer written sign-off — {name} sanctions match"
            )

        if is_pep:
            risk_flags.append({
                "flag":                 f"PEP Status — {name}",
                "severity":             "HIGH",
                "detail":               pep_detail or f"{name} is PEP-connected.",
                "regulatory_reference": "CBN KYC/AML Manual 2023 — PEP Enhanced Due Diligence",
                "action_required":      (
                    "Enhanced Due Diligence required. Senior management approval needed."
                ),
            })
            required_docs.append(f"Source of funds declaration — {name}")
            required_docs.append(f"Enhanced beneficial ownership mapping — {name}")

    # Aggregate risk across all directors
    ratings = [d["individual_risk_rating"] for d in director_screenings]

    if "VERY_HIGH" in ratings:
        overall_rating = "VERY_HIGH"
        due_diligence  = "DECLINE"
        sm_approval    = True
        cbn_reporting  = True
    elif "HIGH" in ratings:
        overall_rating = "HIGH"
        due_diligence  = "EDD"
        sm_approval    = True
        cbn_reporting  = False
    elif "MEDIUM" in ratings:
        overall_rating = "MEDIUM"
        due_diligence  = "EDD"
        sm_approval    = False
        cbn_reporting  = False
    else:
        overall_rating = "LOW"
        due_diligence  = "SDD"
        sm_approval    = False
        cbn_reporting  = False

    # Company-level sanctions check
    company_sanctions = _has_sanctions_match(screening_results, company)
    if company_sanctions and overall_rating not in ("VERY_HIGH",):
        overall_rating = "VERY_HIGH"
        due_diligence  = "DECLINE"
        sm_approval    = True
        cbn_reporting  = True
        risk_flags.append({
            "flag":                 f"Company Sanctions Match — {company}",
            "severity":             "HIGH",
            "detail":               f"{company} matched on OpenSanctions. Mandatory decline.",
            "regulatory_reference": "CBN KYC/AML Manual — Sanctions Screening",
            "action_required":      "Do not proceed. Escalate to compliance immediately.",
        })

    if due_diligence == "EDD":
        required_docs.append("Senior management sign-off — CCO or MD approval required")

    # Build credit memo narrative
    high_risk_names = [
        d["director_name"] for d in director_screenings
        if d["individual_risk_rating"] in ("HIGH", "VERY_HIGH")
    ]

    if high_risk_names:
        narrative = (
            f"{company} presents a {overall_rating} KYC risk rating driven by concerns "
            f"relating to {', '.join(high_risk_names)}. "
            f"{due_diligence} is required before the credit can proceed."
            + (" Senior management approval is mandatory." if sm_approval else "")
        ).strip()
    else:
        narrative = (
            f"{company} presents a LOW KYC risk rating. "
            "No sanctions matches, PEP status, or adverse media were identified across "
            "available screening sources. "
            "Standard Due Diligence documentation is sufficient."
        )

    return {
        "screening_metadata": {
            "company_name":           company,
            "rc_number":              rc,
            "screening_date":         today,
            "sources_checked":        ["OpenSanctions", "OFAC SDN"],
            "web_searches_conducted": [],
        },
        "company_screening": {
            "cac_status":                "NOT_INDEPENDENTLY_VERIFIED",
            "cac_rc_number":             rc,
            "cac_date_incorporated":     None,
            "company_type":              None,
            "company_sanctions_match":   company_sanctions,
            "company_sanctions_detail":  "Match found" if company_sanctions else None,
            "company_adverse_media":     "NONE",
            "company_adverse_media_summary": "Web search not run in deterministic mode.",
        },
        "director_screenings":    director_screenings,
        "aggregate_assessment": {
            "overall_kyc_risk_rating":            overall_rating,
            "due_diligence_tier":                 due_diligence,
            "highest_individual_risk":            high_risk_names[0] if high_risk_names else "None",
            "cbn_reporting_required":             cbn_reporting,
            "nfiu_str_required":                  cbn_reporting,
            "senior_management_approval_required": sm_approval,
        },
        "risk_flags":             risk_flags,
        "required_documentation": list(dict.fromkeys(required_docs)),  # deduplicate
        "credit_memo_narrative":  narrative,
        "_metadata": {
            "mode":               "deterministic",
            "model":              None,
            "rounds":             0,
            "queries":            [],
            "input_tokens":       0,
            "output_tokens":      0,
            "estimated_cost_usd": 0.0,
        },
    }

