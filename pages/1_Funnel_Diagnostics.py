import pandas as pd
import streamlit as st
from lib import style, data, charts, ingest

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

    computed_stats = None
    upload_error = None

    if mode == "Order-level data":
        dc1, dc2 = st.columns([1, 2])
        with dc1:
            st.download_button("Download sample CSV", ingest.sample_order_csv_bytes(),
                                file_name="order_level_template.csv", mime="text/csv")
        with dc2:
            st.caption("Columns: " + ", ".join(ingest.ORDER_CSV_COLUMNS))
        uploaded = st.file_uploader("Upload order-level CSV", type=["csv"])
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                computed_stats = ingest.compute_stats_from_orders(df)
                st.success(f"Parsed {len(df):,} rows — real numbers below, not demo data.")
            except Exception as e:
                upload_error = str(e)
                st.error(f"Couldn't parse that file: {upload_error}")

    elif mode == "Metrics snapshot":
        st.caption("Enter the headline numbers you already have — no file needed.")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            snap_m1m2 = st.number_input("M1→M2 retention %", value=18.0, step=0.5)
            snap_discount = st.number_input("Discount-dependent repeats %", value=41.0, step=0.5)
        with sc2:
            snap_days = st.number_input("Median days to 2nd order", value=34, step=1)
            snap_benchmark = st.number_input("Category benchmark %", value=29.0, step=0.5)
        with sc3:
            snap_paid = st.number_input("Paid social retention %", value=14.0, step=0.5)
            snap_organic = st.number_input("Organic retention %", value=24.0, step=0.5)
            snap_email = st.number_input("Email retention %", value=21.0, step=0.5)
        with st.expander("Funnel stage volumes"):
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            fn_visit = fc1.number_input("Visits", value=100000, step=1000)
            fn_cart = fc2.number_input("Add to cart", value=32000, step=500)
            fn_checkout = fc3.number_input("Checkout", value=14000, step=500)
            fn_purchase = fc4.number_input("Purchases", value=9800, step=100)
            fn_repeat = fc5.number_input("Repeat (M2)", value=1764, step=50)
        computed_stats = ingest.compute_stats_from_snapshot({
            "m1_m2_retention": snap_m1m2, "discount_dependency": snap_discount,
            "days_to_2nd": snap_days, "benchmark": snap_benchmark,
            "seg_paid_social": snap_paid, "seg_organic": snap_organic, "seg_email": snap_email,
            "fn_visit": fn_visit, "fn_cart": fn_cart, "fn_checkout": fn_checkout,
            "fn_purchase": fn_purchase, "fn_repeat": fn_repeat,
        })

    c1, c2 = st.columns(2)
    with c1:
        segment = st.selectbox("Segment", ["All channels", "Paid social", "Organic", "Email"])
    with c2:
        period = st.selectbox("Period", ["Last 90 days", "Last 6 months", "Last 12 months"])
    run = st.button("Run diagnosis →", type="primary",
                     disabled=(mode == "Order-level data" and computed_stats is None))

if run:
    mode_key = {"Sample data (demo)": "sample", "Metrics snapshot": "metrics_snapshot",
                "Order-level data": "order_level"}[mode]
    payload = {"brand_id": st.session_state.get("brand_id"), "mode": mode_key,
               "segment": segment, "period": period}
    if computed_stats is not None:
        payload["computed_stats"] = computed_stats
    with st.spinner("Running the deterministic engine, then 7 AI agents in sequence…"):
        st.session_state["funnel_result"] = data.call_workflow("funnel_diagnostics", payload)

result = st.session_state.get("funnel_result")
if result:
    stats = result["computed_stats"]

    st.markdown("### Deterministic snapshot")
    m1, m2, m3 = st.columns(3)
    m1.metric("M1 → M2 retention", f"{stats['m1_m2_retention']*100:.0f}%")
    m2.metric("Discount-dependent repeats", f"{stats['discount_dependency']*100:.0f}%")
    m3.metric("Median days to 2nd order", f"{stats['time_to_2nd_order_median_days']}")

    st.markdown("### Full analysis dashboard")
    if stats.get("_funnel_note"):
        st.caption(stats["_funnel_note"])
    if stats.get("_cohort_note"):
        st.caption(stats["_cohort_note"])
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
