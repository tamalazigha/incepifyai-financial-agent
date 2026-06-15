import streamlit as st
from kyc_agent import run_full_kyc, run_kyc_with_mock_apis, get_mock_kyc_result

st.set_page_config(
    page_title="IncepifyAI — Reputation & KYC",
    page_icon="🔍",
    layout="wide",
)

st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #993C1D;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Reputation & KYC Agent · Agent 3 of 8</span>
    </div>""",
    unsafe_allow_html=True,
)

# ── Session state: director list ──────────────────────────────
if "directors" not in st.session_state:
    st.session_state.directors = [{"id": 1}]

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Company Details")
    company_name = st.text_input(
        "Company / Obligor Name",
        placeholder="e.g. Sunrise Manufacturing Ltd",
    )
    rc_number = st.text_input(
        "CAC RC Number (optional)",
        placeholder="e.g. RC-482931",
    )
    facility_amount = st.number_input(
        "Facility Amount (NGN '000)",
        min_value=0, value=500000, step=10000,
    )
    company_type = st.selectbox(
        "Entity Type",
        ["Private Limited Company (Ltd)",
         "Public Limited Company (Plc)",
         "Sole Proprietorship",
         "Partnership",
         "NGO / Not-for-Profit",
         "Government Entity",
         "Other"],
    )
    industry_sector = st.selectbox(
        "Industry Sector",
        ["Agriculture", "Construction", "Education",
         "Financial Services", "Healthcare & Pharmaceuticals",
         "ICT & Technology", "Manufacturing", "Mining & Quarrying",
         "Oil & Gas", "Power & Energy", "Real Estate",
         "Retail & Trade", "Transport & Logistics", "Other"],
    )
    run_mode = st.radio(
        "Run Mode",
        ["Full mock (no API)",
         "APIs live + Claude mock",
         "Full live (APIs + Claude)"],
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
        disabled=not (company_name or run_mode == "Full mock (no API)"),
    )
    if "kyc_result" in st.session_state:
        meta = st.session_state["kyc_result"].get("_metadata", {})
        st.caption(f"Searches: {len(meta.get('searches_conducted', []))}")
        st.caption(f"Cost: ${meta.get('estimated_cost_usd', 0):.4f} USD")

# ── Director entry forms ───────────────────────────────────────
if "kyc_result" not in st.session_state:
    st.markdown("### Director & UBO Profiles")
    st.caption("Complete details for each director and ultimate beneficial owner.")
    directors_data = []
    for d in st.session_state.directors:
        did = d["id"]
        with st.expander(f"Director / UBO {did}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                d_name   = st.text_input(f"Full Name #{did}",
                    placeholder="e.g. Chidi Okonkwo", key=f"d_name_{did}")
                d_role   = st.text_input(f"Role / Position #{did}",
                    placeholder="e.g. Managing Director", key=f"d_role_{did}")
                d_dob    = st.text_input(f"Date of Birth #{did}",
                    placeholder="e.g. 15 March 1975", key=f"d_dob_{did}")
                d_nat    = st.selectbox(f"Nationality #{did}",
                    ["Nigerian", "Ghanaian", "Kenyan", "British",
                     "American", "South African", "Other"],
                    key=f"d_nat_{did}")
                d_bvn    = st.text_input(f"BVN (optional) #{did}",
                    key=f"d_bvn_{did}")
            with c2:
                d_share  = st.number_input(f"Shareholding % #{did}",
                    min_value=0.0, max_value=100.0, value=0.0,
                    key=f"d_share_{did}")
                d_pep    = st.checkbox(f"PEP or PEP-connected #{did}",
                    key=f"d_pep_{did}",
                    help="Political exposed person or immediate family member")
                d_pep_d  = st.text_input(f"PEP connection details #{did}",
                    placeholder="e.g. Sibling is serving State Commissioner",
                    key=f"d_pep_d_{did}") if d_pep else ""
                d_country = st.multiselect(f"Countries of operation #{did}",
                    ["Nigeria", "Ghana", "Liberia", "Sierra Leone",
                     "United Kingdom", "United States", "UAE", "Other"],
                    default=["Nigeria"], key=f"d_country_{did}")
                d_notes  = st.text_area(f"Additional context #{did}",
                    placeholder="LinkedIn, other business interests, etc.",
                    height=80, key=f"d_notes_{did}")
            if len(st.session_state.directors) > 1:
                if st.button(f"Remove #{did}", key=f"rm_{did}"):
                    st.session_state.directors = [
                        x for x in st.session_state.directors
                        if x["id"] != did
                    ]
                    st.rerun()
            directors_data.append({
                "name":                    d_name,
                "role":                    d_role,
                "date_of_birth":           d_dob or None,
                "nationality":             d_nat,
                "bvn":                     d_bvn or None,
                "shareholding_pct":        d_share,
                "is_pep":                  d_pep,
                "pep_details":             d_pep_d or None,
                "countries_of_operation":  d_country,
                "additional_notes":        d_notes or None,
            })
    st.session_state["_directors_data"] = directors_data

# ── Run ───────────────────────────────────────────────────────
if run_btn:
    payload = {
        "company_name":         company_name,
        "rc_number":            rc_number or None,
        "facility_amount_000":  facility_amount,
        "entity_type":          company_type,
        "industry_sector":      industry_sector,
        "directors":            st.session_state.get("_directors_data", []),
    }

    if run_mode == "Full mock (no API)":
        st.session_state["kyc_result"] = get_mock_kyc_result()
    elif run_mode == "APIs live + Claude mock":
        with st.spinner("Running sanctions API screening (no Claude)..."):
            st.session_state["kyc_result"] = run_kyc_with_mock_apis(payload)
    else:
        with st.spinner("Running full KYC screening — web search in progress..."):
            st.session_state["kyc_result"] = run_full_kyc(payload)

    # ── Shared suite key ──────────────────────────────────────
    st.session_state["kyc_stored"] = st.session_state["kyc_result"]
    st.rerun()

# ── Nothing run yet ───────────────────────────────────────────
if "kyc_result" not in st.session_state:
    c1, c2, c3 = st.columns(3)
    c1.metric("Sanctions Databases", "OFAC + OpenSanctions", "auto-screened")
    c2.metric("Web Research", "PEP / adverse media", "Claude searches")
    c3.metric("Output", "Section 6 KYC", "Credit memo narrative")
    st.info("Enter director details above and click Run KYC Screening.")
    st.stop()

# ── Display results ───────────────────────────────────────────
r   = st.session_state["kyc_result"]
agg = r.get("aggregate_assessment", {})
rating = agg.get("overall_kyc_risk_rating", "—")
tier   = agg.get("due_diligence_tier",       "—")

r_colors = {"LOW": "green", "MEDIUM": "orange",
            "HIGH": "red",  "CRITICAL": "red"}
rc = r_colors.get(rating, "grey")

st.markdown(f"## KYC Risk: :{rc}[**{rating}**]  ·  Due Diligence Tier: **{tier}**")
if agg.get("nfiu_str_required"):
    st.error("🚨 NFIU STR REQUIRED — file Suspicious Transaction Report immediately.")
if agg.get("senior_management_approval_required"):
    st.warning("⚠️  Senior Management approval required before any disbursement.")
st.markdown(f"> {r.get('credit_memo_narrative', '')}")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Company Overview", "Director Profiles",
    "Risk Flags", "Documents Required",
    "Memo Draft", "Raw JSON"
])

with tab1:
    co = r.get("company_overview", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Company Risk Rating", co.get("company_risk_rating", "—"))
    c2.metric("PEP-Connected?",
              "YES ⚠️" if co.get("pep_connected_entity") else "No")
    c3.metric("Adverse Media",
              co.get("adverse_media_summary", "None found"))

with tab2:
    for dp in r.get("director_profiles", []):
        dr = dp.get("overall_risk_rating", "LOW")
        dc = r_colors.get(dr, "grey")
        with st.expander(
            f"{dp.get('name', '—')} ({dp.get('role', '—')}) — :{dc}[{dr}]",
            expanded=True,
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Sanctions Match",
                      "YES 🚨" if dp.get("sanctions_match") else "Clear")
            c2.metric("PEP Status",
                      "YES ⚠️" if dp.get("is_pep_confirmed") else "No")
            c3.metric("Adverse Media", dp.get("adverse_media", "None found"))
            st.caption(dp.get("web_search_findings", ""))

with tab3:
    flags = r.get("risk_flags", [])
    if not flags:
        st.success("No risk flags identified.")
    for f in flags:
        sev = f.get("severity", "LOW")
        msg = (
            f"**{f.get('flag', '')}** — {f.get('detail', '')}\n\n"
            f"**Action:** {f.get('action_required', '—')}"
        )
        if sev in ("CRITICAL", "HIGH"): st.error(msg)
        elif sev == "MEDIUM":           st.warning(msg)
        else:                           st.info(msg)

with tab4:
    docs = r.get("documents_required", {})
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Company Documents**")
        for d in docs.get("company_documents", []):
            st.markdown(f"- {d}")
    with c2:
        st.markdown("**Director Documents**")
        for d in docs.get("director_documents", []):
            st.markdown(f"- {d}")
    st.markdown("**Enhanced Due Diligence**")
    for d in docs.get("edd_requirements", []):
        st.markdown(f"- {d}")

with tab5:
    st.markdown("**Section 6 — Reputation & KYC (edit before submitting):**")
    st.text_area("",
                 value=r.get("credit_memo_narrative", ""),
                 height=180,
                 label_visibility="collapsed")

with tab6:
    st.json(r)

if st.button("Start New Screening"):
    for k in ["kyc_result", "_directors_data", "kyc_stored"]:
        st.session_state.pop(k, None)
    st.session_state.directors = [{"id": 1}]
    st.rerun()


