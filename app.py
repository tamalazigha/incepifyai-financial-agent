import streamlit as st
import pandas as pd
from financial_agent import analyze_financials, get_mock_result
from pdf_extractor import extract_text_from_pdf, get_pdf_info
 
# ── Page configuration ────────────────────────────────────────────
st.set_page_config(
    page_title="IncepifyAI — Financial Analysis Agent",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# ── Branded header ────────────────────────────────────────────────
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #1D63EB;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Financial Analysis Agent · Credit Underwriting System</span>
    </div>""",
    unsafe_allow_html=True
)
 
# ── Sidebar controls ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Application Details")
    company_name = st.text_input(
        "Company / Obligor Name",
        placeholder="e.g. Dangote Industries Ltd"
    )
    uploaded_file = st.file_uploader(
        "Upload Financial Statements (PDF)",
        type=["pdf"],
        help="Text-based PDFs work best. See docs for scanned PDF handling."
    )
    use_mock = st.checkbox(
        "Use mock data (free — no API call)",
        help="Test the full UI without spending API credits"
    )
    st.markdown("---")
    run_btn = False
    if (uploaded_file and company_name) or use_mock:
        run_btn = st.button("Run Financial Analysis",
                            type="primary", use_container_width=True)
    else:
        st.info("Enter company name and upload a PDF to begin")
    # Show token cost after each run
    if "result" in st.session_state:
        meta = st.session_state["result"].get("_metadata", {})
        st.markdown("---")
        st.caption(f"Model: {meta.get('model_used','—')}")
        st.caption(f"Tokens in: {meta.get('input_tokens',0):,}")
        st.caption(f"Tokens out: {meta.get('output_tokens',0):,}")
        st.caption(f"Est. cost: ${meta.get('estimated_cost_usd',0):.4f} USD")
 
# ── Run the analysis ──────────────────────────────────────────────
if run_btn:
    if use_mock:
        st.session_state["result"] = get_mock_result()
        st.session_state["company"] = "Test Manufacturing Co Ltd"
    else:
        with st.spinner("Extracting text from PDF..."):
            pdf_bytes = uploaded_file.read()
            pdf_info = get_pdf_info(pdf_bytes)
            if not pdf_info["has_text"]:
                st.error("Scanned PDF detected — no selectable text found.")
                st.error("Use a digitally produced PDF or contact IncepifyAI.")
                st.stop()
            extracted = extract_text_from_pdf(pdf_bytes)
        with st.spinner(f"Analysing {company_name}..."):
            result = analyze_financials(extracted, company_name)
            st.session_state["result"] = result
            st.session_state["company"] = company_name
 
# ── Welcome screen (no result yet) ────────────────────────────────
if "result" not in st.session_state:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Analysis time", "< 2 min", "vs 1-2 days manual")
    c2.metric("Ratios computed", "15+", "automatically")
    c3.metric("Risk flags", "Auto", "CBN policy rules")
    c4.metric("Output", "JSON + memo", "structured for credit memo")
    st.info("Upload a financial statement PDF in the sidebar to begin.")
    st.stop()
 
# ── Display results ───────────────────────────────────────────────
result  = st.session_state["result"]
company = st.session_state.get("company", "Company")
rec     = result.get("credit_recommendation", {})
assess  = rec.get("overall_assessment", "N/A")
icons   = {"STRONG":"🟢","SATISFACTORY":"🔵","MARGINAL":"🟡","UNSATISFACTORY":"🔴"}
 
st.markdown(f"## {icons.get(assess,'⚪')} {company} — Assessment: **{assess}**")
st.markdown(f"> {rec.get('narrative_summary', '')}")
st.markdown("---")
 
# ── 5 tabs ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Key Ratios", "Risk Flags", "Sensitivity", "Memo Draft", "Raw JSON"
])
 
with tab1:
    ratios = result.get("key_ratios", {})
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Profitability")
        for k, v in ratios.get("profitability", {}).items():
            if v is not None: st.metric(k.replace("_pct","").replace("_"," ").title(),
                                        f"{v:.1f}%")
        st.markdown("#### Liquidity")
        for k, v in ratios.get("liquidity", {}).items():
            if v is not None:
                dc = "normal" if v >= 1.0 else "inverse"
                st.metric(k.replace("_"," ").title(), f"{v:.2f}x", delta_color=dc)
    with c2:
        st.markdown("#### Leverage")
        for k, v in ratios.get("leverage", {}).items():
            if v is not None: st.metric(k.replace("_"," ").title(), f"{v:.2f}x")
        st.markdown("#### Cashflow")
        for k, v in ratios.get("cashflow", {}).items():
            if v is not None:
                lbl = k.replace("_000","(NGN 000)").replace("_"," ").title()
                val = f"{v:,.0f}" if "000" in k else f"{v:.2f}"
                st.metric(lbl, val)
 
with tab2:
    flags = result.get("risk_flags", [])
    if not flags:
        st.success("No risk flags identified under current policy thresholds.")
    for flag in flags:
        sev   = flag.get("severity","LOW")
        label = flag.get("flag","")
        det   = flag.get("detail","")
        thr   = flag.get("policy_threshold","")
        msg   = f"**{label}** — {det}  \n*Policy threshold: {thr}*"
        if sev == "HIGH":   st.error(f"HIGH: {msg}")
        elif sev == "MEDIUM": st.warning(f"MEDIUM: {msg}")
        else:               st.info(f"LOW: {msg}")
 
with tab3:
    sens = result.get("sensitivity_analysis", {})
    base = sens.get("base_case", {})
    down = sens.get("downside_case", {})
    df = pd.DataFrame({
        "Year":         ["Year 1","Year 2","Year 3"],
        "Base DSCR":    [base.get("dscr_yr1"),base.get("dscr_yr2"),base.get("dscr_yr3")],
        "Downside DSCR":[down.get("dscr_yr1"),down.get("dscr_yr2"),down.get("dscr_yr3")],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"DSCR minimum: 1.20x · Downside: {down.get('revenue_stress_pct',0):.0f}% revenue stress")
    st.markdown(f"**Base case:** {base.get('narrative','')}")
    st.markdown(f"**Downside:** {down.get('narrative','')}")
 
with tab4:
    hl = result.get("financial_highlights", {})
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Strengths**")
        for s in hl.get("key_strengths", []): st.markdown(f"- {s}")
    with c2:
        st.markdown("**Concerns**")
        for c in hl.get("key_concerns", []):  st.markdown(f"- {c}")
    st.markdown("---")
    st.markdown("**Section 13 — Financial Analysis (edit before submitting):**")
    st.text_area("Override memo text:", value=rec.get("narrative_summary",""),
                 height=160, label_visibility="collapsed")
 
with tab5:
    st.json(result)
