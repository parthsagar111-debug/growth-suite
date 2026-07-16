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

MODE_OPTIONS = ["Sample Demo", "Metrics Snapshot", "Order-Level"]

# ── Connected control strip + upload drawer ─────────────────────────────
# One real st.container(border=True) — brand/workspace, data-source mode,
# and the page's own filters share a top row; the Run button gets its own
# row right below (still inside the same card) rather than a 5th column,
# because a 5-column row this packed reliably wraps at typical viewport
# widths — Streamlit gives each stColumn a hard minimum width, and once
# the row's total minimum exceeds the container, the last column drops
# to its own full-width line instead of shrinking. Two rows avoids that.
# The mode toggle also gets a deliberately wide first column: unlike the
# mockup's plain flex row (which just sizes to content), st.columns()
# uses fixed proportional widths regardless of what's inside them, so a
# 3-option segmented control needs real column width or its own pills
# wrap onto separate lines — that's what the "Data Source Mode" three
# stacked buttons in the live screenshot actually was.
with st.container(border=True):
    sc1, sc2, sc3, sc4 = st.columns([2.2, 1.3, 1, 1])
    with sc1:
        if hasattr(st, "segmented_control"):
            mode = st.segmented_control("Data Source Mode", MODE_OPTIONS, default=MODE_OPTIONS[0])
            if mode is None:
                mode = MODE_OPTIONS[0]
        else:
            mode = st.selectbox("Data Source Mode", MODE_OPTIONS)
    is_upload_mode = mode != "Sample Demo"
    has_saved_ghost = st.session_state.get("ghost_brand_id") is not None
    locked = is_upload_mode and not has_saved_ghost
    with sc2:
        if locked:
            style.brand_selector(label="Scope Memory Context", locked=True)
            scoped_brand_id = None
        else:
            scoped_brand_id = style.brand_selector(label="Scope Memory Context")
    with sc3:
        segment = st.selectbox("Segment", ["All channels", "Paid social", "Organic", "Email"])
    with sc4:
        period = st.selectbox("Period", ["Last 90 days", "Last 6 months", "Last 12 months"])

    # Brand/workspace is the only piece of the Run button's validity known
    # this early — whether an upload mode has a parsed file yet is only
    # known further down, after the drawer renders, so that half of the
    # guard is checked post-click instead of via a pre-disabled state.
    missing_brand = not locked and scoped_brand_id is None
    bc1, bc2 = st.columns([3, 1])
    with bc2:
        run = st.button(
            "Run diagnosis →", type="primary", disabled=missing_brand,
            help="Select a brand first." if missing_brand else None,
            use_container_width=True,
        )

    computed_stats = None

    if mode == "Order-Level":
        st.markdown('<div class="gs-drawer-seam"></div>', unsafe_allow_html=True)
        dc1, dc2, dc3 = st.columns([1.4, 1.4, 2])
        with dc1:
            st.download_button("📥 Download CSV Template", ingest.sample_order_csv_bytes(),
                                file_name="order_level_template.csv", mime="text/csv", use_container_width=True)
        with dc2:
            uploaded = st.file_uploader("Upload order-level CSV", type=["csv"], label_visibility="collapsed")
        with dc3:
            st.caption("Columns: " + ", ".join(ingest.ORDER_CSV_COLUMNS))
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                computed_stats = ingest.compute_stats_from_orders(df)
                style.status_pill(f"✓ Parsed {len(df):,} rows — real numbers, not demo data", "ok")
            except Exception as e:
                st.error(f"Couldn't parse that file: {e}")

    elif mode == "Metrics Snapshot":
        st.markdown('<div class="gs-drawer-seam"></div>', unsafe_allow_html=True)
        st.caption("Enter the headline numbers you already have — no file needed.")
        nc1, nc2, nc3 = st.columns(3)
        with nc1:
            snap_m1m2 = st.number_input("M1→M2 retention %", value=18.0, step=0.5)
            snap_discount = st.number_input("Discount-dependent repeats %", value=41.0, step=0.5)
        with nc2:
            snap_days = st.number_input("Median days to 2nd order", value=34, step=1)
            snap_benchmark = st.number_input("Category benchmark %", value=29.0, step=0.5)
        with nc3:
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

