import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Results & learnings")
st.markdown('<p class="subtitle">Grade a shipped experiment against the decision rule it committed to, and keep a running log of what was learned.</p>', unsafe_allow_html=True)

# ── Horizontal control strip ────────────────────────────────────────────
st.markdown('<div class="gs-control-strip">', unsafe_allow_html=True)
sc1, _ = st.columns([1.3, 3])
with sc1:
    brand_id = style.brand_selector(label="Brand / workspace")
st.markdown('</div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### Grade an outcome")
    st.caption("This step is deliberately not AI — the verdict is computed by comparing your actual "
               "numbers against the thresholds already agreed to in Experiment Designer.")

    experiments = data.get_experiments(brand_id)
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
        style.status_pill("✓ No experiments for this brand yet — generate one in Experiment Designer first", "muted")

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
            style.status_pill("✓ Saved to this brand's memory", "ok")
        else:
            style.status_pill("⚠ Not saved — Supabase unreachable, session-only", "warn")

st.markdown("### Full analysis dashboard")
with st.spinner("Pulling this brand's experiment history and looking for patterns…"):
    result = data.call_workflow("results_learnings", {"brand_id": brand_id})

history = result["history"]
dist = result["verdict_distribution"]
total_graded = sum(dist.values())
win_rate = round(dist.get("SHIP", 0) / total_graded * 100) if total_graded else 0
cum_impact = result["cumulative_impact_pp"][-1] if result["cumulative_impact_pp"] else 0

st.markdown("### Executive scorecard")
m1, m2, m3 = st.columns(3)
m1.metric("Experiments graded", total_graded)
m2.metric("Win rate", f"{win_rate}%")
m3.metric("Cumulative lift", f"{cum_impact}pp")

c1, c2 = st.columns(2)
with c1:
    if history:
        st.plotly_chart(charts.win_rate_over_time(history), use_container_width=True)
        st.plotly_chart(charts.cumulative_impact(result["cumulative_impact_pp"]), use_container_width=True)
    else:
        style.status_pill("✓ No graded history yet for this brand", "muted")
with c2:
    if total_graded:
        st.plotly_chart(charts.verdict_distribution(dist), use_container_width=True)
    else:
        style.status_pill("✓ No verdicts to distribute yet", "muted")
    if result["themes"]:
        st.plotly_chart(charts.theme_cluster(result["themes"]), use_container_width=True)
    else:
        style.status_pill("✓ No recurring themes yet — need more graded experiments", "muted")

style.agent_card("Pattern recognition", result["narrative"]["pattern_recognition"])

st.markdown("### Learnings log")
if history:
    for h in history:
        with st.container(border=True):
            style.badge(h["verdict"], style.VERDICT_COLOR.get(h["verdict"], "accent"))
            st.caption(f"{h['date']} · {h['brand']} · lift {h['lift_pp']}pp")
else:
    style.empty_state("No graded experiments for this brand yet.")

style.next_action(
    "Loop back to a fresh diagnosis to keep the flywheel turning — every grade here sharpens the "
    "next Experiment Designer run's Similar-Experiment Analyst.",
    button_label="Start a new diagnosis →",
    button_page="pages/1_Funnel_Diagnostics.py",
    pdf_url=result.get("pdf_url"),
)
