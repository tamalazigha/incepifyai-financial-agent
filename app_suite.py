import streamlit as st
 
st.set_page_config(
    page_title="IncepifyAI — Credit Underwriting Suite",
    page_icon="🏦",
    layout="wide",
)
 
st.markdown(
    """<div style='padding:20px 24px;background:linear-gradient(
    135deg,#161E41 0%,#8B6914 100%);border-radius:10px;margin-bottom:24px'>
    <span style='font-size:26px;font-weight:700;color:white'>Incepify</span>
    <span style='font-size:26px;font-weight:700;color:#FEF6DC'>AI</span>
    <span style='font-size:14px;color:#FEF6DC;margin-left:14px'>
        Credit Underwriting Suite · 8 agents · CBN-compliant · COMPLETE SYSTEM</span>
    </div>""",
    unsafe_allow_html=True,
)
 
applicant = st.session_state.get("applicant_name","No application in progress")
st.markdown(f"### Current Application: **{applicant}**")
st.caption("Run agents in order 1 → 8. Agent 8 generates the downloadable credit memo.")
st.markdown("---")
 
# ── Agent tracker ─────────────────────────────────────────────────────────────
AGENTS = [
    ("1","Financial Analysis",     "financial_result",      "📊"),
    ("2","Collateral & Security",  "collateral_result",     "🛡️"),
    ("3","Reputation & KYC",       "kyc_stored",            "🔍"),
    ("4","Relationship & Revenue", "revenue_result",        "💰"),
    ("5","Industry Intelligence",  "industry_result",       "🔭"),
    ("6","Management Assessment",  "management_result",     "👔"),
    ("7","Risk Assessment",        "risk_assessment_result","⚠️"),
    ("8","Report & Routing",       "report_complete",       "📋"),
]
 
row1 = st.columns(3)
for i,(num,name,key,icon) in enumerate(AGENTS[:3]):
    done = key in st.session_state
    row1[i].metric(label=f"{icon} Agent {num}: {name}",
        value="Complete ✓" if done else "Pending",
        delta=name, delta_color="normal" if done else "off")
 
row2 = st.columns(3)
for i,(num,name,key,icon) in enumerate(AGENTS[3:6]):
    done = key in st.session_state
    row2[i].metric(label=f"{icon} Agent {num}: {name}",
        value="Complete ✓" if done else "Pending",
        delta=name, delta_color="normal" if done else "off")
 
done7 = "risk_assessment_result" in st.session_state
st.metric(label="⚠️ Agent 7: Risk Assessment",
    value="Complete ✓" if done7 else "Pending — run after Agents 1–6",
    delta="Risk matrix · Credit rating · Covenants · Section 17",
    delta_color="normal" if done7 else "off")
 
done8 = "report_complete" in st.session_state
st.metric(label="📋 Agent 8: Report & Routing — THE FINAL AGENT",
    value="✅  CREDIT MEMO READY" if done8 else "Pending — run after Agent 7",
    delta="16-section credit memo · Routing decision · HTML download",
    delta_color="normal" if done8 else "off")
 
st.markdown("---")
has_any = any(k in st.session_state for _,_,k,_ in AGENTS)
if not has_any:
    st.info("👈  Navigate to Agent 1 — Financial Analysis in the sidebar to begin.")
    st.stop()
 
# ── Download button (when Agent 8 complete) ──────────────────────────────────
if done8:
    from report_agent import generate_html_memo
    rr8    = st.session_state["report_complete"]
    meta8  = rr8.get("memo_metadata",{})
    html8  = generate_html_memo(rr8)
    bname  = meta8.get("borrower_name","Borrower").replace(" ","_")
    ref8   = meta8.get("memo_reference","memo").replace("/","_")
    rating8 = meta8.get("overall_risk_rating","—")
    rec8    = meta8.get("credit_recommendation","—")
    route8  = meta8.get("routing_authority_label","—")
    st.success(f"✅  CREDIT MEMO COMPLETE  ·  {rating8}  ·  {rec8}  ·  → {route8}")
    st.download_button(
        label="📄  Download Complete Credit Memo (HTML — print to PDF in browser)",
        data=html8,
        file_name=f"CreditMemo_{bname}_{ref8}.html",
        mime="text/html",
        type="primary",
        use_container_width=True,
    )
    st.markdown("---")
 
