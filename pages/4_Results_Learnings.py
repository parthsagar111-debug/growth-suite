import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Results & learnings")
st.markdown('<p class="subtitle">Grade a shipped experiment against the decision rule it committed to, and keep a running log of what was learned.</p>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### Grade an outcome")
    st.caption("This step is deliberately not AI — the verdict is computed by comparing your actual "
               "numbers against the thresholds already agreed to in Experiment Designer.")

    experiments = data.get_experiments(st.session_state.get("brand_id"))
    if experiments:
        ids = [e["id"] for e in experiments]
        labels = {e["id"]: f"{e['hypothesis'][:70]}{'…' if len(e['hypothesis']) > 70 else ''} · {str(e['created_at'])[:10]}"
                  for e in experiments}
        default_id = st.session_state.get("latest_experiment_id")
        default_index = ids.index(default_id) if default_id in ids else 0
        experiment_id = st.selectbox("Which experiment are you grading?", ids,
                                      index=default_index, format_func=lambda x: labels[x])
    else:
        experiment_id = None
        st.caption("No experiments found for this brand yet — generate one in Experiment Designer first.")

    c1, c2, c3 = st.columns(3)
    with c1:
        lift = st.number_input("Actual M2 lift (pp)", value=3.4, step=0.1)
    with c2:
        optout = st.number_input("Opt-out delta (pp)", value=0.3, step=0.1)
    with c3:
        support = st.number_input("Support ticket delta", value=0, step=1)
    grade = st.button("Grade this experiment →", type="primary", disabled=experiment_id is None)

if grade:
    if optout >= 1.5:
        verdict = "KILL"
        takeaway = (f"Opt-out rose {optout}pp, past the 1.5pp kill threshold, regardless of the {lift}pp lift — "
                    "the guardrail is doing its job. Treat this as message fatigue or copy risk, not proof "
                    "the mechanism itself failed.")
    elif lift >= 3.0:
        verdict = "SHIP"
        takeaway = (f"Lift of {lift}pp cleared the 3pp bar with opt-out at {optout}pp, well within tolerance — "
                    "the mechanism worked without a measurable downside. Worth extending the same pattern "
                    "to the next stage in the journey.")
    else:
        verdict = "EXTEND"
        takeaway = (f"Lift of {lift}pp is directionally positive but under the 3pp bar, with opt-out at "
                    f"{optout}pp. Not enough signal yet to call it either way — extend before deciding.")
    saved = data.save_experiment_result(experiment_id, lift, optout, support, verdict, takeaway)
    st.session_state["latest_verdict"] = (verdict, lift, optout, takeaway, saved)

if "latest_verdict" in st.session_state:
    verdict, lift, optout, takeaway, saved = st.session_state["latest_verdict"]
    with st.container(border=True):
        style.badge(verdict, style.VERDICT_COLOR[verdict])
        st.markdown(f"Graded deterministically: lift {lift}pp, opt-out delta {optout}pp against the "
                     "committed decision rule — no model involved in this call.")
        style.agent_card("Takeaway", takeaway)
        if saved:
            st.caption("Saved to this brand's memory — reflected in the dashboard below and available "
                       "to Experiment Designer's Similar-Experiment Analyst on future runs.")
        else:
            st.caption("Not saved — Supabase wasn't reachable, so this verdict only applies to this session.")

st.markdown("### Full analysis dashboard")
with st.spinner("Pulling this brand's experiment history and looking for patterns…"):
    result = data.call_workflow("results_learnings", {"brand_id": st.session_state.get("brand_id")})
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(charts.win_rate_over_time(result["history"]), use_container_width=True)
    st.plotly_chart(charts.cumulative_impact(result["cumulative_impact_pp"]), use_container_width=True)
with c2:
    st.plotly_chart(charts.verdict_distribution(result["verdict_distribution"]), use_container_width=True)
    st.plotly_chart(charts.theme_cluster(result["themes"]), use_container_width=True)

style.agent_card("Pattern recognition", result["narrative"]["pattern_recognition"])

col_a, col_b = st.columns([3, 1])
with col_b:
    style.export_pdf_button(result.get("pdf_url"))

st.markdown("### Learnings log")
if result["history"]:
    for h in result["history"]:
        with st.container(border=True):
            style.badge(h["verdict"], style.VERDICT_COLOR.get(h["verdict"], "accent"))
            st.caption(f"{h['date']} · {h['brand']} · lift {h['lift_pp']}pp")
else:
    style.empty_state("No graded experiments for this brand yet.")
