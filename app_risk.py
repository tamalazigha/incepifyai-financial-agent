import streamlit as st
import pandas as pd
from risk_agent import assess_risk, get_mock_risk_result, get_all_mock_inputs
 
st.set_page_config(page_title="IncepifyAI — Risk Assessment Agent",
                   page_icon="warning", layout="wide")
 
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #A32D2D;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Risk Assessment Agent · Agent 7 of 8 · Synthesis of Agents 1–6</span>
    </div>""", unsafe_allow_html=True)
 
# ── Check which prior agents are available in session state ───
REQUIRED_KEYS = {
    "financial_result":  "Agent 1 — Financial Analysis",
    "collateral_result": "Agent 2 — Collateral & Security",
    "kyc_stored":        "Agent 3 — Reputation & KYC",
    "revenue_result":    "Agent 4 — Relationship & Revenue",
    "industry_result":   "Agent 5 — Industry Intelligence",
    "management_result": "Agent 6 — Management Assessment",
}
available = {k: k in st.session_state for k in REQUIRED_KEYS}
all_available = all(available.values())
 
with st.sidebar:
    st.markdown("### Prior Agent Status")
    for key, name in REQUIRED_KEYS.items():
        icon = "✅" if available[key] else "⏳"
        st.markdown(f"{icon} {name}")
    st.markdown("---")
    use_mock = st.checkbox("Use mock data (no API cost)",
        value=not all_available,
        help="Auto-enabled when running standalone without the full suite")
    run_btn = st.button("Run Risk Assessment", type="primary",
        use_container_width=True)
    if "risk_result" in st.session_state:
        meta = st.session_state["risk_result"].get("_metadata",{})
        st.caption(f"Tokens: {meta.get('input_tokens',0)+meta.get('output_tokens',0):,}")
        st.caption(f"Cost: ${meta.get('estimated_cost_usd',0):.4f} USD")
 
if run_btn:
    if use_mock:
        st.session_state["risk_result"] = get_mock_risk_result()
    else:
        if not all_available:
            st.error("Not all prior agents have been run. "
                     "Run Agents 1–6 first, or enable mock mode.")
            st.stop()
        all_outputs = {k: st.session_state[k] for k in REQUIRED_KEYS}
        with st.spinner("Synthesising outputs of all 6 agents — please wait..."):
            st.session_state["risk_result"] = assess_risk(all_outputs)
    st.rerun()
 
if "risk_result" not in st.session_state:
    if not all_available:
        st.warning(
            "Running in standalone mode. Prior agent results are not in session. "
            "Enable mock data in the sidebar to test the full output."
        )
    c1,c2,c3 = st.columns(3)
    c1.metric("Input sources","6 agents","Agents 1–6")
    c2.metric("Risk dimensions","6","One per agent")
    c3.metric("Output","Section 17","Credit memo risk narrative")
    st.info("Click Run Risk Assessment in the sidebar to begin.")
    st.stop()
 
# ── Display ────────────────────────────────────────────
r  = st.session_state["risk_result"]
rs = r.get("risk_summary",{})
rating  = rs.get("overall_credit_risk_rating","—")
rec     = rs.get("credit_recommendation","—")
rationale = rs.get("recommendation_rationale","")
 
r_colors={"PASS":"green","WATCH":"orange","SUBSTANDARD":"red","DOUBTFUL":"red","DECLINE":"red"}
rc = r_colors.get(rating,"grey")
 
st.markdown(f"## :{rc}[{rating}]  ·  Recommendation: **{rec}**")
st.markdown(f"> {rationale}")
st.markdown(f"> {r.get('credit_memo_narrative','')}")
st.markdown("---")
 
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "Risk Matrix","Key Risks","Conditions & Covenants",
    "Cross-Dimensional","Memo Draft","Raw JSON"])
 
with tab1:
    matrix = r.get("risk_matrix",[])
    if matrix:
        df = pd.DataFrame([{
            "Dimension":    m.get("risk_category",""),
            "Likelihood":   m.get("likelihood",""),
            "Impact":       m.get("impact",""),
            "Risk Rating":  m.get("risk_rating",""),
            "Key Driver":   m.get("key_driver",""),
            "Residual":     m.get("residual_risk",""),
            "Source":       m.get("source_agent",""),
        } for m in matrix])
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.markdown("---")
        for m in matrix:
            with st.expander(f"{m['risk_category']} — {m['risk_rating']}"):
                st.markdown(f"**Description:** {m.get('risk_description','')}")
                st.markdown(f"**Mitigant:** {m.get('mitigant','')}")
 
with tab2:
    for kr in r.get("key_risks",[]):
        res = kr.get("residual_risk_after_mitigant","LOW")
        col = "red" if res=="HIGH" else "orange" if res=="MEDIUM" else "green"
        with st.expander(f"#{kr['rank']} {kr['risk_title']} — Residual: :{col}[{res}]",expanded=True):
            st.markdown(f"**Risk:** {kr.get('risk_detail','')}")
            st.markdown(f"**Mitigant:** {kr.get('mitigant','')}")
 
with tab3:
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Conditions Precedent** (before drawdown)")
        for cp in r.get("conditions_precedent",[]): st.markdown(f"- {cp}")
        st.markdown("**Structural Covenants**")
        for sc in r.get("structural_covenants",[]): st.markdown(f"- {sc}")
    with c2:
        st.markdown("**Financial Covenants** (ongoing)")
        for fc in r.get("financial_covenants",[]): st.markdown(f"- {fc}")
        st.markdown("**Monitoring Requirements**")
        for mr in r.get("monitoring_requirements",[]): st.markdown(f"- {mr}")
 
with tab4:
    cross = r.get("cross_dimensional_risks",[])
    if not cross: st.info("No cross-dimensional risks identified.")
    for cr in cross:
        st.warning(f"**{cr['risk']}** — Agents: {', '.join(cr.get('agents_involved',[]))}")
        st.caption(cr.get("detail",""))
 
with tab5:
    st.markdown("**Section 17 — Risk Assessment & Mitigants (edit before submitting):**")
    st.text_area("",value=r.get("credit_memo_narrative",""),height=200,label_visibility="collapsed")
 
with tab6:
    st.json(r)
 
if st.button("Reset Risk Assessment"):
    st.session_state.pop("risk_result",None)
    st.rerun()
