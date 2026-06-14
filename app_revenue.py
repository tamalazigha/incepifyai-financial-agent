import streamlit as st
import pandas as pd
from revenue_agent import analyze_relationship, get_mock_revenue_result
 
st.set_page_config(page_title="IncepifyAI — Relationship & Revenue Agent",
                   page_icon="chart_with_upwards_trend", layout="wide")
 
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #3B6D11;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Relationship & Revenue Agent · Agent 4 of 8</span>
    </div>""", unsafe_allow_html=True)
 
REVENUE_CATEGORIES = ["Interest Income","Fee Income",
    "FX Income","Commission Income","Other Income"]
 
with st.sidebar:
    st.markdown("### Entity & Facility")
    company_name  = st.text_input("Company / Obligor Name",
        placeholder="e.g. Sunrise Manufacturing Ltd")
    rel_years     = st.number_input("Relationship Length (years)",
        min_value=0, max_value=50, value=5)
    n_facilities  = st.number_input("Number of Current Facilities",
        min_value=1, max_value=20, value=2)
    exposure      = st.number_input("Total Credit Exposure (NGN '000)",
        min_value=0, value=500000, step=10000)
    cof           = st.number_input("Cost of Funds Allocated (NGN '000)",
        min_value=0, value=2000, step=100,
        help="Interest cost allocated to this credit exposure")
    opex          = st.number_input("Operating Costs Allocated (NGN '000)",
        min_value=0, value=1600, step=100,
        help="Branch and overhead costs allocated to this relationship")
    payment_hist  = st.selectbox("Payment History",
        ["EXCELLENT","GOOD","SATISFACTORY","POOR"])
    use_mock      = st.checkbox("Use mock data (no API cost)")
    st.markdown("---")
    run_btn = st.button("Run Revenue Analysis", type="primary",
        use_container_width=True,
        disabled=not company_name and not use_mock)
    if "rev_result" in st.session_state:
        meta = st.session_state["rev_result"].get("_metadata",{})
        st.caption(f"Cost: ${meta.get('estimated_cost_usd',0):.4f} USD")
 
# Revenue input table
if "rev_result" not in st.session_state:
    st.markdown("### Revenue Data (NGN '000)")
    st.caption("Enter YTD actual, prior year actuals, and current year plan.")
    revenue_items = []
    header = st.columns([2.5,1,1,1])
    header[0].markdown("**Income Stream**")
    header[1].markdown("**YTD Actual**")
    header[2].markdown("**Prior Year**")
    header[3].markdown("**Annual Plan**")
    for cat in REVENUE_CATEGORIES:
        cols = st.columns([2.5,1,1,1])
        cols[0].markdown(f"**{cat}**")
        ytd  = cols[1].number_input("",min_value=0,value=0,step=100,
            key=f"ytd_{cat}",label_visibility="collapsed")
        py_  = cols[2].number_input("",min_value=0,value=0,step=100,
            key=f"py_{cat}",label_visibility="collapsed")
        plan = cols[3].number_input("",min_value=0,value=0,step=100,
            key=f"pl_{cat}",label_visibility="collapsed")
        revenue_items.append({"category":cat,"ytd":ytd,"prior_year":py_,"plan":plan})
    st.session_state["_revenue_items"] = revenue_items
 
if run_btn:
    if use_mock:
        st.session_state["rev_result"] = get_mock_revenue_result()
    else:
        payload = {
            "company_name":                  company_name,
            "relationship_length_years":      rel_years,
            "number_of_facilities":           n_facilities,
            "total_credit_exposure_000":      exposure,
            "cost_of_funds_000":              cof,
            "operating_costs_allocated_000":  opex,
            "payment_history":                payment_hist,
            "revenue_items": st.session_state.get("_revenue_items",[]),
        }
        with st.spinner("Calculating metrics and generating narrative..."):
            st.session_state["rev_result"] = analyze_relationship(payload)
    st.rerun()
 
if "rev_result" not in st.session_state:
    c1,c2,c3 = st.columns(3)
    c1.metric("Metrics computed","15+","automatically in Python")
    c2.metric("External API calls","0","no new accounts needed")
    c3.metric("Cost per analysis","~$0.02","Sonnet narrative only")
    st.info("Fill in the revenue form above and click Run Revenue Analysis.")
    st.stop()
 
r   = st.session_state["rev_result"]
rs  = r.get("relationship_score",{})
ra  = r.get("revenue_analysis",{})
tier= rs.get("tier","—")
tier_colors = {"PLATINUM":"violet","GOLD":"orange","SILVER":"blue",
               "BRONZE":"orange","BELOW_HURDLE":"red"}
tc  = tier_colors.get(tier,"grey")
 
st.markdown(f"## :{tc}[{tier} Tier]  ·  Score: {rs.get('score','—')}/10  ·  Strategic Importance: {rs.get('strategic_importance','—')}")
st.markdown(f"> {r.get('credit_memo_narrative','')}")
st.markdown("---")
 
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "Revenue Analysis","Relationship Profile","Risk Flags",
    "Memo Draft","Raw JSON"])
 
with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("YTD Gross Revenue", f"NGN {ra.get('ytd_gross_revenue_000',0):,.0f}k")
    c2.metric("YoY Growth",f"{ra.get('yoy_growth_pct',0):+.1f}%")
    c3.metric("Plan Attainment",f"{ra.get('plan_attainment_pct',0):.1f}%")
    c4.metric("Relationship ROA",f"{ra.get('roa_pct',0):.2f}%")
    df = pd.DataFrame({"Metric":["Gross Revenue YTD","Prior Year Revenue",
        "Planned Revenue","Net Revenue","Cost of Funds","Operating Costs"],
        "NGN '000":[ra.get("ytd_gross_revenue_000",0),
            ra.get("prior_year_revenue_000",0),ra.get("planned_revenue_000",0),
            ra.get("net_revenue_000",0),ra.get("cost_of_funds_000",0),
            ra.get("operating_costs_000",0)]})
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.markdown(f"**Revenue commentary:** {ra.get('revenue_commentary','')}")
 
with tab2:
    rp = r.get("relationship_profile",{})
    c1,c2,c3 = st.columns(3)
    c1.metric("Relationship Length",f"{rp.get('relationship_length_years',0)} years")
    c2.metric("Relationship Quality",rp.get("relationship_quality","—"))
    c3.metric("Payment History",rp.get("payment_history_assessment","—"))
    if rp.get("payment_history_commentary"):
        st.caption(rp["payment_history_commentary"])
    xp = rs.get("cross_sell_opportunities",[])
    if xp:
        st.markdown("**Cross-sell opportunities:**")
        for opp in xp: st.markdown(f"- {opp}")
 
with tab3:
    flags = r.get("risk_flags",[])
    if not flags: st.success("No risk flags identified.")
    for f in flags:
        msg = f"**{f['flag']}** — {f['detail']}\n\n**Action:** {f['action_required']}"
        if f["severity"]=="HIGH": st.error(msg)
        elif f["severity"]=="MEDIUM": st.warning(msg)
        else: st.info(msg)
 
with tab4:
    st.markdown("**Section 14 — Relationship & Revenue (edit before submitting):**")
    st.text_area("",value=r.get("credit_memo_narrative",""),
                 height=160,label_visibility="collapsed")
 
with tab5:
    st.json(r)
 
if st.button("Start New Analysis"):
    for k in ["rev_result","_revenue_items"]:
        st.session_state.pop(k,None)
    st.rerun()
