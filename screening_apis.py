 
import os
import requests
from dotenv import load_dotenv
 
load_dotenv()
 
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")
 
 
# ─────────────────────────────────────────────────────────────
# OPENSANCTIONS — 180+ global lists, PEP database
# Docs: https://www.opensanctions.org/api/
# Free tier: 100 requests/day (no key needed)
# Paid:      $99/month unlimited (set OPENSANCTIONS_API_KEY in .env)
# ─────────────────────────────────────────────────────────────
 
def check_opensanctions(name: str, schema: str = "Person") -> dict:
    """
    Screen a name against the OpenSanctions consolidated database.
 
    Args:
        name:   Full name to screen (director or company).
        schema: "Person" for directors, "Company" for the entity.
 
    Returns:
        dict with keys:
          status               — "checked" | "rate_limited" | "error_NNN" | "error"
          matches_found        — int
          high_confidence_match — bool (True if any match score >= 0.80)
          matches              — list of top matches (up to 5)
    """
    url = "https://api.opensanctions.org/match/default"
 
    payload = {
        "queries": {
            "q1": {
                "schema": schema,
                "properties": {"name": [name]},
            }
        }
    }
 
    headers = {"Content-Type": "application/json"}
    if OPENSANCTIONS_API_KEY:
        headers["Authorization"] = f"ApiKey {OPENSANCTIONS_API_KEY}"
 
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15,
        )
 
        if response.status_code == 200:
            data    = response.json()
            results = (
                data
                .get("responses", {})
                .get("q1", {})
                .get("results", [])
            )
            if not isinstance(results, list):
                results = []
 
            # Only surface results with a meaningful match score
            matches = [
                {
                    "name":     r.get("caption", ""),
                    "score":    r.get("score", 0),
                    "datasets": r.get("datasets", []),
                    "is_pep":   "peps" in " ".join(r.get("datasets", [])).lower(),
                    "topics":   r.get("properties", {}).get("topics", []),
                }
                for r in results
                if r.get("score", 0) >= 0.60
            ]
 
            return {
                "status":                "checked",
                "matches_found":         len(matches),
                "high_confidence_match": any(m["score"] >= 0.80 for m in matches),
                "matches":               matches[:5],
            }
 
        if response.status_code == 429:
            return {
                "status":                "rate_limited",
                "matches_found":         0,
                "high_confidence_match": False,
                "matches":               [],
                "note": (
                    "OpenSanctions free-tier daily limit reached. "
                    "Add OPENSANCTIONS_API_KEY to .env for unlimited access "
                    "or retry after midnight UTC."
                ),
            }
 
        return {
            "status":                f"error_{response.status_code}",
            "matches_found":         0,
            "high_confidence_match": False,
            "matches":               [],
            "note": f"OpenSanctions returned HTTP {response.status_code}.",
        }
 
    except requests.exceptions.Timeout:
        return {
            "status":                "timeout",
            "matches_found":         0,
            "high_confidence_match": False,
            "matches":               [],
            "note": "OpenSanctions request timed out after 15 seconds.",
        }
 
    except Exception as exc:
        return {
            "status":                "error",
            "matches_found":         0,
            "high_confidence_match": False,
            "matches":               [],
            "note": f"OpenSanctions error: {type(exc).__name__}: {exc}",
        }
 
 
# ─────────────────────────────────────────────────────────────
# OFAC SDN — US Treasury Specially Designated Nationals list
# Docs: https://ofac.treasury.gov/api
# Free public API — no key required.
#
# NOTE: OpenSanctions' default index already includes the full OFAC SDN
# dataset. A clean OpenSanctions result therefore provides equivalent
# coverage even when the direct OFAC API is unreachable.
# ─────────────────────────────────────────────────────────────
 
