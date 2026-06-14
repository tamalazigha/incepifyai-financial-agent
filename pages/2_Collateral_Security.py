import importlib.util

streamlit_spec = importlib.util.find_spec("streamlit")
if streamlit_spec is None:
    raise ImportError("The 'streamlit' package is required to run this app.")
st = importlib.import_module("streamlit")

pandas_spec = importlib.util.find_spec("pandas")
if pandas_spec is None:
    raise ImportError("The 'pandas' package is required to run this app.")
pd = importlib.import_module("pandas")

from collateral_agent import analyze_collateral, get_mock_collateral_result
st.set_page_config(
    page_title="IncepifyAI — Collateral & Security Agent",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# ── Branded header ────────────────────────────────────────────────
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #0F6E56;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Collateral & Security Agent · Credit Underwriting System · Agent 2 of 8</span>
    </div>""",
    unsafe_allow_html=True
)
 
# ── Collateral type options ────────────────────────────────────────
COLL_TYPES = {
    "CASH_NGN":              "Cash / Fixed Deposit (NGN)",
    "CASH_USD":              "Cash / Fixed Deposit (USD)",
    "FGN_SECURITIES":        "Federal Government Securities",
    "LIFE_ASSURANCE":        "Life Assurance Policy",
    "TRADE_RECEIVABLES":     "Trade Receivables (<90 days)",
    "REAL_PROPERTY_COFO":    "Real Property — CofO Title",
    "REAL_PROPERTY_LEASEHOLD":"Real Property — Leasehold",
    "LISTED_EQUITIES":       "Listed Equities (NGX)",
    "PLANT_EQUIPMENT":       "Plant & Equipment",
    "MOTOR_VEHICLES":        "Motor Vehicles",
    "STOCK_FAST":            "Stock in Trade (fast-moving)",
    "STOCK_SLOW":            "Stock in Trade (slow-moving)",
    "UNLISTED_EQUITIES":     "Unlisted / Private Equities",
    "CORPORATE_GUARANTEE":   "Corporate Guarantee",
    "PERSONAL_GUARANTEE":    "Personal Guarantee",
}
FACILITY_TYPES = {
    "TERM_LOAN_3YR_PLUS":   "Term Loan (tenor ≥ 3 years)  — 150% min",
    "TERM_LOAN_UNDER_3YR":  "Term Loan (tenor < 3 years)  — 125% min",
    "OVERDRAFT":            "Overdraft / Revolving Credit  — 125% min",
    "TRADE_FINANCE":        "Trade Finance (LC/Bond)       — 110% min",
}
 
# ── Session state: list of collateral items ───────────────────────
if "collateral_items" not in st.session_state:
    st.session_state.collateral_items = [{"id": 1}]
 
# ── Sidebar: facility details ─────────────────────────────────────
with st.sidebar:
    st.markdown("### Facility Details")
    company_name  = st.text_input("Company / Obligor Name",
                                  placeholder="e.g. Sunrise Manufacturing Ltd")
    facility_amt  = st.number_input("Facility Amount (NGN '000)",
                                    min_value=0, value=500000, step=10000)
    facility_type = st.selectbox("Facility Type",
                                 options=list(FACILITY_TYPES.keys()),
                                 format_func=lambda x: FACILITY_TYPES[x])
    tenor_months  = st.number_input("Facility Tenor (months)",
                                    min_value=1, max_value=360, value=60)
    use_mock = st.checkbox("Use mock data (no API cost)")
    st.markdown("---")
    if st.button("+ Add Collateral Item", use_container_width=True):
        new_id = max(i["id"] for i in st.session_state.collateral_items) + 1
        st.session_state.collateral_items.append({"id": new_id})
        st.rerun()
    st.markdown("---")
    run_btn = st.button("Run Collateral Analysis",
                        type="primary", use_container_width=True,
                        disabled=not (company_name or use_mock))
    if "coll_result" in st.session_state:
        meta = st.session_state["coll_result"].get("_metadata",{})
        st.caption(f"Cost: ${meta.get('estimated_cost_usd',0):.4f} USD")
 
# ── Collateral item forms ──────────────────────────────────────────
if "coll_result" not in st.session_state:
    st.markdown("### Collateral / Security Package")
    items_data = []
    for item in st.session_state.collateral_items:
        item_id = item["id"]
        with st.expander(f"Collateral Item {item_id}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                c_type = st.selectbox(f"Collateral Type #{item_id}",
                    options=list(COLL_TYPES.keys()),
                    format_func=lambda x: COLL_TYPES[x],
                    key=f"type_{item_id}")
                c_desc = st.text_input(f"Description #{item_id}",
                    placeholder="e.g. Industrial warehouse, Apapa Lagos",
                    key=f"desc_{item_id}")
                c_omv  = st.number_input(f"Open Market Value (NGN '000) #{item_id}",
                    min_value=0, value=500000, step=10000,
                    key=f"omv_{item_id}")
                c_fsv  = st.number_input(f"Forced Sale Value (NGN '000) #{item_id}",
                    min_value=0, value=0, step=10000,
                    help="Leave 0 if unknown — agent will estimate at 70% of OMV",
                    key=f"fsv_{item_id}")
            with col2:
                c_val_date  = st.text_input(f"Valuation Date #{item_id}",
                    placeholder="e.g. March 2024", key=f"vd_{item_id}")
                c_location  = st.text_input(f"Location #{item_id}",
                    placeholder="e.g. Victoria Island, Lagos", key=f"loc_{item_id}")
                st.markdown(f"**Documentation Status #{item_id}**")
                d_title  = st.checkbox("Title document available", key=f"title_{item_id}", value=True)
                d_val    = st.checkbox("Valuation report available", key=f"val_{item_id}", value=True)
                d_ins    = st.checkbox("Insurance in place (bank noted)", key=f"ins_{item_id}")
                d_cac    = st.checkbox("CAC charge registered", key=f"cac_{item_id}")
                d_gov    = st.checkbox("Governor's Consent obtained", key=f"gov_{item_id}")
                d_enc    = st.checkbox("Confirmed encumbrance-free", key=f"enc_{item_id}", value=True)
            if len(st.session_state.collateral_items) > 1:
                if st.button(f"Remove item {item_id}", key=f"rm_{item_id}"):
                    st.session_state.collateral_items = [
                        x for x in st.session_state.collateral_items
                        if x["id"] != item_id
                    ]
                    st.rerun()
            items_data.append({
                "item_number": item_id,
                "type": c_type,
                "description": c_desc,
                "open_market_value_000": c_omv,
                "forced_sale_value_000": c_fsv if c_fsv > 0 else None,
                "valuation_date": c_val_date or None,
                "location": c_location or None,
                "documentation_status": {
                    "title_document_available": d_title,
                    "valuation_report_available": d_val,
                    "insurance_in_place": d_ins,
                    "charge_registered_cac": d_cac,
                    "governors_consent_obtained": d_gov,
                    "encumbrance_free": d_enc
                }
            })
    st.session_state["_items_data"] = items_data
 
# ── Run analysis ──────────────────────────────────────────────────
if run_btn:
    if use_mock:
        st.session_state["coll_result"] = get_mock_collateral_result()
    else:
        payload = {
            "company_name": company_name,
            "facility_amount_000": facility_amt,
            "facility_type": facility_type,
            "facility_tenor_months": tenor_months,
            "collateral_items": st.session_state.get("_items_data", [])
        }
        with st.spinner("Collateral & Security Agent analysing..."):
            st.session_state["coll_result"] = analyze_collateral(payload)
            st.session_state["collateral_result"] = st.session_state["coll_result"]
    st.rerun()
 
# ── Display results ───────────────────────────────────────────────
if "coll_result" not in st.session_state:
    st.info("Complete the collateral details above and click Run Collateral Analysis.")
    st.stop()
 
r = st.session_state["coll_result"]
cs = r.get("coverage_summary", {})
status = cs.get("coverage_status","—")
icons  = {"ADEQUATE":"green", "SHORTFALL":"red", "BORDERLINE":"orange"}
color  = icons.get(status,"grey")
 
st.markdown(f"## Security Assessment: :{color}[**{status}**]")
st.markdown(f"> {r.get('credit_memo_narrative','')}")
 
# Pre-disbursement conditions banner
pdc = r.get("pre_disbursement_conditions", [])
if pdc:
    st.error("**PRE-DISBURSEMENT CONDITIONS — must be satisfied before any drawdown:**")
    for c in pdc: st.error(f"  •  {c}")
 
st.markdown("---")
 
# ── Four results tabs ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Coverage Summary", "Item Analysis", "Risk Flags",
    "Memo Draft", "Raw JSON"
])
 
with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Coverage Ratio", f"{cs.get('coverage_ratio_pct',0):.1f}%",
              f"Min: {cs.get('minimum_required_pct',0):.0f}%")
    surplus = cs.get("shortfall_or_surplus_000",0)
    c2.metric("Shortfall / Surplus",
              f"NGN {abs(surplus):,.0f}k",
              "Surplus" if surplus>0 else "SHORTFALL",
              delta_color="normal" if surplus>0 else "inverse")
    c3.metric("Total Adjusted Value",
              f"NGN {cs.get('total_adjusted_value_000',0):,.0f}k")
    c4.metric("Tier 1 & 2 Share",
              f"{cs.get('tier_1_pct_of_total',0)+cs.get('tier_2_pct_of_total',0):.1f}%",
              "Higher is better")
    # Tier breakdown table
    tier_df = pd.DataFrame({
        "Tier": ["Tier 1 (Cash/Govt Sec)","Tier 2 (Property/Receivables)",
                 "Tier 3 (Equipment/Stock/Equities)","Tier 4 (Guarantees/Unlisted)"],
        "% of Adjusted Value": [
            cs.get("tier_1_pct_of_total",0), cs.get("tier_2_pct_of_total",0),
            cs.get("tier_3_pct_of_total",0), cs.get("tier_4_pct_of_total",0)
        ]
    })
    st.dataframe(tier_df, use_container_width=True, hide_index=True)
 
with tab2:
    for item in r.get("collateral_analysis", []):
        with st.expander(f"Item {item['item_number']}: {item.get('description','—')} — {item.get('quality_tier','—')}", expanded=True):
            c1,c2,c3 = st.columns(3)
            c1.metric("Open Market Value", f"NGN {item.get('open_market_value_000',0):,.0f}k")
            c2.metric("Advance Rate", f"{item.get('advance_rate_pct',0):.0f}%")
            c3.metric("Adjusted Value", f"NGN {item.get('adjusted_value_000',0):,.0f}k")
            enf = item.get("enforcement_risk","—")
            col = "red" if enf=="HIGH" else "orange" if enf=="MEDIUM" else "green"
            st.markdown(f"**Enforcement Risk:** :{col}[{enf}]")
            st.caption(item.get("enforcement_risk_narrative",""))
            if item.get("documentation_gaps"):
                st.warning("Documentation gaps: " + " · ".join(item["documentation_gaps"]))
            perf = item.get("perfection_checklist",{})
            perf_df = pd.DataFrame({
                "Requirement": list(perf.keys()),
                "Status": list(perf.values())
            })
            st.dataframe(perf_df, use_container_width=True, hide_index=True)
 
with tab3:
    flags = r.get("risk_flags",[])
    if not flags: st.success("No risk flags identified.")
    for f in flags:
        sev = f.get("severity","LOW")
        msg = (f"**{f.get('flag','')}** — {f.get('detail','')}\n\n"
               f"*Legal ref: {f.get('legal_reference','—')}*\n\n"
               f"Pre-disbursement condition: {'YES' if f.get('pre_disbursement_condition') else 'No'}")
        if sev=="HIGH":   st.error(msg)
        elif sev=="MEDIUM": st.warning(msg)
        else:             st.info(msg)
 
with tab4:
    st.markdown("**Section 4 — Collateral / Security (edit before submitting):**")
    st.text_area("Override memo text:", value=r.get("credit_memo_narrative",""),
                 height=180, label_visibility="collapsed")
    if pdc:
        st.markdown("**Pre-Disbursement Conditions:**")
        for c in pdc: st.markdown(f"- {c}")
 
with tab5:
    st.json(r)
 
# ── Reset button ──────────────────────────────────────────────────
if st.button("Start New Analysis"):
    for k in ["coll_result", "_items_data"]:
        if k in st.session_state: del st.session_state[k]
    st.session_state.collateral_items = [{"id": 1}]
    st.rerun()