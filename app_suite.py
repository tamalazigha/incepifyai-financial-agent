import streamlit as st

st.set_page_config(
    page_title="IncepifyAI — Credit Underwriting Suite",
    page_icon="🏦",
    layout="wide",
)

st.markdown(
    """<div style='padding:20px 24px;background:linear-gradient(
    135deg,#161E41,#1D63EB);border-radius:10px;margin-bottom:24px'>
    <h1 style='color:white;margin:0;font-size:26px'>
        IncepifyAI Credit Underwriting Suite</h1>
    <p style='color:#B5D4F4;margin:6px 0 0'>
        8 agents · 16 underwriting criteria · CBN-compliant</p>
    </div>""",
    unsafe_allow_html=True,
)

applicant = st.session_state.get("applicant_name", "No application in progress")
st.markdown(f"### Current Application: **{applicant}**")
st.markdown(
    "Use the sidebar to navigate to each agent. "
    "Results appear below as each agent is completed."
)
st.markdown("---")

# ── Agent completion status ──────────────────────────────────────────────────
agents_status = [
    ("1", "Financial Analysis",     "financial_result",  "📊"),
    ("2", "Collateral & Security",  "collateral_result", "🛡️"),
    ("3", "Reputation & KYC",       "kyc_stored",        "🔍"),
    ("4", "Relationship & Revenue", "revenue_result",    "💰"),
]

status_cols = st.columns(4)
for i, (num, name, key, icon) in enumerate(agents_status):
    done = key in st.session_state
    status_cols[i].metric(
        label=f"{icon} Agent {num}: {name}",
        value="Complete" if done else "Pending",
        delta="✓ Done" if done else "Not yet run",
        delta_color="normal" if done else "off",
    )

st.markdown("---")

# ── Summary results when agents are complete ─────────────────────────────────
has_any = any(k in st.session_state for _, _, k, _ in agents_status)

if not has_any:
    st.info("Navigate to Agent 1 — Financial Analysis in the sidebar to begin.")
    st.stop()

# Financial summary
if "financial_result" in st.session_state:
    fr  = st.session_state["financial_result"]
    rec = fr.get("credit_recommendation", {})
    with st.expander("📊 Agent 1 — Financial Analysis Summary", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Assessment", rec.get("overall_assessment", "—"))
        c2.metric(
            "DSCR (Yr 1 Base)",
            fr.get("sensitivity_analysis", {})
              .get("base_case", {})
              .get("dscr_yr1", "—"),
        )
        c3.metric("Primary Repayment", rec.get("primary_repayment_viability", "—"))
        st.caption(rec.get("narrative_summary", ""))

# Collateral summary
if "collateral_result" in st.session_state:
    cr = st.session_state["collateral_result"]
    cs = cr.get("coverage_summary", {})
    with st.expander("🛡️ Agent 2 — Collateral & Security Summary", expanded=True):
        c1, c2, c3 = st.columns(3)
        status = cs.get("coverage_status", "—")
        c1.metric("Coverage Status", status)
        c2.metric("Coverage Ratio", f"{cs.get('coverage_ratio_pct', 0):.1f}%")
        surplus = cs.get("shortfall_or_surplus_000", 0)
        label   = "Surplus" if surplus >= 0 else "Shortfall"
        c3.metric(label, f"NGN {abs(surplus):,.0f}k")
        pdc = cr.get("pre_disbursement_conditions", [])
        if pdc:
            st.warning("Pre-disbursement conditions: " + " · ".join(pdc))

# KYC summary
if "kyc_stored" in st.session_state:
    kr  = st.session_state["kyc_stored"]
    agg = kr.get("aggregate_assessment", {})
    with st.expander("🔍 Agent 3 — Reputation & KYC Summary", expanded=True):
        c1, c2, c3 = st.columns(3)
        rating = agg.get("overall_kyc_risk_rating", "—")
        c1.metric("KYC Risk Rating", rating)
        c2.metric("Due Diligence Tier", agg.get("due_diligence_tier", "—"))
        c3.metric(
            "SM Approval Required",
            "YES ⚠️" if agg.get("senior_management_approval_required") else "No",
        )
        if agg.get("nfiu_str_required"):
            st.error("NFIU STR required — report to NFIU immediately.")
        st.caption(kr.get("credit_memo_narrative", ""))

# Revenue summary
if "revenue_result" in st.session_state:
    rr = st.session_state["revenue_result"]
    rs = rr.get("relationship_score", {})
    ra = rr.get("revenue_analysis",   {})
    with st.expander("💰 Agent 4 — Relationship & Revenue Summary", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Relationship Tier",  rs.get("tier", "—"))
        c2.metric("Relationship Score", f"{rs.get('score', '—')}/10")
        c3.metric("Relationship ROA",   f"{ra.get('roa_pct', 0):.2f}%")
        st.caption(rr.get("credit_memo_narrative", ""))

# ── Overall credit recommendation (when all 4 complete) ──────────────────────
all_done = all(k in st.session_state for _, _, k, _ in agents_status)

if all_done:
    st.markdown("---")
    st.markdown("### Overall Credit Recommendation")

    # FIX: wrap each multi-line boolean in outer parentheses
    # so Python knows the expression continues to the next line.
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

    all_green = fin_ok and coll_ok and kyc_ok and roa_ok

    if all_green:
        st.success(
            "✅  All four agents PASS.  "
            "Credit application may proceed to the approval committee."
        )
    else:
        fails = []
        if not fin_ok:
            fails.append("Financial analysis: MARGINAL or UNSATISFACTORY")
        if not coll_ok:
            fails.append("Collateral: SHORTFALL — additional security needed")
        if not kyc_ok:
            fails.append("KYC: DECLINE risk rating — compliance review required")
        if not roa_ok:
            fails.append("Revenue: Sub-economic ROA — exception needed")
        st.error("One or more agents require attention before approval:")
        for f in fails:
            st.error(f"  •  {f}")

# ── Clear all results ─────────────────────────────────────────────────────────
st.markdown("---")
if st.button("🗑️  Clear All Results — Start New Application"):
    keys_to_clear = [
        "financial_result", "collateral_result", "kyc_stored",
        "revenue_result",   "applicant_name",
        "result",           "company",          # Agent 1 local keys
        "coll_result",                           # Agent 2 local key
        "kyc_result",                            # Agent 3 local key
        "rev_result",       "_revenue_items",    # Agent 4 local keys
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
    st.rerun()