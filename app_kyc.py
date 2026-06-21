import streamlit as st
import pandas as pd
from kyc_agent import run_full_kyc, run_kyc_with_mock_apis, get_mock_kyc_result
 
st.set_page_config(
    page_title="IncepifyAI — Reputation & KYC Agent",
    page_icon="🔍",
    layout="wide",
)
 
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #534AB7;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Reputation & KYC Agent · Agent 3 of 8 · CBN AML/CFT Compliant</span>
    </div>""",
    unsafe_allow_html=True,
)
 
INDUSTRIES = [
    "Manufacturing", "Oil & Gas Trading", "Real Estate", "Agriculture",
    "Financial Services", "Technology", "Construction", "Retail & Distribution",
    "Healthcare", "Education", "Mining", "Political Consulting", "Other",
]
 
# ── Session state: director list ──────────────────────────────
if "directors" not in st.session_state:
    st.session_state.directors = [{"id": 1}]
 
# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Entity Details")
    company_name = st.text_input(
        "Company Name",
        placeholder="e.g. Sunrise Manufacturing Ltd",
    )
    rc_number = st.text_input(
        "CAC RC Number (optional)",
        placeholder="e.g. RC-482931",
    )
    industry = st.selectbox("Industry", INDUSTRIES)
    country = st.selectbox(
        "Country of Incorporation",
        ["Nigeria", "Ghana", "Kenya", "South Africa", "Other"],
    )
 
    st.markdown("---")
    st.markdown("### Run Mode")
    run_mode = st.radio(
        "Select mode:",
        ["Full mock (no API)", "APIs live + Claude mock", "Full live"],
        help="Use Full mock for UI testing. Full live for real screening.",
    )
 
    st.markdown("---")
    if st.button("+ Add Director", use_container_width=True):
        new_id = max(d["id"] for d in st.session_state.directors) + 1
        st.session_state.directors.append({"id": new_id})
        st.rerun()
 
    run_btn = st.button(
        "Run KYC Screening",
        type="primary",
        use_container_width=True,
        disabled=not company_name and run_mode != "Full mock (no API)",
    )
 
    if "kyc_result" in st.session_state:
        meta = st.session_state["kyc_result"].get("_metadata", {})
        st.markdown("---")
        st.caption(f"Mode: {meta.get('mode', '—')}")
        st.caption(f"Searches run: {len(meta.get('queries', []))}")
        st.caption(f"Cost: ${meta.get('estimated_cost_usd', 0):.4f} USD")
        if meta.get("error"):
            st.caption(f"⚠️ {meta['error'][:80]}")
        if meta.get("warning"):
            st.caption(f"⚠️ {meta['warning'][:80]}")
 
# ── Director entry forms ────────────────────────────────────────
if "kyc_result" not in st.session_state:
    st.markdown("### Directors & Key Officers")
    directors_data = []
    for d in st.session_state.directors:
        did = d["id"]
        with st.expander(f"Director / Officer {did}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                d_name = st.text_input(
                    f"Full Name #{did}",
                    placeholder="e.g. Chidi Okonkwo",
                    key=f"name_{did}",
                )
                d_position = st.text_input(
                    f"Position #{did}",
                    placeholder="e.g. Managing Director",
                    key=f"pos_{did}",
                )
                d_nat = st.selectbox(
                    f"Nationality #{did}",
                    ["Nigerian", "Ghanaian", "Kenyan", "British", "American", "Other"],
                    key=f"nat_{did}",
                )
            with c2:
                d_pep_self = st.checkbox(
                    f"Currently holds / held public office #{did}",
                    key=f"pep_{did}",
                )
                d_pep_fam = st.checkbox(
                    f"Family member holds public office #{did}",
                    key=f"pepfam_{did}",
                )
                d_notes = st.text_input(
                    f"Additional context #{did}",
                    placeholder="e.g. Previously CFO at GTBank",
                    key=f"notes_{did}",
                )
            if len(st.session_state.directors) > 1:
                if st.button(f"Remove #{did}", key=f"rm_{did}"):
                    st.session_state.directors = [
                        x for x in st.session_state.directors if x["id"] != did
                    ]
                    st.rerun()
            directors_data.append({
                "name": d_name,
                "position": d_position,
                "nationality": d_nat,
                "self_declared_pep": d_pep_self,
                "family_pep_connection": d_pep_fam,
                "notes": d_notes or None,
            })
    st.session_state["_directors"] = directors_data
 
# ── Run ───────────────────────────────────────────────────────
if run_btn:
    payload = {
        "company_name": company_name,
        "rc_number": rc_number or None,
        "industry": industry,
        "country": country,
        "directors": st.session_state.get("_directors", []),
    }
    if run_mode == "Full mock (no API)":
        st.session_state["kyc_result"] = get_mock_kyc_result()
    elif run_mode == "APIs live + Claude mock":
        with st.spinner("Running sanctions API screening (no Claude)..."):
            st.session_state["kyc_result"] = run_kyc_with_mock_apis(payload)
    else:
        with st.spinner("Running full KYC screening — web search in progress..."):
            st.session_state["kyc_result"] = run_full_kyc(payload)
 
    # Shared suite key (for forward compatibility with app_suite.py)
    st.session_state["kyc_stored"] = st.session_state["kyc_result"]
    st.rerun()
 
# ── Nothing run yet ──────────────────────────────────────────────
if "kyc_result" not in st.session_state:
    c1, c2, c3 = st.columns(3)
    c1.metric("Screening sources", "8", "Global + Nigeria-specific")
    c2.metric("PEP definitions", "CBN Manual 2023", "All categories")
    c3.metric("Sanctions lists", "180+", "via OpenSanctions")
    st.info("Enter entity details in the sidebar and click Run KYC Screening.")
    st.stop()
 
# ══════════════════════════════════════════════════════════════
# RESULTS DISPLAY — using the VERIFIED CORRECT field names that
# match kyc_agent.py's actual output:
#   company_screening (not company_overview)
#   director_screenings (not director_profiles)
#   required_documentation as a flat list (not documents_required as a dict)
# ══════════════════════════════════════════════════════════════
 
r = st.session_state["kyc_result"]
agg = r.get("aggregate_assessment", {})
rating = agg.get("overall_kyc_risk_rating", "—")
tier = agg.get("due_diligence_tier", "—")
 
rating_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red", "VERY_HIGH": "red"}
col = rating_colors.get(rating, "grey")
 
st.markdown(f"## :{col}[KYC Risk: **{rating}**]  ·  Due Diligence Required: **{tier}**")
 
if agg.get("senior_management_approval_required"):
    st.warning("**SENIOR MANAGEMENT APPROVAL REQUIRED** before credit can proceed.")
if agg.get("nfiu_str_required"):
    st.error("**NFIU SUSPICIOUS TRANSACTION REPORT (STR) REQUIRED** — report to NFIU immediately.")
if agg.get("cbn_reporting_required"):
    st.error("**CBN REPORTING OBLIGATION TRIGGERED** — consult compliance officer.")
 
st.markdown(f"> {r.get('credit_memo_narrative', '')}")
st.markdown("---")
 
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Company Screening", "Director Profiles", "Risk Flags",
    "Documentation Required", "Raw JSON",
])
 
# ── Tab 1: Company Screening (reads "company_screening" — CORRECT KEY) ──
with tab1:
    cs = r.get("company_screening", {})
    if not cs:
        st.info(
            "No company screening data found under the 'company_screening' key. "
            "Check the Raw JSON tab to see the actual structure returned."
        )
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("CAC Status", cs.get("cac_status", "—"))
        c2.metric("RC Number", cs.get("cac_rc_number", "—"))
        c3.metric("Incorporated", cs.get("cac_date_incorporated", "—"))
 
        sanc = "HIT" if cs.get("company_sanctions_match") else "CLEAR"
        sc = "red" if cs.get("company_sanctions_match") else "green"
        st.markdown(f"**Sanctions:** :{sc}[{sanc}]")
 
        media_lvl = cs.get("company_adverse_media", "NONE")
        mc = "green" if media_lvl == "NONE" else "orange" if media_lvl == "MINOR" else "red"
        st.markdown(f"**Adverse Media:** :{mc}[{media_lvl}]")
 
        if cs.get("company_adverse_media_summary"):
            st.caption(cs["company_adverse_media_summary"])
        if cs.get("company_type"):
            st.caption(f"Entity type: {cs['company_type']}")
 
# ── Tab 2: Director Profiles (reads "director_screenings" — CORRECT KEY) ──
with tab2:
    director_list = r.get("director_screenings", [])
    if not director_list:
        st.info(
            "No director screening data found under the 'director_screenings' key. "
            "Check the Raw JSON tab to see the actual structure returned."
        )
    for d in director_list:
        dr = d.get("individual_risk_rating", "—")
        dc = "green" if dr == "LOW" else "orange" if dr == "MEDIUM" else "red"
        with st.expander(
            f"{d.get('director_name', '—')} ({d.get('position', '—')}) — :{dc}[{dr}]",
            expanded=True,
        ):
            c1, c2, c3, c4 = st.columns(4)
            pep = "YES" if d.get("pep_status") else "No"
            c1.metric("PEP Status", pep)
            s = "HIT" if d.get("sanctions_match") else "Clear"
            c2.metric("Sanctions", s)
            o = "HIT" if d.get("ofac_match") else "Clear"
            c3.metric("OFAC", o)
            am = d.get("adverse_media", "NONE")
            c4.metric("Adverse Media", am)
            if d.get("pep_detail"):
                st.warning(f"PEP detail: {d['pep_detail']}")
            if d.get("sanctions_detail"):
                st.error(f"Sanctions detail: {d['sanctions_detail']}")
            st.caption(d.get("individual_risk_narrative", ""))
 
# ── Tab 3: Risk Flags (reads "risk_flags" — already correct) ──
with tab3:
    flags = r.get("risk_flags", [])
    if not flags:
        st.success("No risk flags identified.")
    for f in flags:
        sev = f.get("severity", "LOW")
        msg = (
            f"**{f.get('flag', '')}** — {f.get('detail', '')}\n\n"
            f"*Regulatory ref: {f.get('regulatory_reference', '—')}*\n\n"
            f"**Action required:** {f.get('action_required', '—')}"
        )
        if sev == "HIGH":
            st.error(msg)
        elif sev == "MEDIUM":
            st.warning(msg)
        else:
            st.info(msg)
 
# ── Tab 4: Documentation Required (reads "required_documentation" — FLAT LIST) ──
with tab4:
    docs = r.get("required_documentation", [])
    if not docs:
        st.info(
            "No documentation requirements found under the 'required_documentation' key. "
            "Check the Raw JSON tab to see the actual structure returned."
        )
    else:
        for d in docs:
            st.markdown(f"- {d}")
    st.markdown("---")
    st.markdown("**Section 15 — Reputation / Credit Bureau Check (edit before submitting):**")
    st.text_area(
        "Override:",
        value=r.get("credit_memo_narrative", ""),
        height=160,
        label_visibility="collapsed",
    )
 
with tab5:
    st.json(r)
 
if st.button("Start New Screening"):
    for k in ["kyc_result", "_directors", "kyc_stored"]:
        st.session_state.pop(k, None)
    st.session_state.directors = [{"id": 1}]
    st.rerun()
 