# ── Agent 1–7 summaries ───────────────────────────────────────────────────────
if "financial_result" in st.session_state:
    fr  = st.session_state["financial_result"]
    rec = fr.get("credit_recommendation",{})
    with st.expander(f"📊 Agent 1 — Financial Analysis  |  {rec.get('overall_assessment','—')}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("Assessment",rec.get("overall_assessment","—"))
        c2.metric("Primary Repayment",rec.get("primary_repayment_viability","—"))
        st.caption(rec.get("narrative_summary",""))
 
if "collateral_result" in st.session_state:
    cr = st.session_state["collateral_result"]
    cs = cr.get("coverage_summary",{})
    with st.expander(f"🛡️ Agent 2 — Collateral  |  {cs.get('coverage_status','—')}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("Coverage Ratio",f"{cs.get('coverage_ratio_pct',0):.1f}%")
        c2.metric("Coverage Status",cs.get("coverage_status","—"))
 
if "kyc_stored" in st.session_state:
    kr  = st.session_state["kyc_stored"]
    agg = kr.get("aggregate_assessment",{})
    with st.expander(f"🔍 Agent 3 — KYC  |  {agg.get('overall_kyc_risk_rating','—')}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("KYC Rating",agg.get("overall_kyc_risk_rating","—"))
        c2.metric("Due Diligence",agg.get("due_diligence_tier","—"))
 
if "revenue_result" in st.session_state:
    rr = st.session_state["revenue_result"]
    rs = rr.get("relationship_score",{})
    ra = rr.get("revenue_analysis",{})
    with st.expander(f"💰 Agent 4 — Revenue  |  {rs.get('tier','—')}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("Tier",rs.get("tier","—"))
        c2.metric("ROA",f"{ra.get('roa_pct',0):.2f}%")
 
if "industry_result" in st.session_state:
    ir = st.session_state["industry_result"]
    ia = ir.get("industry_assessment",{})
    with st.expander(f"🔭 Agent 5 — Industry  |  {ia.get('outlook','—')}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("Outlook",ia.get("outlook","—"))
        c2.metric("Industry Risk",ia.get("industry_risk_rating","—"))
 
if "management_result" in st.session_state:
    mr = st.session_state["management_result"]
    ma = mr.get("management_assessment",{})
    with st.expander(f"👔 Agent 6 — Management  |  {ma.get('management_quality','—')}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("Quality",ma.get("management_quality","—"))
        c2.metric("Score",f"{ma.get('overall_management_score',0)}/10")
 
if "risk_assessment_result" in st.session_state:
    rr7 = st.session_state["risk_assessment_result"]
    rs7 = rr7.get("risk_summary",{})
    rat7 = rs7.get("overall_credit_risk_rating","—")
    with st.expander(f"⚠️ Agent 7 — Risk Assessment  |  {rat7}",expanded=False):
        c1,c2 = st.columns(2)
        c1.metric("Risk Rating",rat7)
        c2.metric("Recommendation",rs7.get("credit_recommendation","—"))
        st.caption(rs7.get("recommendation_rationale",""))
 
if done8:
    with st.expander("📋 Agent 8 — Report & Routing  |  CREDIT MEMO COMPLETE",expanded=True):
        meta8 = st.session_state["report_complete"].get("memo_metadata",{})
        c1,c2,c3 = st.columns(3)
        c1.metric("Risk Rating",   meta8.get("overall_risk_rating","—"))
        c2.metric("Recommendation",meta8.get("credit_recommendation","—"))
        c3.metric("Routed To",     meta8.get("routing_authority_label","—"))
        addl = meta8.get("additional_approvers",[])
        if addl: st.warning("Additional approvers: " + " · ".join(addl))
 
# ── Clear all ─────────────────────────────────────────────────────────────────
st.markdown("---")
if st.button("🗑️  Clear All Results — Start New Application"):
    clear_keys = [
        "financial_result","collateral_result","kyc_stored",
        "revenue_result","industry_result","management_result",
        "risk_assessment_result","report_complete","applicant_name",
        "result","company","coll_result","kyc_result","rev_result",
        "_revenue_items","ind_result","mgmt_result","_mgmt_directors",
        "risk_result","report_result",
    ]
    for k in clear_keys: st.session_state.pop(k,None)
    st.rerun()

