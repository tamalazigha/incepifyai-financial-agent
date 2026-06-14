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
        Credit Underwriting Suite · 5 agents · CBN-compliant</span>
    </div>""",
    unsafe_allow_html=True,
)
 
applicant = st.session_state.get("applicant_name", "No application in progress")
st.markdown(f"### Current Application: **{applicant}**")
st.caption("Use the sidebar to navigate to each agent. Run them in order 1 → 5.")
st.markdown("---")
 
# ── Agent completion tracker ─────────────────────────────────────────────────
AGENTS = [
    ("1", "Financial Analysis",     "financial_result",  "📊"),
    ("2", "Collateral & Security",  "collateral_result", "🛡️"),
    ("3", "Reputation & KYC",       "kyc_stored",        "🔍"),
    ("4", "Relationship & Revenue", "revenue_result",    "💰"),
    ("5", "Industry Intelligence",  "industry_result",   "🔭"),
]
 
cols = st.columns(5)
for i, (num, name, key, icon) in enumerate(AGENTS):
    done = key in st.session_state
    cols[i].metric(
        label=f"{icon} Agent {num}: {name}",
        value="Complete ✓" if done else "Pending",
        delta=name,
        delta_color="normal" if done else "off",
    )
 
st.markdown("---")
has_any = any(k in st.session_state for _, _, k, _ in AGENTS)
if not has_any:
    st.info("👈  Navigate to Agent 1 — Financial Analysis in the sidebar to begin.")
    st.stop()
 
# ── Agent 1: Financial Analysis ─────────────────────────────────────────────
if "financial_result" in st.session_state:
    fr  = st.session_state["financial_result"]
    rec = fr.get("credit_recommendation", {})
    assessment = rec.get("overall_assessment", "—")
    with st.expander(f"📊 Agent 1 — Financial Analysis  |  {assessment}", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Assessment", assessment)
        sens = fr.get("sensitivity_analysis", {}).get("base_case", {})
        c2.metric("DSCR Year 1 (base)", sens.get("dscr_yr1", "—"))
        c3.metric("Primary Repayment", rec.get("primary_repayment_viability", "—"))
        st.caption(rec.get("narrative_summary", ""))
 
# ── Agent 2: Collateral ──────────────────────────────────────────────────────
if "collateral_result" in st.session_state:
    cr = st.session_state["collateral_result"]
    cs = cr.get("coverage_summary", {})
    status = cs.get("coverage_status", "—")
    with st.expander(f"🛡️ Agent 2 — Collateral & Security  |  {status}", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Coverage Status", status)
        c2.metric("Coverage Ratio", f"{cs.get('coverage_ratio_pct', 0):.1f}%")
        surplus = cs.get("shortfall_or_surplus_000", 0)
        c3.metric("Surplus / Shortfall", f"NGN {abs(surplus):,.0f}k")
        pdc = cr.get("pre_disbursement_conditions", [])
        if pdc:
            st.warning("Pre-disbursement: " + " · ".join(pdc))
 
# ── Agent 3: KYC ────────────────────────────────────────────────────────────
if "kyc_stored" in st.session_state:
    kr  = st.session_state["kyc_stored"]
    agg = kr.get("aggregate_assessment", {})
    rating = agg.get("overall_kyc_risk_rating", "—")
    tier   = agg.get("due_diligence_tier", "—")
    with st.expander(f"🔍 Agent 3 — Reputation & KYC  |  {rating} · {tier}", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("KYC Risk Rating",    rating)
        c2.metric("Due Diligence Tier", tier)
        c3.metric("SM Approval",
            "YES ⚠️" if agg.get("senior_management_approval_required") else "No")
        if agg.get("nfiu_str_required"):
            st.error("NFIU STR required — report immediately.")
        st.caption(kr.get("credit_memo_narrative", ""))
 
# ── Agent 4: Revenue ────────────────────────────────────────────────────────
if "revenue_result" in st.session_state:
    rr = st.session_state["revenue_result"]
    rs = rr.get("relationship_score", {})
    ra = rr.get("revenue_analysis",   {})
    tier_r = rs.get("tier", "—")
    with st.expander(f"💰 Agent 4 — Relationship & Revenue  |  {tier_r}", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Relationship Tier",  tier_r)
        c2.metric("Score",              f"{rs.get('score','—')}/10")
        c3.metric("Relationship ROA",   f"{ra.get('roa_pct', 0):.2f}%")
        st.caption(rr.get("credit_memo_narrative", ""))
 
# ── Agent 5: Industry Intelligence ──────────────────────────────────────────
if "industry_result" in st.session_state:
    ir  = st.session_state["industry_result"]
    ia  = ir.get("industry_assessment", {})
    ip2 = ir.get("industry_profile",    {})
    md  = ir.get("market_data",          {})
    outlook2 = ia.get("outlook", "—")
    rating2  = ia.get("industry_risk_rating", "—")
    impl2    = ia.get("credit_risk_implication", "—")
    with st.expander(
        f"🔭 Agent 5 — Industry Intelligence  |  {outlook2} · {rating2}",
        expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sector", ip2.get("sector", "—"))
        c2.metric("Industry Outlook", outlook2)
        c3.metric("Industry Risk",    rating2)
        c4.metric("Credit Implication", impl2)
        cagr = md.get("cagr_projected_5yr_pct")
        if cagr is not None:
            st.caption(f"Market projected CAGR: {cagr:.1f}% p.a.  ·  {ia.get('outlook_commentary','')}")
        st.caption(ir.get("credit_memo_narrative", ""))
 
# ── Overall recommendation (when all 5 complete) ─────────────────────────────
all_done = all(k in st.session_state for _, _, k, _ in AGENTS)
if all_done:
    st.markdown("---")
    st.markdown("### Overall Credit Recommendation")
 
    fin_ok = (
        st.session_state["financial_result"]
        .get("credit_recommendation", {})
        .get("overall_assessment", "")
        in ("STRONG", "SATISFACTORY")
    )
    coll_ok = (
        st.session_state["collateral_result"]
        .get("coverage_summary", {})
        .get("coverage_status", "")
        == "ADEQUATE"
    )
    kyc_ok = (
        st.session_state["kyc_stored"]
        .get("aggregate_assessment", {})
        .get("due_diligence_tier", "")
        not in ("DECLINE", "")
    )
    roa_ok = (
        st.session_state["revenue_result"]
        .get("revenue_analysis", {})
        .get("roa_pct", 0)
        >= 0.5
    )
    ind_ok = (
        st.session_state["industry_result"]
        .get("industry_assessment", {})
        .get("credit_risk_implication", "")
        != "CONSTRAINS"
    )
 
    fails = []
    if not fin_ok:  fails.append("Financial: MARGINAL or UNSATISFACTORY")
    if not coll_ok: fails.append("Collateral: SHORTFALL — additional security needed")
    if not kyc_ok:  fails.append("KYC: DECLINE risk — compliance review required")
    if not roa_ok:  fails.append("Revenue: ROA below 0.5% hurdle — exception required")
    if not ind_ok:  fails.append("Industry: outlook CONSTRAINS the credit — sector headwinds noted")
 
    if not fails:
        st.success(
            "✅  All five agents PASS.  "
            "This application may proceed to the approval committee."
        )
    else:
        st.error("One or more agents require resolution before approval:")
        for f in fails:
            st.error(f"  •  {f}")
 
# ── Clear all results ─────────────────────────────────────────────────────────
st.markdown("---")
if st.button("🗑️  Clear All Results — Start New Application"):
    clear_keys = [
        "financial_result", "collateral_result", "kyc_stored",
        "revenue_result",   "industry_result",   "applicant_name",
        "result", "company", "coll_result", "kyc_result",
        "rev_result", "_revenue_items", "ind_result",
    ]
    for k in clear_keys:
        st.session_state.pop(k, None)
    st.rerun()
