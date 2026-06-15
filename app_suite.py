import streamlit as st
 
st.set_page_config(
    page_title="IncepifyAI — Credit Underwriting Suite",
    page_icon="🏦",
    layout="wide",
)
 
st.markdown(
    """<div style='padding:20px 24px;background:linear-gradient(
    135deg,#161E41 0%,#185FA5 100%);border-radius:10px;margin-bottom:24px'>
    <span style='font-size:26px;font-weight:700;color:white'>Incepify</span>
    <span style='font-size:26px;font-weight:700;color:#7BC8F6'>AI</span>
    <span style='font-size:14px;color:#B5D4F4;margin-left:14px'>
        Credit Underwriting Suite · 7 agents · CBN-compliant</span>
    </div>""",
    unsafe_allow_html=True,
)
 
applicant = st.session_state.get("applicant_name","No application in progress")
st.markdown(f"### Current Application: **{applicant}**")
st.caption("Run agents in order 1 → 7. Agent 7 synthesises all prior outputs.")
st.markdown("---")
 
# ── Agent tracker — Agents 1-6 in 2 rows of 3, Agent 7 full-width ──────────
AGENTS = [
    ("1","Financial Analysis",    "financial_result",      "📊"),
    ("2","Collateral & Security", "collateral_result",     "🛡️"),
    ("3","Reputation & KYC",      "kyc_stored",            "🔍"),
    ("4","Relationship & Revenue","revenue_result",        "💰"),
    ("5","Industry Intelligence", "industry_result",       "🔭"),
    ("6","Management Assessment", "management_result",     "👔"),
    ("7","Risk Assessment",       "risk_assessment_result","⚠️"),
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
 
# Agent 7 — full width
done7 = "risk_assessment_result" in st.session_state
st.metric(label="⚠️ Agent 7: Risk Assessment (synthesis of all agents)",
    value="Complete ✓" if done7 else "Pending — run after Agents 1–6",
    delta="Risk matrix · Credit rating · Covenants · Section 17",
    delta_color="normal" if done7 else "off")
 
st.markdown("---")
has_any = any(k in st.session_state for _,_,k,_ in AGENTS)
if not has_any:
    st.info("👈  Navigate to Agent 1 — Financial Analysis in the sidebar to begin.")
    st.stop()
 
# ── Agent 1 summary ──────────────────────────────────────────────────────────
if "financial_result" in st.session_state:
    fr = st.session_state["financial_result"]
    rec = fr.get("credit_recommendation",{})
    a = rec.get("overall_assessment","—")
    with st.expander(f"📊 Agent 1 — Financial Analysis  |  {a}",expanded=False):
        c1,c2,c3 = st.columns(3)
        c1.metric("Overall Assessment",a)
        c2.metric("DSCR Yr 1",fr.get("sensitivity_analysis",{}).get("base_case",{}).get("dscr_yr1","—"))
        c3.metric("Primary Repayment",rec.get("primary_repayment_viability","—"))
        st.caption(rec.get("narrative_summary",""))
 
# ── Agent 2 summary ──────────────────────────────────────────────────────────
if "collateral_result" in st.session_state:
    cr = st.session_state["collateral_result"]
    cs = cr.get("coverage_summary",{})
    status = cs.get("coverage_status","—")
    with st.expander(f"🛡️ Agent 2 — Collateral & Security  |  {status}",expanded=False):
        c1,c2,c3 = st.columns(3)
        c1.metric("Coverage Status",status)
        c2.metric("Coverage Ratio",f"{cs.get('coverage_ratio_pct',0):.1f}%")
        surplus = cs.get("shortfall_or_surplus_000",0)
        c3.metric("Surplus/Shortfall",f"NGN {abs(surplus):,.0f}k")
        pdc = cr.get("pre_disbursement_conditions",[])
        if pdc: st.warning("Pre-disbursement: " + " · ".join(pdc[:2]))
 
# ── Agent 3 summary ──────────────────────────────────────────────────────────
if "kyc_stored" in st.session_state:
    kr = st.session_state["kyc_stored"]
    agg = kr.get("aggregate_assessment",{})
    rat = agg.get("overall_kyc_risk_rating","—")
    with st.expander(f"🔍 Agent 3 — KYC  |  {rat} · {agg.get('due_diligence_tier','—')}",expanded=False):
        c1,c2,c3 = st.columns(3)
        c1.metric("KYC Rating",rat)
        c2.metric("Due Diligence",agg.get("due_diligence_tier","—"))
        c3.metric("SM Approval","YES ⚠️" if agg.get("senior_management_approval_required") else "No")
 
# ── Agent 4 summary ──────────────────────────────────────────────────────────
if "revenue_result" in st.session_state:
    rr = st.session_state["revenue_result"]
    rs = rr.get("relationship_score",{})
    ra = rr.get("revenue_analysis",{})
    with st.expander(f"💰 Agent 4 — Revenue  |  {rs.get('tier','—')} · {ra.get('roa_pct',0):.2f}% ROA",expanded=False):
        c1,c2,c3 = st.columns(3)
        c1.metric("Tier",rs.get("tier","—"))
        c2.metric("Score",f"{rs.get('score','—')}/10")
        c3.metric("ROA",f"{ra.get('roa_pct',0):.2f}%")
 
# ── Agent 5 summary ──────────────────────────────────────────────────────────
if "industry_result" in st.session_state:
    ir = st.session_state["industry_result"]
    ia = ir.get("industry_assessment",{})
    with st.expander(f"🔭 Agent 5 — Industry  |  {ia.get('outlook','—')} · {ia.get('industry_risk_rating','—')}",expanded=False):
        c1,c2,c3 = st.columns(3)
        c1.metric("Sector",ir.get("industry_profile",{}).get("sector","—"))
        c2.metric("Outlook",ia.get("outlook","—"))
        c3.metric("Credit Implication",ia.get("credit_risk_implication","—"))
 
# ── Agent 6 summary ──────────────────────────────────────────────────────────
if "management_result" in st.session_state:
    mr = st.session_state["management_result"]
    ma = mr.get("management_assessment",{})
    mo = mr.get("management_overview",{})
    with st.expander(f"👔 Agent 6 — Management  |  {ma.get('management_quality','—')} · {ma.get('overall_management_score',0)}/10",expanded=False):
        c1,c2,c3 = st.columns(3)
        c1.metric("Quality",ma.get("management_quality","—"))
        c2.metric("Score",f"{ma.get('overall_management_score',0)}/10")
        c3.metric("Key Man Risk","YES ⚠️" if ma.get("key_man_risk_identified") else "No")
 
st.markdown("---")
 
# ── AGENT 7 OUTPUT — THE OVERALL RECOMMENDATION ──────────────────────────────
if "risk_assessment_result" in st.session_state:
    rr7 = st.session_state["risk_assessment_result"]
    rs7 = rr7.get("risk_summary",{})
    rating7  = rs7.get("overall_credit_risk_rating","—")
    rec7     = rs7.get("credit_recommendation","—")
    r7colors = {"PASS":"green","WATCH":"orange",
                "SUBSTANDARD":"red","DOUBTFUL":"red","DECLINE":"red"}
    rc7 = r7colors.get(rating7,"grey")
 
    st.markdown("### ⚠️ Agent 7 — Risk Assessment & Overall Credit Recommendation")
    st.markdown(f"## :{rc7}[**{rating7}**]  ·  {rec7}")
    st.markdown(f"> {rs7.get('recommendation_rationale','')}")
    st.markdown(f"> {rr7.get('credit_memo_narrative','')}")
 
    c1,c2,c3,c4 = st.columns(4)
    matrix = rr7.get("risk_matrix",[])
    high_risks = [m for m in matrix if m.get("risk_rating") in ("HIGH","VERY_HIGH")]
    c1.metric("Risk Dimensions Assessed",len(matrix))
    c2.metric("HIGH/VERY_HIGH Risks",len(high_risks))
    c3.metric("Conditions Precedent",len(rr7.get("conditions_precedent",[])))
    c4.metric("Financial Covenants",len(rr7.get("financial_covenants",[])))
 
    if rr7.get("conditions_precedent"):
        st.error("**PRE-DISBURSEMENT CONDITIONS (must be satisfied before drawdown):**")
        for cp in rr7["conditions_precedent"]:
            st.error(f"  •  {cp}")
 
else:
    agents_1_to_6 = ["financial_result","collateral_result","kyc_stored",
                      "revenue_result","industry_result","management_result"]
    ready = all(k in st.session_state for k in agents_1_to_6)
    if ready:
        st.success("✅  Agents 1–6 are all complete. Navigate to **Agent 7 — Risk Assessment** in the sidebar to generate the overall credit recommendation.")
    else:
        pending = [AGENTS[i][1] for i,(_,_,k,_) in enumerate(AGENTS[:6]) if k not in st.session_state]
        st.info(f"Complete these agents first: {', '.join(pending)}")
 
# ── Clear all ─────────────────────────────────────────────────────────────────
st.markdown("---")
if st.button("🗑️  Clear All Results — Start New Application"):
    clear_keys = [
        "financial_result","collateral_result","kyc_stored",
        "revenue_result","industry_result","management_result",
        "risk_assessment_result","applicant_name",
        "result","company","coll_result","kyc_result",
        "rev_result","_revenue_items","ind_result",
        "mgmt_result","_mgmt_directors","risk_result",
    ]
    for k in clear_keys: st.session_state.pop(k,None)
    st.rerun()
