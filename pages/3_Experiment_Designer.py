import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Experiment Designer")
st.markdown('<p class="subtitle">Type a hypothesis to get a real z-test spec, guardrails, and a decision rule — committed before the test runs.</p>', unsafe_allow_html=True)

imported = st.session_state.pop("imported_hypothesis", None)
if imported:
    style.flow_banner(f"Imported hypothesis from Lifecycle Architect: {imported}")

# ── Horizontal control strip ────────────────────────────────────────────
# Card look comes from a real st.container(border=True), not a blanket
# CSS rule on every columns() row.
with st.container(border=True):
    sc1, sc2, sc3, sc4 = st.columns([1.3, 1, 1, 1.2])
    with sc1:
        brand_id = style.brand_selector(label="Scope Memory Context")
    with sc2:
        baseline = st.text_input("Baseline rate", "18%")
    with sc3:
        mde = st.text_input("Minimum detectable effect", "+3pp")
    with sc4:
        traffic = st.text_input("Daily eligible traffic", "640 customers/day")
    hyp = st.text_area("Hypothesis", value=imported or
                        "Sending a day-28 \"reorder in 30 seconds\" WhatsApp nudge (no discount) to "
                        "at-risk customers will lift M2 repeat-purchase rate.")

    missing = brand_id is None or not hyp.strip()
    run = st.button(
        "Generate spec →", type="primary", disabled=missing,
        help=("Select a brand first." if brand_id is None else "Enter a hypothesis first.") if missing else None,
    )

if run:
    with st.spinner("Computing the z-test spec, then running 5 AI agents on guardrails and risk…"):
        result_value = data.call_workflow(
            "experiment_designer",
            {"brand_id": brand_id, "hypothesis": hyp,
             "baseline": baseline, "mde": mde, "traffic": traffic},
        )
    style.remember_result("experiment_result", result_value, brand_id)
    # n8n's Memory: Write already persisted this spec to Supabase before responding —
    # grab its id (matched on hypothesis text) so Results & Learnings can grade it later.
    # get_experiments() is now cached (see data.py) so it doesn't hit Supabase on
    # every rerun — but that means it must be explicitly cleared here, or this
    # lookup could return a stale pre-insert list and never find the new row.
    data.get_experiments.clear()
    recent = data.get_experiments(brand_id)
    if recent and recent[0].get("hypothesis") == hyp:
        st.session_state["latest_experiment_id"] = recent[0]["id"]

style.stale_guard("experiment_result", brand_id)
result = st.session_state.get("experiment_result")
if result:
    spec = result["spec"]

    st.markdown("### Executive scorecard")
    style.kpi_row([
        {"label": "Sample size per arm", "value": f"{spec['sample_size_per_arm']:,}"},
        {"label": "Est. duration", "value": f"{spec['duration_days']} days"},
        {"label": "Confidence / power", "value": f"{int(spec['confidence']*100)}% / {int(spec['power']*100)}%"},
    ])

    st.markdown("### Full analysis dashboard")
    # Duration was its own block-fill chart before — dropped, since it's
    # already a plain number in the scorecard above (Est. duration) and
    # doesn't need a second, slower-to-read visual for the same fact.
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.power_curve(spec["power_curve"]), use_container_width=True)
    with c2:
        st.plotly_chart(charts.sample_size_tradeoff(spec["power_curve"]), use_container_width=True)
        if result["historical_outcomes"]:
            st.plotly_chart(charts.historical_outcomes(result["historical_outcomes"]), use_container_width=True)
        else:
            style.status_pill("✓ No comparable past experiments — first test for this brand", "muted")

    # ── Consolidated AI summary ─────────────────────────────────────────
    st.markdown("### AI analysis")
    n = result["narrative"]
    ai1, ai2 = st.columns([3, 2])
    with ai1:
        style.agent_card("Risk & rationale", f"**{n['synthesis']}**{n['risk_assessment']}")
    with ai2:
        style.agent_card("Historical precedent", n["similar_experiment_analyst"])

    st.markdown("### Guardrail metrics")
    guardrails = result["guardrails"]
    gcols = st.columns(min(len(guardrails), 3)) if guardrails else []
    for i, g in enumerate(guardrails):
        with gcols[i % len(gcols)]:
            with st.container(border=True):
                st.markdown(f"**{g['metric']}**")
                st.caption(g["why"])
                style.zone(f"Safe: {g['safe_zone']}", "safe")
                style.zone(f"Kill: {g['kill_zone']}", "kill")

    st.markdown("### Decision rule — committed pre-test")
    dr = result["decision_rule"]
    with st.container(border=True):
        for verdict, text in [("SHIP", dr["ship"]), ("EXTEND", dr["extend"]), ("KILL", dr["kill"])]:
            style.badge(verdict, style.VERDICT_COLOR[verdict])
            st.caption(text)

    style.next_action(
        "Grade the real outcome against this decision rule once the test ships.",
        button_label="Go to Results & Learnings →",
        button_page="pages/4_Results_Learnings.py",
        pdf_url=result.get("pdf_url"),
    )
else:
    style.empty_state("Enter a hypothesis above and generate a spec to see the full dashboard.")
