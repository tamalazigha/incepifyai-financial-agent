import streamlit as st
import pandas as pd
from revenue_agent import analyze_relationship, get_mock_revenue_result

st.set_page_config(
    page_title="IncepifyAI — Relationship & Revenue",
    page_icon="💰",
    layout="wide",
)

st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #3B6D11;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Relationship & Revenue Agent · Agent 4 of 8</span>
    </div>""",
    unsafe_allow_html=True,
)

REVENUE_CATEGORIES = [
    ("loans_and_advances",    "Loans & Advances Income"),
    ("deposits_and_liabilities", "Deposits & Liabilities Income"),
    ("trade_finance",         "Trade Finance Income"),
    ("fx_transactions",       "FX / Treasury Income"),
    ("fees_and_commissions",  "Fees & Commissions"),
]

PERIODS = ["Prior Year (PY)", "Current Year (CY)", "YTD Actual"]

# ── Session state: revenue table ──────────────────────────────
if "_revenue_items" not in st.session_state:
    st.session_state["_revenue_items"] = {
        cat: {"py": 0.0, "cy": 0.0, "ytd": 0.0}
        for cat, _ in REVENUE_CATEGORIES
    }

with st.sidebar:
    st.markdown("### Entity Details")
    company_name     = st.text_input(
        "Company / Obligor Name",
        placeholder="e.g. Sunrise Manufacturing Ltd",
    )
    relationship_yrs = st.number_input(
        "Years as Bank Customer", min_value=0, max_value=50, value=5,
    )
    account_officer  = st.text_input(
        "Account Officer", placeholder="e.g. Tunde Adeyemi",
    )
    branch           = st.text_input(
        "Branch / Business Unit", placeholder="e.g. Victoria Island Corporate",
    )

    st.markdown("### Facility Context")
    facility_amount  = st.number_input(
        "Facility Amount (NGN '000)", min_value=0, value=500000, step=10000,
    )
    facility_type    = st.selectbox(
        "Facility Type",
        ["Term Loan", "Overdraft", "Trade Finance (LC/Bond)",
         "Revolving Credit Facility", "Other"],
    )
    existing_exposure = st.number_input(
        "Existing Exposure (NGN '000)", min_value=0, value=0, step=10000,
    )

    st.markdown("### Balance Metrics")
    avg_deposit_bal  = st.number_input(
        "Average Deposit Balance — CY (NGN '000)", min_value=0, value=0, step=1000,
    )
    avg_loan_bal     = st.number_input(
        "Average Loan Balance — CY (NGN '000)", min_value=0, value=0, step=1000,
    )
    cost_of_funds    = st.number_input(
        "Cost of Funds Rate (%)", min_value=0.0, max_value=50.0, value=8.0, step=0.1,
    )
    ytd_months       = st.number_input(
        "YTD Months Elapsed", min_value=1, max_value=12, value=9,
    )

    use_mock = st.checkbox("Use mock data (no API cost)")
    st.markdown("---")
    run_btn = st.button(
        "Run Revenue Analysis",
        type="primary",
        use_container_width=True,
        disabled=not (company_name or use_mock),
    )
    if "rev_result" in st.session_state:
        meta = st.session_state["rev_result"].get("_metadata", {})
        st.caption(f"Cost: ${meta.get('estimated_cost_usd', 0):.4f} USD")

# ── Revenue input table ────────────────────────────────────────
if "rev_result" not in st.session_state:
    st.markdown("### Revenue & Income Data (NGN '000)")
    st.caption(
        "Enter actual income earned by the bank from this relationship "
        "across all product lines."
    )

    rev_items = st.session_state["_revenue_items"]

    header_cols = st.columns([3, 1, 1, 1])
    header_cols[0].markdown("**Income Category**")
    for j, period in enumerate(PERIODS):
        header_cols[j + 1].markdown(f"**{period}**")

    for cat_key, cat_label in REVENUE_CATEGORIES:
        row_cols = st.columns([3, 1, 1, 1])
        row_cols[0].markdown(cat_label)
        rev_items[cat_key]["py"]  = row_cols[1].number_input(
            f"PY_{cat_key}", min_value=0.0, value=float(rev_items[cat_key]["py"]),
            step=100.0, label_visibility="collapsed", key=f"py_{cat_key}",
        )
        rev_items[cat_key]["cy"]  = row_cols[2].number_input(
            f"CY_{cat_key}", min_value=0.0, value=float(rev_items[cat_key]["cy"]),
            step=100.0, label_visibility="collapsed", key=f"cy_{cat_key}",
        )
        rev_items[cat_key]["ytd"] = row_cols[3].number_input(
            f"YTD_{cat_key}", min_value=0.0, value=float(rev_items[cat_key]["ytd"]),
            step=100.0, label_visibility="collapsed", key=f"ytd_{cat_key}",
        )
    st.session_state["_revenue_items"] = rev_items

    # Summary row
    total_py  = sum(rev_items[k]["py"]  for k, _ in REVENUE_CATEGORIES)
    total_cy  = sum(rev_items[k]["cy"]  for k, _ in REVENUE_CATEGORIES)
    total_ytd = sum(rev_items[k]["ytd"] for k, _ in REVENUE_CATEGORIES)
    total_cols = st.columns([3, 1, 1, 1])
    total_cols[0].markdown("**TOTAL INCOME**")
    total_cols[1].markdown(f"**{total_py:,.0f}**")
    total_cols[2].markdown(f"**{total_cy:,.0f}**")
    total_cols[3].markdown(f"**{total_ytd:,.0f}**")

# ── Run ───────────────────────────────────────────────────────
if run_btn:
    if use_mock:
        st.session_state["rev_result"] = get_mock_revenue_result()
    else:
        rev_items = st.session_state.get("_revenue_items", {})
        revenue_data = {}
        for cat_key, _ in REVENUE_CATEGORIES:
            revenue_data[cat_key] = {
                "prior_year_000":    rev_items.get(cat_key, {}).get("py", 0.0),
                "current_year_000":  rev_items.get(cat_key, {}).get("cy", 0.0),
                "ytd_actual_000":    rev_items.get(cat_key, {}).get("ytd", 0.0),
            }

        payload = {
            "company_name":            company_name,
            "relationship_years":      relationship_yrs,
            "account_officer":         account_officer or None,
            "branch":                  branch or None,
            "facility_amount_000":     facility_amount,
            "facility_type":           facility_type,
            "existing_exposure_000":   existing_exposure,
            "avg_deposit_balance_000": avg_deposit_bal,
            "avg_loan_balance_000":    avg_loan_bal,
            "cost_of_funds_pct":       cost_of_funds,
            "ytd_months_elapsed":      ytd_months,
            "revenue_data":            revenue_data,
        }
        with st.spinner("Revenue Agent analysing relationship economics..."):
            st.session_state["rev_result"] = analyze_relationship(payload)

    # ── Shared suite key ──────────────────────────────────────
    st.session_state["revenue_result"] = st.session_state["rev_result"]
    st.rerun()

# ── Nothing run yet ───────────────────────────────────────────
if "rev_result" not in st.session_state:
    c1, c2, c3 = st.columns(3)
    c1.metric("Metrics calculated", "8+", "ROA, RoRWA, NIM, YoY growth...")
    c2.metric("Relationship tier", "Auto-scored", "GOLD / SILVER / BRONZE")
    c3.metric("Output", "Section 10", "Credit memo narrative")
    st.info(
        "Enter revenue data in the table above and click Run Revenue Analysis, "
        "or tick 'Use mock data'."
    )
    st.stop()

# ── Display results ───────────────────────────────────────────
r   = st.session_state["rev_result"]
rs  = r.get("relationship_score", {})
ra  = r.get("revenue_analysis",   {})
tier  = rs.get("tier", "—")
score = rs.get("score", 0)
roa   = ra.get("roa_pct", 0.0)

t_colors = {"GOLD": "orange", "SILVER": "grey", "BRONZE": "orange"}
tc = t_colors.get(tier, "blue")

st.markdown(
    f"## :{tc}[{tier} Tier Relationship]  ·  "
    f"Score: **{score}/10**  ·  ROA: **{roa:.2f}%**"
)
st.markdown(f"> {r.get('credit_memo_narrative', '')}")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Revenue Analysis", "Relationship Score",
    "Risk Flags", "Memo Draft", "Raw JSON"
])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("YTD Gross Revenue",
              f"NGN {ra.get('ytd_gross_revenue_000', 0):,.0f}k")
    c2.metric("YoY Revenue Growth",
              f"{ra.get('yoy_growth_pct', 0):.1f}%",
              delta_color="normal" if ra.get("yoy_growth_pct", 0) >= 0 else "inverse")
    c3.metric("Plan Attainment",
              f"{ra.get('plan_attainment_pct', 0):.1f}%")
    c4.metric("Revenue Trend",
              ra.get("revenue_trend", "—"))
    c1.metric("Return on Assets",
              f"{roa:.2f}%",
              "Hurdle: 1.0% (GOLD)",
              delta_color="normal" if roa >= 1.0 else "inverse")
    c2.metric("NIM",
              f"{ra.get('nim_pct', 0):.2f}%")
    c3.metric("Avg Deposit Balance",
              f"NGN {ra.get('avg_deposit_balance_000', 0):,.0f}k")
    c4.metric("Avg Loan Balance",
              f"NGN {ra.get('avg_loan_balance_000', 0):,.0f}k")

    breakdown = ra.get("revenue_breakdown", {})
    if breakdown:
        df = pd.DataFrame([
            {"Category": k.replace("_", " ").title(),
             "PY (NGN '000)": v.get("prior_year_000", 0),
             "CY (NGN '000)": v.get("current_year_000", 0),
             "YTD (NGN '000)": v.get("ytd_actual_000", 0),
             "YoY %": f"{v.get('yoy_growth_pct', 0):.1f}%"}
            for k, v in breakdown.items()
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    c1, c2 = st.columns(2)
    c1.metric("Relationship Tier",  tier)
    c2.metric("Composite Score",    f"{score}/10")
    c1.metric("Relationship Years", rs.get("relationship_years", "—"))
    c2.metric("Wallet Share",       f"{rs.get('wallet_share_pct', 0):.1f}%")
    st.caption(rs.get("tier_rationale", ""))
    crs = r.get("cross_sell_opportunities", [])
    if crs:
        st.markdown("**Cross-sell Opportunities:**")
        for opp in crs:
            st.markdown(f"- {opp}")

with tab3:
    flags = r.get("risk_flags", [])
    if not flags:
        st.success("No risk flags identified.")
    for f in flags:
        sev = f.get("severity", "LOW")
        msg = f"**{f.get('flag', '')}** — {f.get('detail', '')}"
        if sev == "HIGH":    st.error(msg)
        elif sev == "MEDIUM": st.warning(msg)
        else:                st.info(msg)

with tab4:
    st.markdown("**Section 10 — Relationship & Revenue (edit before submitting):**")
    st.text_area("",
                 value=r.get("credit_memo_narrative", ""),
                 height=180,
                 label_visibility="collapsed")

with tab5:
    st.json(r)

if st.button("Start New Analysis"):
    for k in ["rev_result", "revenue_result"]:
        st.session_state.pop(k, None)
    st.session_state["_revenue_items"] = {
        cat: {"py": 0.0, "cy": 0.0, "ytd": 0.0}
        for cat, _ in REVENUE_CATEGORIES
    }
    st.rerun()

