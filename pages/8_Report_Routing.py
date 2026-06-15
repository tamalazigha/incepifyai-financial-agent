import streamlit as st
from report_agent import (
    generate_report, get_mock_report_result,
    get_all_mock_inputs, generate_html_memo
)
 
st.set_page_config(page_title="IncepifyAI — Report & Routing Agent",
                   page_icon="📋", layout="wide")
 
st.markdown(
    """<div style='padding:16px 20px;background:linear-gradient(
    135deg,#161E41 0%,#8B6914 100%);border-radius:8px;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:white'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#FEF6DC'>AI</span>
    <span style='font-size:13px;color:#FEF6DC;margin-left:12px'>
        Report & Routing Agent · Agent 8 of 8 · THE FINAL AGENT</span>
    </div>""", unsafe_allow_html=True)
 
REQUIRED_KEYS = {
    "financial_result":       "Agent 1 — Financial Analysis",
    "collateral_result":      "Agent 2 — Collateral & Security",
    "kyc_stored":             "Agent 3 — Reputation & KYC",
    "revenue_result":         "Agent 4 — Relationship & Revenue",
    "industry_result":        "Agent 5 — Industry Intelligence",
    "management_result":      "Agent 6 — Management Assessment",
    "risk_assessment_result": "Agent 7 — Risk Assessment",
}
available = {k: k in st.session_state for k in REQUIRED_KEYS}
all_available = all(available.values())
 
with st.sidebar:
    st.markdown("### Prior Agent Status")
    for key, name in REQUIRED_KEYS.items():
        icon = "✅" if available[key] else "⏳"
        st.markdown(f"{icon} {name}")
    all_ok = all(available.values())
    st.markdown("---")
    use_mock = st.checkbox("Use mock data (no API cost)",
        value=not all_ok)
    run_btn = st.button("Generate Credit Memo", type="primary",
        use_container_width=True)
    if "report_result" in st.session_state:
        meta = st.session_state["report_result"].get("_metadata",{})
        cost = meta.get("estimated_cost_usd",0)
        toks = meta.get("input_tokens",0)+meta.get("output_tokens",0)
        st.caption(f"Tokens: {toks:,}")
        st.caption(f"Cost: ${cost:.4f} USD")
 
if run_btn:
    if use_mock:
        st.session_state["report_result"] = get_mock_report_result()
    else:
        if not all_ok:
            st.error("Not all prior agents complete. Enable mock mode or run Agents 1–7 first.")
            st.stop()
        all_outputs = {k: st.session_state[k] for k in REQUIRED_KEYS}
        with st.spinner("Assembling complete credit approval memo — please wait (30-60s)..."):
            st.session_state["report_result"] = generate_report(all_outputs)
    st.session_state["report_complete"] = st.session_state["report_result"]
    st.rerun()

if "report_result" not in st.session_state:
    c1, c2, c3 = st.columns(3)
    c1.metric("Sections", "16", "Complete credit memo")
    c2.metric("Routing tiers", "5", "Business → Board")
    c3.metric("Output", "HTML download", "Print-ready memo")
    st.info("Click Generate Credit Memo in the sidebar.")
    st.stop()
 
r    = st.session_state["report_result"]
meta = r.get("memo_metadata", {})
secs = r.get("sections",      {})
 
rating  = meta.get("overall_risk_rating",     "—")
rec     = meta.get("credit_recommendation",   "—")
routing = meta.get("routing_authority_label", "—")
addl    = meta.get("additional_approvers",    [])
 
r_colors = {"PASS":"green","WATCH":"orange","SUBSTANDARD":"red",
            "DOUBTFUL":"red","DECLINE":"red"}
rc = r_colors.get(rating,"grey")
 
st.markdown(f"## :{rc}[{rating}]  ·  {rec}  ·  → **{routing}**")
if addl:
    st.warning("Additional approvers required: " + " · ".join(addl))
st.markdown(f"> {secs.get('s01_executive_summary','')}")
 
# Download button
html_memo = generate_html_memo(r)
borrower  = meta.get("borrower_name","Borrower").replace(" ","_")
ref       = meta.get("memo_reference","memo").replace("/","_")
st.download_button(
    label="📄  Download Credit Memo (HTML — print to PDF in browser)",
    data=html_memo,
    file_name=f"CreditMemo_{borrower}_{ref}.html",
    mime="text/html",
    type="primary",
)
st.markdown("---")
 
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "Sections 1–4","Sections 5–8","Sections 9–11",
    "Conditions & Covenants","Routing & Recommendation","Raw JSON",
])
 
with tab1:
    for num,key,title in [
        ("01","s01_executive_summary","Executive Summary"),
        ("02","s02_obligor_profile","Obligor Profile"),
        ("03","s03_purpose_of_credit","Purpose of Credit"),
        ("04","s04_facility_structure","Facility Structure"),
    ]:
        with st.expander(f"Section {num} — {title}", expanded=num=="01"):
            st.markdown(secs.get(key,"Not generated."))
 
with tab2:
    for num,key,title in [
        ("05","s05_financial_analysis","Financial Analysis"),
        ("06","s06_collateral_security","Collateral & Security"),
        ("07","s07_kyc_compliance","KYC & AML Compliance"),
        ("08","s08_relationship_revenue","Relationship & Revenue"),
    ]:
        with st.expander(f"Section {num} — {title}", expanded=True):
            st.markdown(secs.get(key,"Not generated."))
 
with tab3:
    for num,key,title in [
        ("09","s09_industry_analysis","Industry Analysis"),
        ("10","s10_management_assessment","Management Assessment"),
        ("11","s11_risk_assessment","Risk Assessment & Mitigants"),
    ]:
        with st.expander(f"Section {num} — {title}", expanded=True):
            st.markdown(secs.get(key,"Not generated."))
 
with tab4:
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Section 12 — Conditions Precedent**")
        for i,cp in enumerate(secs.get("s12_conditions_precedent",[]),1):
            st.markdown(f"{i}. {cp}")
        st.markdown("**Section 14 — Monitoring & Reporting**")
        for i,m in enumerate(secs.get("s14_monitoring_reporting",[]),1):
            st.markdown(f"{i}. {m}")
    with c2:
        st.markdown("**Section 13 — Financial Covenants**")
        for i,cov in enumerate(secs.get("s13_financial_covenants",[]),1):
            st.markdown(f"{i}. {cov}")
 
with tab5:
    st.markdown("**Section 15 — Routing & Approval Authority**")
    st.info(secs.get("s15_routing_authority","—"))
    st.markdown("**Section 16 — Overall Recommendation**")
    rec_text = secs.get("s16_recommendation","")
    if "APPROVE" in rec and "CONDITION" not in rec:
        st.success(rec_text)
    elif "CONDITION" in rec:
        st.warning(rec_text)
    else:
        st.error(rec_text)
 
with tab6:
    st.json(r)
 
if st.button("Reset — Generate New Memo"):
    st.session_state.pop("report_result", None)
    st.rerun()
