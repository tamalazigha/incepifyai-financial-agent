
import streamlit as st
import pandas as pd
from industry_agent import analyze_industry, get_mock_industry_result
 
st.set_page_config(
    page_title="IncepifyAI — Industry Intelligence Agent",
    page_icon="🔭",
    layout="wide",
)
 
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #854F0B;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Industry Intelligence Agent · Agent 5 of 8</span>
    </div>""",
    unsafe_allow_html=True,
)
 
CBN_SECTORS = [
    "Agriculture",
    "Construction",
    "Education",
    "Financial Services",
    "Healthcare & Pharmaceuticals",
    "ICT & Technology",
    "Manufacturing",
    "Mining & Quarrying",
    "Oil & Gas",
    "Power & Energy",
    "Real Estate",
    "Retail & Trade",
    "Transport & Logistics",
    "Other",
]
 
# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Company & Sector Details")
    company_name = st.text_input(
        "Company / Obligor Name",
        placeholder="e.g. Sunrise Manufacturing Ltd",
    )
    sector = st.selectbox("CBN Sector", CBN_SECTORS)
    sub_sector = st.text_input(
        "Sub-Sector (optional)",
        placeholder="e.g. Food & Beverages · Cement · Textiles",
    )
    country = st.selectbox(
        "Country",
        ["Nigeria", "Ghana", "Kenya", "South Africa", "Other"],
    )
    company_desc = st.text_area(
        "Brief Company Description (optional)",
        placeholder="e.g. Produces packaged food products; 8-year client; est. 2% market share",
        height=100,
        help="More context = more targeted searches = better output",
    )
    use_mock = st.checkbox("Use mock data (no API cost)")
    st.markdown("---")
    run_btn = st.button(
        "Run Industry Analysis",
        type="primary",
        use_container_width=True,
        disabled=not (company_name and sector) and not use_mock,
    )
    if "ind_result" in st.session_state:
        meta = st.session_state["ind_result"].get("_metadata", {})
        n = len(meta.get("searches_conducted", []))
        st.caption(f"Searches run: {n}")
        st.caption(f"Cost: ${meta.get('estimated_cost_usd', 0):.4f} USD")
 
# ── Run analysis ──────────────────────────────────────────────────────────────
if run_btn:
    if use_mock:
        st.session_state["ind_result"] = get_mock_industry_result()
    else:
        payload = {
            "company_name":       company_name,
            "sector":             sector,
            "sub_sector":         sub_sector or None,
            "country":            country,
            "company_description": company_desc or None,
        }
        with st.spinner(f"Researching {sector} industry — web searches in progress..."):
            st.session_state["ind_result"] = analyze_industry(payload)
    # ── shared suite key ──────────────────────────────────────────────────────
    st.session_state["industry_result"] = st.session_state["ind_result"]
    st.rerun()
 
# ── Nothing run yet ───────────────────────────────────────────────────────────
if "ind_result" not in st.session_state:
    c1, c2, c3 = st.columns(3)
    c1.metric("Searches per run",  "3–6",         "web queries auto-selected by Claude")
    c2.metric("Sources",           "8 categories", "CBN, NBS, Reuters, NGX...")
    c3.metric("Cost per run",      "~$0.05",       "Sonnet + web search tokens")
    st.info(
        "Select the sector and enter the company name in the sidebar, "
        "then click Run Industry Analysis."
    )
    st.stop()
 
# ── Display results ───────────────────────────────────────────────────────────
r   = st.session_state["ind_result"]
ia  = r.get("industry_assessment", {})
ip  = r.get("industry_profile",    {})
md  = r.get("market_data",         {})
 
outlook = ia.get("outlook",                 "—")
rating  = ia.get("industry_risk_rating",    "—")
impl    = ia.get("credit_risk_implication", "—")
 
o_colors = {"POSITIVE": "green", "STABLE": "blue", "CAUTIOUS": "orange", "NEGATIVE": "red"}
r_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red", "VERY_HIGH": "red"}
oc = o_colors.get(outlook, "grey")
rc = r_colors.get(rating,  "grey")
 
st.markdown(
    f"## :{oc}[{outlook} Outlook]  ·  :{rc}[{rating} Risk]  ·  "
    f"Credit Implication: **{impl}**"
)
st.markdown(f"> {r.get('credit_memo_narrative', '')}")
st.markdown("---")
 
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Market Overview",
    "Competitive Landscape",
    "Trends & Risks",
    "Memo Draft",
    "Raw JSON",
])
 
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Market Size (USD)",
        f"${md.get('market_size_usd_bn', 'N/A')}bn"
        if md.get("market_size_usd_bn") is not None else "N/A",
    )
    c2.metric(
        "Market Size (NGN)",
        f"₦{md.get('market_size_ngn_bn', 'N/A')}bn"
        if md.get("market_size_ngn_bn") is not None else "N/A",
    )
    c3.metric(
        "Historical CAGR (5yr)",
        f"{md.get('cagr_historical_5yr_pct', 'N/A')}%"
        if md.get("cagr_historical_5yr_pct") is not None else "N/A",
    )
    c4.metric(
        "Projected CAGR (5yr)",
        f"{md.get('cagr_projected_5yr_pct', 'N/A')}%"
        if md.get("cagr_projected_5yr_pct") is not None else "N/A",
    )
    if md.get("data_source_notes"):
        st.caption(f"Sources: {md['data_source_notes']}")
    st.markdown(
        f"**Sector:** {ip.get('sector', '—')}  ·  "
        f"**Sub-sector:** {ip.get('sub_sector', '—')}  ·  "
        f"**CBN Classification:** {ip.get('cbn_sector_classification', '—')}"
    )
    if ia.get("outlook_commentary"):
        st.markdown(f"**Outlook commentary:** {ia['outlook_commentary']}")
 
with tab2:
    cl = r.get("competitive_landscape", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Market Structure",     cl.get("market_structure",     "—"))
    c2.metric("Barriers to Entry",    cl.get("barriers_to_entry",    "—"))
    c3.metric("Competitive Intensity", cl.get("competitive_intensity", "—"))
    competitors = cl.get("top_competitors", [])
    if competitors:
        st.markdown("**Key Competitors:**  " + "  ·  ".join(competitors))
    op = r.get("obligor_position", {})
    c1, c2 = st.columns(2)
    c1.metric("Competitive Position", op.get("competitive_position", "—"))
    c2.metric(
        "Est. Market Share",
        f"{op.get('estimated_market_share_pct', 'N/A')}%"
        if op.get("estimated_market_share_pct") is not None else "N/A",
    )
    if op.get("key_differentiators"):
        st.markdown("**Differentiators:**")
        for d in op["key_differentiators"]:
            st.markdown(f"- {d}")
    if op.get("key_vulnerabilities"):
        st.markdown("**Vulnerabilities:**")
        for v in op["key_vulnerabilities"]:
            st.markdown(f"- {v}")
 
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Industry Trends**")
        for tr in r.get("industry_trends", []):
            imp = tr.get("impact", "NEUTRAL")
            ic  = "green" if imp == "POSITIVE" else "red" if imp == "NEGATIVE" else "grey"
            st.markdown(f":{ic}[{imp}] **{tr['trend']}**")
            st.caption(tr.get("detail", ""))
    with c2:
        st.markdown("**Risk Factors**")
        for rf in r.get("risk_factors", []):
            sev = rf.get("severity", "LOW")
            sc  = "red" if sev == "HIGH" else "orange" if sev == "MEDIUM" else "blue"
            st.markdown(f":{sc}[{sev}] **{rf['risk']}**")
            st.caption(rf.get("detail", ""))
 
with tab4:
    st.markdown("**Section 11 — Industry Analysis (edit before submitting):**")
    st.text_area(
        "",
        value=r.get("credit_memo_narrative", ""),
        height=160,
        label_visibility="collapsed",
    )
    searches = r.get("_metadata", {}).get("searches_conducted", [])
    if searches:
        st.markdown("**Web searches conducted by Claude:**")
        for s in searches:
            st.markdown(f"- {s}")
 
with tab5:
    st.json(r)
 
# ── Reset ─────────────────────────────────────────────────────────────────────
if st.button("Start New Analysis"):
    st.session_state.pop("ind_result", None)
    st.rerun()