if run:
    if mode == "Order-Level" and computed_stats is None:
        st.error("Upload and parse a CSV before running diagnosis.")
    else:
        mode_key = {"Sample Demo": "sample", "Metrics Snapshot": "metrics_snapshot",
                    "Order-Level": "order_level"}[mode]
        payload = {"brand_id": scoped_brand_id, "mode": mode_key, "segment": segment, "period": period}
        if computed_stats is not None:
            payload["computed_stats"] = computed_stats
        with st.spinner("Running the deterministic engine, then 7 AI agents in sequence…"):
            result_value = data.call_workflow("funnel_diagnostics", payload)
        style.remember_result("funnel_result", result_value, scoped_brand_id)
        st.session_state["funnel_is_ghost"] = locked

# State-bug guard: if the brand/workspace selection has changed since
# the cached result was produced, drop the stale result instead of
# silently showing one brand's dashboard under a different brand's name.
style.stale_guard("funnel_result", scoped_brand_id)
result = st.session_state.get("funnel_result")
if result:
    # ── Post-analysis workspace nudge ───────────────────────────────────
    if st.session_state.get("funnel_is_ghost") and not has_saved_ghost:
        style.workspace_save_nudge(default_name="My custom brand")

    stats = result["computed_stats"]

    st.markdown("### Executive scorecard")
    retention_gap = stats['m1_m2_retention'] * 100 - stats['benchmark']['category_typical']
    style.kpi_row([
        {"label": "M1 → M2 retention", "value": f"{stats['m1_m2_retention']*100:.0f}%",
         "delta": f"{abs(retention_gap):.0f}pp vs benchmark", "positive": retention_gap >= 0},
        {"label": "Discount-dependent repeats", "value": f"{stats['discount_dependency']*100:.0f}%"},
        {"label": "Median days to 2nd order", "value": f"{stats['time_to_2nd_order_median_days']}"},
    ])

    st.markdown("### Full analysis dashboard")
    if stats.get("_funnel_note"):
        st.caption(stats["_funnel_note"])
    if stats.get("_cohort_note"):
        st.caption(stats["_cohort_note"])
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.funnel_dropoff(stats["funnel_stages"]), use_container_width=True)
        anomalies = charts.detect_anomalies(stats["trend"])
        st.plotly_chart(charts.trend_with_anomalies(stats["trend"]), use_container_width=True)
        if anomalies:
            style.status_pill(f"⚠ {len(anomalies)} anomaly point(s) flagged", "warn")
        else:
            style.status_pill("✓ 0 anomalies flagged", "ok")
        st.plotly_chart(charts.discount_dependency(stats["discount_dependency"]), use_container_width=True)
        st.plotly_chart(charts.benchmark_bar(stats["benchmark"]), use_container_width=True)
    with c2:
        st.plotly_chart(charts.cohort_heatmap(stats["cohorts"]), use_container_width=True)
        st.plotly_chart(charts.segment_comparison(stats["segments"]), use_container_width=True)
        st.plotly_chart(charts.time_to_second_order(stats["time_to_2nd_order_median_days"]), use_container_width=True)

    # ── Consolidated AI summary ─────────────────────────────────────────
    # Five separate agent-label headers collapsed into two dense reading
    # panes instead: what's broken, and what the numbers around it say.
    st.markdown("### AI analysis")
    n = result["narrative"]
    ai1, ai2 = st.columns([3, 2])
    with ai1:
        style.agent_card("Primary funnel leak", f"**{n['synthesis']}**{n['root_cause']}")
    with ai2:
        cohort_summary = f"{n['benchmark_commentary']} {n['segment_insight']}"
        if anomalies:
            cohort_summary += f" {n['anomaly_explainer']}"
        style.agent_card("Cohort analytics summary", cohort_summary)

    st.markdown("### Ranked plays")
    if result["ranked_plays"]:
        for i, play in enumerate(result["ranked_plays"], start=1):
            with st.container(border=True):
                style.badge(f"{play['impact']} impact", style.IMPACT_COLOR.get(play["impact"], "accent"))
                st.markdown(f"**{i}. {play['title']}**")
                st.caption(play["rationale"])
    else:
        style.status_pill("✓ No plays generated yet", "muted")

    style.next_action(
        "Ground the next tool in this brand's real M1→M2 cliff instead of a category guess.",
        button_label="Send diagnosis to Lifecycle Architect →",
        button_page="pages/2_Lifecycle_Architect.py",
        button_state=("imported_diagnosis", result),
        pdf_url=result.get("pdf_url"),
    )
else:
    style.empty_state("Run a diagnosis above to see the full dashboard.")
