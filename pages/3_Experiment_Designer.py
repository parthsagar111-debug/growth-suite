import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Experiment designer")
st.markdown('<p class="subtitle">Type a hypothesis to get a real z-test spec, guardrails, and a decision rule — committed before the test runs.</p>', unsafe_allow_html=True)

imported = st.session_state.pop("imported_hypothesis", None)
if imported:
    style.flow_banner(f"Imported hypothesis from Lifecycle Architect: {imported}")

with st.container(border=True):
    st.markdown("### Hypothesis")
    hyp = st.text_area("Hypothesis", value=imported or
                        "Sending a day-28 \"reorder in 30 seconds\" WhatsApp nudge (no discount) to "
                        "at-risk customers will lift M2 repeat-purchase rate.")
    c1, c2, c3 = st.columns(3)
    with c1:
        baseline = st.text_input("Baseline rate", "18%")
    with c2:
        mde = st.text_input("Minimum detectable effect", "+3pp")
    with c3:
        traffic = st.text_input("Daily eligible traffic", "640 customers/day")
    run = st.button("Generate spec →", type="primary")

if run:
    with st.spinner("Computing the z-test spec, then running 5 AI agents on guardrails and risk…"):
        st.session_state["experiment_result"] = data.call_workflow(
            "experiment_designer",
            {"brand_id": st.session_state.get("brand_id"), "hypothesis": hyp,
             "baseline": baseline, "mde": mde, "traffic": traffic},
        )
    # n8n's Memory: Write already persisted this spec to Supabase before responding —
    # grab its id (matched on hypothesis text) so Results & Learnings can grade it later.
    recent = data.get_experiments(st.session_state.get("brand_id"))
    if recent and recent[0].get("hypothesis") == hyp:
        st.session_state["latest_experiment_id"] = recent[0]["id"]

result = st.session_state.get("experiment_result")
if result:
    spec = result["spec"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Per arm", f"{spec['sample_size_per_arm']:,}")
    m2.metric("Est. duration", f"{spec['duration_days']} days")
    m3.metric("Confidence / power", f"{int(spec['confidence']*100)}% / {int(spec['power']*100)}%")

    st.markdown("### Full analysis dashboard")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.power_curve(spec["power_curve"]), use_container_width=True)
        st.plotly_chart(charts.duration_timeline(spec["duration_days"]), use_container_width=True)
    with c2:
        st.plotly_chart(charts.sample_size_tradeoff(spec["power_curve"]), use_container_width=True)
        st.plotly_chart(charts.historical_outcomes(result["historical_outcomes"]), use_container_width=True)

    st.markdown("### AI analysis")
    n = result["narrative"]
    style.agent_card("Risk assessment", n["risk_assessment"])
    style.agent_card("Similar-experiment analyst", n["similar_experiment_analyst"])
    style.agent_card("Narrative synthesis", f"**{n['synthesis']}**")

    st.markdown("### Guardrail metrics")
    for g in result["guardrails"]:
        with st.container(border=True):
            st.markdown(f"**{g['metric']}**")
            st.caption(g["why"])
            gc1, gc2 = st.columns(2)
            with gc1:
                style.zone(f"Safe zone: {g['safe_zone']}", "safe")
            with gc2:
                style.zone(f"Kill zone: {g['kill_zone']}", "kill")

    st.markdown("### Decision rule — committed pre-test")
    dr = result["decision_rule"]
    with st.container(border=True):
        for verdict, text in [("SHIP", dr["ship"]), ("EXTEND", dr["extend"]), ("KILL", dr["kill"])]:
            style.badge(verdict, style.VERDICT_COLOR[verdict])
            st.caption(text)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        style.flow_banner("Grade the real outcome against this decision rule once the test ships.")
        if st.button("Go to Results & Learnings →"):
            st.switch_page("pages/4_Results_Learnings.py")
    with col_b:
        style.export_pdf_button(result.get("pdf_url"))
else:
    style.empty_state("Enter a hypothesis above and generate a spec to see the full dashboard.")
