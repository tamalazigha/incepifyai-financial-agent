import streamlit as st
import pandas as pd
from management_agent import assess_management, get_mock_management_result
 
st.set_page_config(page_title="IncepifyAI — Management Assessment Agent",
                   page_icon="briefcase", layout="wide")
 
st.markdown(
    """<div style='padding:16px 20px;background:#F0F2F6;
    border-radius:8px;border-left:4px solid #185FA5;margin-bottom:20px'>
    <span style='font-size:22px;font-weight:700;color:#161E41'>Incepify</span>
    <span style='font-size:22px;font-weight:700;color:#1D63EB'>AI</span>
    <span style='font-size:13px;color:grey;margin-left:12px'>
        Management Assessment Agent · Agent 6 of 8</span>
    </div>""", unsafe_allow_html=True)
 
# ── Session state: director list ──────────────────────
if "mgmt_directors" not in st.session_state:
    st.session_state.mgmt_directors = [{"id": 1}]
 
# ── Sidebar: company & board details ──────────────────
with st.sidebar:
    st.markdown("### Company Details")
    company_name = st.text_input("Company Name",
        placeholder="e.g. Sunrise Manufacturing Ltd")
    rc_number    = st.text_input("CAC RC Number (optional)",
        placeholder="e.g. RC-482931")
    st.markdown("### Board Composition")
    audit_committee     = st.checkbox("Audit committee in place")
    ceo_chair_separate  = st.checkbox("CEO and Chairman are separate", value=True)
    use_mock = st.checkbox("Use mock data (no API cost)")
    st.markdown("---")
    if st.button("+ Add Director", use_container_width=True):
        new_id = max(d["id"] for d in st.session_state.mgmt_directors) + 1
        st.session_state.mgmt_directors.append({"id": new_id})
        st.rerun()
    run_btn = st.button("Run Management Assessment", type="primary",
        use_container_width=True,
        disabled=not company_name and not use_mock)
    if "mgmt_result" in st.session_state:
        meta = st.session_state["mgmt_result"].get("_metadata",{})
        n = len(meta.get("searches_conducted",[]))
        st.caption(f"Web searches: {n}")
        st.caption(f"Cost: ${meta.get('estimated_cost_usd',0):.4f} USD")
 
# ── Director entry forms ───────────────────────────────
if "mgmt_result" not in st.session_state:
    st.markdown("### Director & Management Profiles")
    st.caption("Complete as much detail as possible — more context produces better research.")
    directors_data = []
    for d in st.session_state.mgmt_directors:
        did = d["id"]
        with st.expander(f"Director / Officer {did}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                d_name    = st.text_input(f"Full Name #{did}",
                    placeholder="e.g. Chidi Okonkwo", key=f"mgmt_name_{did}")
                d_role    = st.text_input(f"Role / Position #{did}",
                    placeholder="e.g. Managing Director / CEO",
                    key=f"mgmt_role_{did}")
                d_yrs     = st.number_input(f"Total Years Experience #{did}",
                    min_value=0, max_value=50, value=10,
                    key=f"mgmt_yrs_{did}")
                d_quals   = st.text_input(f"Qualifications #{did}",
                    placeholder="e.g. MBA (LBS), BSc Engineering (UNILAG), ICAN",
                    key=f"mgmt_quals_{did}")
            with c2:
                d_prev    = st.text_area(f"Previous Companies / Roles #{did}",
                    placeholder="e.g. Nestlé Nigeria — Production Manager (2010-2018)\nDangote Industries — Operations Director (2018-2022)",
                    height=100, key=f"mgmt_prev_{did}")
                d_nex     = st.checkbox(f"Non-Executive Director #{did}",
                    key=f"mgmt_nex_{did}")
                d_keyman  = st.checkbox(f"Key man / primary decision-maker #{did}",
                    key=f"mgmt_km_{did}")
                d_notes   = st.text_input(f"Additional context #{did}",
                    placeholder="e.g. LinkedIn: linkedin.com/in/...",
                    key=f"mgmt_notes_{did}")
            if len(st.session_state.mgmt_directors) > 1:
                if st.button(f"Remove #{did}", key=f"mgmt_rm_{did}"):
                    st.session_state.mgmt_directors = [
                        x for x in st.session_state.mgmt_directors
                        if x["id"] != did
                    ]
                    st.rerun()
            directors_data.append({
                "name":                d_name,
                "role":                d_role,
                "years_of_experience": d_yrs,
                "qualifications":      [q.strip() for q in d_quals.split(",") if q.strip()],
                "previous_companies":  [p.strip() for p in d_prev.splitlines() if p.strip()],
                "is_non_executive":    d_nex,
                "is_key_man":          d_keyman,
                "notes":               d_notes or None,
            })
    st.session_state["_mgmt_directors"] = directors_data
 