def check_ofac_sdn(name: str) -> dict:
    """
    Screen a name against the OFAC Specially Designated Nationals (SDN) list.
 
    Tries the v2 endpoint first, then falls back to v1. Both response
    structures are handled. Returns a structured "unavailable" result
    (not a bare exception) when both URLs fail, so Claude can report
    the situation precisely rather than producing a vague message.
 
    Args:
        name: Full name to screen.
 
    Returns:
        dict with keys:
          status         — "checked" | "unavailable"
          matches_found  — int
          matches        — list of matching SDN entries (up to 3)
          source_url     — which endpoint responded (when checked)
          note           — human-readable explanation (when unavailable)
    """
    # Try v2 first, fall back to v1 if needed
    endpoints = [
        "https://api.ofac.treasury.gov/v2/sdn/search",
        "https://api.ofac.treasury.gov/v1/sdn/search",
    ]
    params = {"name": name, "minScore": 60}
 
    last_error = ""
 
    for url in endpoints:
        try:
            response = requests.get(url, params=params, timeout=20)
 
            if response.status_code == 200:
                data = response.json()
 
                # Handle v1 structure: {"sdnList": {"sdnEntry": [...]}}
                # Handle v2 structure: {"results": [...]}
                entries = (
                    data.get("sdnList", {}).get("sdnEntry")
                    or data.get("results")
                    or []
                )
 
                # The API sometimes returns a single dict instead of a list
                if isinstance(entries, dict):
                    entries = [entries]
                if not isinstance(entries, list):
                    entries = []
 
                matches = [
                    {
                        "name": (
                            (
                                e.get("lastName", "")
                                + " "
                                + e.get("firstName", "")
                            ).strip()
                            or e.get("name", "")
                            or e.get("caption", "")
                        ),
                        "sdn_type": e.get("sdnType") or e.get("type", ""),
                        "program":  str(
                            e.get("programList", {}).get("program", "")
                            or e.get("program", "")
                        ),
                    }
                    for e in entries
                ]
 
                return {
                    "status":        "checked",
                    "source_url":    url,
                    "matches_found": len(matches),
                    "matches":       matches[:3],
                }
 
            # Non-200 response — note the error and try the next URL
            last_error = f"HTTP {response.status_code} from {url}"
 
        except requests.exceptions.Timeout:
            last_error = f"Timeout after 20 s from {url}"
            continue
 
        except requests.exceptions.ConnectionError as exc:
            last_error = f"Connection error from {url}: {exc}"
            continue
 
        except Exception as exc:
            last_error = f"{type(exc).__name__} from {url}: {exc}"
            continue
 
    # Both endpoints failed — return a clear, structured unavailable status.
    # Claude reads this "note" field and produces a precise output rather
    # than a vague "inconclusive due to API failure" message.
    return {
        "status":        "unavailable",
        "matches_found": 0,
        "matches":       [],
        "last_error":    last_error,
        "note": (
            "The OFAC SDN direct API was unreachable at the time of screening "
            f"({last_error}). "
            "This does not indicate a sanctions match or a clean result. "
            "OpenSanctions screening above incorporates the full OFAC SDN "
            "dataset and provides equivalent coverage for this check. "
            "A manual OFAC verification is recommended before credit approval."
        ),
    }
 
 
# ─────────────────────────────────────────────────────────────
# SCREEN ALL — run both APIs for a list of names
# ─────────────────────────────────────────────────────────────
 
def screen_all(names: list, is_company: bool = False) -> dict:
    """
    Screen a list of names (directors or company) across all available APIs.
 
    Args:
        names:      List of name strings to screen.
        is_company: True to use the "Company" schema for OpenSanctions,
                    False (default) to use "Person".
 
    Returns:
        Flat dict keyed by name, each value containing:
          {"opensanctions": {...}, "ofac": {...}}
 
    Example:
        screen_all(["Chidi Okonkwo", "Adaeze Nwosu"], is_company=False)
        → {
            "Chidi Okonkwo": {"opensanctions": {...}, "ofac": {...}},
            "Adaeze Nwosu":  {"opensanctions": {...}, "ofac": {...}},
          }
    """
    schema  = "Company" if is_company else "Person"
    results = {}
 
    for name in names:
        name = (name or "").strip()
        if not name:
            continue
 
        results[name] = {
            "opensanctions": check_opensanctions(name, schema=schema),
            "ofac":          check_ofac_sdn(name),
        }
 
    return results
 
 
# ─────────────────────────────────────────────────────────────
# MOCK RESULTS — for UI testing and the Full Mock Streamlit mode
# ─────────────────────────────────────────────────────────────
 
def get_mock_screening_results() -> dict:
    """
    Hardcoded screening results for use in Full Mock mode.
    No API calls are made. Returns a structure that matches what
    screen_all() produces so the rest of the agent code is exercised
    exactly as in live mode.
 
    Simulates:
      - One clean director (no matches anywhere)
      - One company with a clean result
    """
    return {
        "Chidi Okonkwo": {
            "opensanctions": {
                "status":                "checked",
                "matches_found":         0,
                "high_confidence_match": False,
                "matches":               [],
            },
            "ofac": {
                "status":        "checked",
                "source_url":    "https://api.ofac.treasury.gov/v2/sdn/search",
                "matches_found": 0,
                "matches":       [],
            },
        },
        "Adaeze Nwosu": {
            "opensanctions": {
                "status":                "checked",
                "matches_found":         0,
                "high_confidence_match": False,
                "matches":               [],
            },
            "ofac": {
                "status":        "checked",
                "source_url":    "https://api.ofac.treasury.gov/v2/sdn/search",
                "matches_found": 0,
                "matches":       [],
            },
        },
        "Sunrise Manufacturing Ltd": {
            "opensanctions": {
                "status":                "checked",
                "matches_found":         0,
                "high_confidence_match": False,
                "matches":               [],
            },
            "ofac": {
                "status":        "checked",
                "source_url":    "https://api.ofac.treasury.gov/v2/sdn/search",
                "matches_found": 0,
                "matches":       [],
            },
        },
    }
 
