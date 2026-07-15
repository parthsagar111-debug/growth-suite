import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Funnel diagnostics")
st.markdown('<p class="subtitle">Upload funnel metrics or order history to get a diagnosed leak, a full analysis dashboard, and ranked plays.</p>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### Input")
    mode = st.radio("Data source", ["Sample data (demo)", "Metrics snapshot", "Order-level data"], horizontal=True)
    c1, c2 = st.columns(2)
    with c1:
        segment = st.selectbox("Segment", ["All channels", "Paid social", "Organic", "Email"])
    with c2:
        period = st.selectbox("Period", ["Last 90 days", "Last 6 months", "Last 12 months"])
    run = st.button("Run diagnosis →", type="primary")

if run:
    with st.spinner("Running the deterministic engine, then 7 AI agents in sequence…"):
        st.session_state["funnel_result"] = data.call_workflow(
            "funnel_diagnostics",
            {"brand_id": st.session_state.get("brand_id"), "mode": mode, "segment": segment, "period": period},
        )

result = st.session_state.get("funnel_result")
if result:
    stats = result["computed_stats"]

    st.markdown("### Deterministic snapshot")
    m1, m2, m3 = st.columns(3)
    m1.metric("M1 → M2 retention", f"{stats['m1_m2_retention']*100:.0f}%")
    m2.metric("Discount-dependent repeats", f"{stats['discount_dependency']*100:.0f}%")
    m3.metric("Median days to 2nd order", f"{stats['time_to_2nd_order_median_days']}")

    st.markdown("### Full analysis dashboard")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.funnel_dropoff(stats["funnel_stages"]), use_container_width=True)
        st.plotly_chart(charts.trend_with_anomalies(stats["trend"]), use_container_width=True)
        st.plotly_chart(charts.discount_dependency(stats["discount_dependency"]), use_container_width=True)
        st.plotly_chart(charts.benchmark_bar(stats["benchmark"]), use_container_width=True)
    with c2:
        st.plotly_chart(charts.cohort_heatmap(stats["cohorts"]), use_container_width=True)
        st.plotly_chart(charts.segment_comparison(stats["segments"]), use_container_width=True)
        st.plotly_chart(charts.time_to_second_order(stats["time_to_2nd_order_median_days"]), use_container_width=True)

    st.markdown("### AI analysis — five lenses")
    n = result["narrative"]
    style.agent_card("Interpreter", n["interpreter"])
    style.agent_card("Anomaly explainer", n["anomaly_explainer"])
    style.agent_card("Root cause", n["root_cause"])
    style.agent_card("Benchmark commentary", n["benchmark_commentary"])
    style.agent_card("Segment insight", n["segment_insight"])
    style.agent_card("Narrative synthesis", f"**{n['synthesis']}**")

    st.markdown("### Ranked plays")
    for i, play in enumerate(result["ranked_plays"], start=1):
        with st.container(border=True):
            style.badge(f"{play['impact']} impact", style.IMPACT_COLOR.get(play["impact"], "accent"))
            st.markdown(f"**{i}. {play['title']}**")
            st.caption(play["rationale"])

    col_a, col_b = st.columns([3, 1])
    with col_a:
        style.flow_banner("Ground the next tool in this brand's real M1→M2 cliff instead of a category guess.")
        if st.button("Send diagnosis to Lifecycle Architect →"):
            st.session_state["imported_diagnosis"] = result
            st.switch_page("pages/2_Lifecycle_Architect.py")
    with col_b:
        style.export_pdf_button(result.get("pdf_url"))
else:
    style.empty_state("Run a diagnosis above to see the full dashboard.")