# ── Run ────────────────────────────────────────────────
if run_btn:
    if use_mock:
        st.session_state["mgmt_result"] = get_mock_management_result()
    else:
        payload = {
            "company_name":        company_name,
            "rc_number":           rc_number or None,
            "audit_committee":     audit_committee,
            "ceo_chairman_separate": ceo_chair_separate,
            "directors":           st.session_state.get("_mgmt_directors", []),
        }
        with st.spinner("Researching management team — web searches in progress..."):
            st.session_state["mgmt_result"] = assess_management(payload)
    st.rerun()
 
# ── No result yet ──────────────────────────────────────
if "mgmt_result" not in st.session_state:
    c1, c2, c3 = st.columns(3)
    c1.metric("Scoring dimensions", "6", "weighted composite")
    c2.metric("Searches per director", "2–3", "CAC + background")
    c3.metric("Cost per run", "~$0.04", "Sonnet + web search")
    st.info("Enter director details above and click Run Management Assessment.")
    st.stop()
 
# ── Results ────────────────────────────────────────────
r   = st.session_state["mgmt_result"]
ma  = r.get("management_assessment", {})
mo  = r.get("management_overview",   {})
score   = ma.get("overall_management_score", 0)
quality = ma.get("management_quality", "—")
key_man = ma.get("key_man_risk_identified", False)
q_colors = {"STRONG":"green","SATISFACTORY":"orange","WEAK":"red"}
qc = q_colors.get(quality,"grey")
 
st.markdown(f"## :{qc}[{quality} Management]  ·  Score: **{score}/10**")
if key_man:
    st.error(f"⚠️  KEY MAN RISK: {ma.get('key_man_description','')}")
st.markdown(f"> {r.get('credit_memo_narrative','')}")
st.markdown("---")
 
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "Overview","Director Profiles","Board Governance","Memo Draft","Raw JSON"])
 
with tab1:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Overall Score",   f"{score}/10")
    c2.metric("Quality Band",    quality)
    c3.metric("Board Size",      mo.get("total_directors","—"))
    c4.metric("Independence",    f"{mo.get('board_independence_pct',0):.0f}%")
    c1,c2 = st.columns(2)
    c1.metric("CAC Verification", mo.get("cac_verification_status","—"))
    c2.metric("Succession Plan",  ma.get("succession_planning","—"))
    st.metric("Team Depth",       ma.get("team_depth","—"))
 
with tab2:
    for dp in r.get("director_profiles",[]):
        ds = dp.get("individual_score",0)
        dc = "green" if ds>=8 else "orange" if ds>=5 else "red"
        with st.expander(
            f"{dp.get('name')} ({dp.get('role')}) — Score: {ds}/10",
            expanded=True):
            c1,c2,c3 = st.columns(3)
            c1.metric("Experience", f"{dp.get('years_of_experience',0)} yrs")
            c2.metric("Track Record", dp.get("track_record","—"))
            c3.metric("CAC Status", dp.get("cac_registered","—"))
            if dp.get("qualifications"):
                st.markdown("**Qualifications:** " + " · ".join(dp["qualifications"]))
            if dp.get("previous_companies"):
                st.markdown("**Previous roles:**")
                for pc in dp["previous_companies"]: st.markdown(f"- {pc}")
            if dp.get("key_man_risk"):
                st.warning("Key man risk identified for this director")
            if dp.get("web_search_findings"):
                st.info(f"Web findings: {dp['web_search_findings']}")
            st.caption(dp.get("individual_score_narrative",""))
 
with tab3:
    ba = r.get("board_assessment",{})
    gov = ba.get("governance_structure","—")
    gc = "green" if gov=="STRONG" else "orange" if gov=="ADEQUATE" else "red"
    st.markdown(f"**Governance Structure:** :{gc}[{gov}]")
    st.caption(ba.get("governance_commentary",""))
    c1,c2,c3 = st.columns(3)
    c1.metric("Audit Committee", "Yes" if ba.get("audit_committee_present") else "No")
    c2.metric("CEO/Chair Separate", "Yes" if ba.get("ceo_chairman_separation") else "No")
    c3.metric("Skills Diversity", ba.get("board_skills_diversity","—"))
    flags = r.get("risk_flags",[])
    if flags:
        st.markdown("**Risk Flags:**")
        for f in flags:
            sev=f.get("severity","LOW")
            msg=f"**{f['flag']}** — {f['detail']}\n\n**Action:** {f['action_required']}"
            if sev=="HIGH": st.error(msg)
            elif sev=="MEDIUM": st.warning(msg)
            else: st.info(msg)
 
with tab4:
    st.markdown("**Section 13 — Management Assessment (edit before submitting):**")
    st.text_area("",value=r.get("credit_memo_narrative",""),
                 height=160,label_visibility="collapsed")
    searches = r.get("_metadata",{}).get("searches_conducted",[])
    if searches:
        st.markdown("**Web searches conducted:**")
        for s in searches: st.markdown(f"- {s}")
 
with tab5:
    st.json(r)
 
if st.button("Start New Assessment"):
    for k in ["mgmt_result","_mgmt_directors"]:
        st.session_state.pop(k, None)
    st.session_state.mgmt_directors = [{"id": 1}]
    st.rerun()
