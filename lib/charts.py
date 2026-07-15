"""Plotly chart builders. Every function returns a go.Figure so pages
can just st.plotly_chart(fn(...), use_container_width=True).

Corporate palette: Indigo (primary), Emerald (positive), Slate (neutral),
Crimson (negative/drop-off). Amber is a fifth accent reserved for the
three-state SHIP/EXTEND/KILL vocabulary."""
import plotly.graph_objects as go

ACCENT, TEAL, CORAL, AMBER, GREEN, RED, MUTED = (
    "#4f46e5", "#059669", "#dc2626", "#b45309", "#059669", "#dc2626", "#64748b")

GRIDLINE = "#e2e8f0"

BASE_LAYOUT = dict(
    margin=dict(l=40, r=20, t=30, b=40), height=320,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Helvetica, Arial, sans-serif", size=12, color="#0f172a"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def _apply(fig, title=""):
    """Applies the shared layout, plus the 'clean horizontal grid lines
    only' rule: no vertical gridlines, no chart-junk axis lines, no
    marker borders — a SaaS dashboard look rather than a default Plotly
    figure with every gridline switched on."""
    fig.update_layout(**BASE_LAYOUT, title=dict(text=title, font=dict(size=13, color="#334155")))
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, gridwidth=1, zeroline=False, showline=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False)
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    return fig


def detect_anomalies(trend):
    """Points more than 25% off the mean — shared by the chart and by
    pages that just need the count for a compact status pill instead of
    rendering the whole chart's flagged-point logic twice."""
    y = [t["value"] for t in trend]
    if not y:
        return []
    mean = sum(y) / len(y)
    return [t for t in trend if abs(t["value"] - mean) > mean * 0.25]


# ── Funnel Diagnostics ───────────────────────────────────────────────
def funnel_dropoff(stages):
    fig = go.Figure(go.Funnel(
        y=[s["stage"] for s in stages], x=[s["value"] for s in stages],
        marker=dict(color=[ACCENT] * len(stages), line=dict(width=0))))
    return _apply(fig, "Funnel drop-off by stage")


def cohort_heatmap(cohorts):
    months = [c["cohort"] for c in cohorts]
    cols = ["m1", "m2", "m3", "m4"]
    z = [[c[k] for k in cols] for c in cohorts]
    fig = go.Figure(go.Heatmap(
        z=z, x=["M1", "M2", "M3", "M4"], y=months,
        colorscale=[[0, "#fef2f2"], [0.5, "#fde68a"], [1, "#059669"]],
        text=[[f"{v}%" for v in row] for row in z], texttemplate="%{text}",
        xgap=3, ygap=3))
    return _apply(fig, "Cohort retention heatmap")


def trend_with_anomalies(trend):
    x = [t["period"] for t in trend]
    y = [t["value"] for t in trend]
    flagged = detect_anomalies(trend)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=ACCENT), name="Metric"))
    if flagged:
        fig.add_trace(go.Scatter(x=[t["period"] for t in flagged], y=[t["value"] for t in flagged], mode="markers",
                                  marker=dict(color=CORAL, size=11, symbol="circle-open", line=dict(width=2)),
                                  name="Flagged"))
    return _apply(fig, "Trend with flagged anomalies")


def segment_comparison(segments):
    fig = go.Figure(go.Bar(
        x=[s["segment"] for s in segments], y=[s["value"] * 100 for s in segments],
        marker_color=[TEAL, ACCENT, AMBER][: len(segments)]))
    fig.update_yaxes(title="M1→M2 retention %")
    return _apply(fig, "Segment comparison")


def discount_dependency(dependency_pct):
    fig = go.Figure(go.Pie(
        labels=["Discount-dependent repeats", "Full-price repeats"],
        values=[dependency_pct * 100, (1 - dependency_pct) * 100],
        marker=dict(colors=[CORAL, TEAL], line=dict(width=0)), hole=0.55))
    return _apply(fig, "Discount dependency")


def time_to_second_order(median_days):
    import random
    random.seed(7)
    samples = [max(1, int(random.gauss(median_days, 12))) for _ in range(120)]
    fig = go.Figure(go.Histogram(x=samples, marker_color=ACCENT, nbinsx=20))
    fig.add_vline(x=median_days, line_dash="dash", line_color=CORAL,
                  annotation_text=f"median {median_days}d")
    return _apply(fig, "Time to second order")


def benchmark_bar(benchmark):
    fig = go.Figure(go.Bar(
        x=["You", "Category typical"], y=[benchmark["you"], benchmark["category_typical"]],
        marker_color=[ACCENT, MUTED]))
    fig.update_yaxes(title="M1→M2 retention %")
    return _apply(fig, "Category benchmark")


# ── Lifecycle Architect ──────────────────────────────────────────────
def journey_timeline(stages):
    fig = go.Figure()
    days = [s["day"] for s in stages]
    positions = ["top center" if i % 2 == 0 else "bottom center" for i in range(len(days))]
    fig.add_trace(go.Scatter(x=days, y=[1] * len(days), mode="lines",
                              line=dict(color=MUTED, dash="dot"), showlegend=False))
    for i, (d, s) in enumerate(zip(days, stages)):
        fig.add_trace(go.Scatter(
            x=[d], y=[1], mode="markers+text", showlegend=False,
            marker=dict(size=20, color=ACCENT),
            text=[s["name"]], textposition=positions[i],
            textfont=dict(size=11),
        ))
    fig.update_yaxes(visible=False, range=[0.3, 1.7])
    fig.update_xaxes(title="Day")
    return _apply(fig, "Journey timeline")


def engagement_funnel(funnel):
    fig = go.Figure(go.Funnel(
        y=[f["stage"] for f in funnel], x=[f["value"] for f in funnel],
        marker=dict(color=[TEAL] * len(funnel), line=dict(width=0))))
    return _apply(fig, "Expected engagement funnel")


def tone_curve(stages):
    days = [s["day"] for s in stages]
    warmth = [s["tone_score"]["warmth"] for s in stages]
    urgency = [s["tone_score"]["urgency"] for s in stages]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=warmth, mode="lines+markers", name="Warmth", line=dict(color=TEAL)))
    fig.add_trace(go.Scatter(x=days, y=urgency, mode="lines+markers", name="Urgency", line=dict(color=CORAL)))
    fig.update_yaxes(title="Score", range=[0, 1])
    fig.update_xaxes(title="Day")
    return _apply(fig, "Tone curve across the journey")


def cadence_benchmark(cadence):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cadence["you"], y=["You"] * len(cadence["you"]),
                              mode="markers", marker=dict(size=14, color=ACCENT), name="You"))
    fig.add_trace(go.Scatter(x=cadence["category_typical"], y=["Category typical"] * len(cadence["category_typical"]),
                              mode="markers", marker=dict(size=14, color=MUTED), name="Category typical"))
    fig.update_xaxes(title="Day")
    return _apply(fig, "Cadence vs category benchmark")


# ── Experiment Designer ──────────────────────────────────────────────
def power_curve(curve):
    fig = go.Figure(go.Scatter(
        x=[c["mde"] for c in curve], y=[c["n"] for c in curve],
        mode="lines+markers", line=dict(color=ACCENT)))
    fig.update_xaxes(title="Minimum detectable effect (pp)")
    fig.update_yaxes(title="Sample size per arm", type="log")
    return _apply(fig, "Power curve")


def sample_size_tradeoff(power_curve):
    mdes = [c["mde"] for c in power_curve]
    n80_vals = [c["n"] for c in power_curve]
    n90_vals = [int(v * 1.34) for v in n80_vals]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mdes, y=n80_vals, mode="lines+markers", name="80% power", line=dict(color=ACCENT)))
    fig.add_trace(go.Scatter(x=mdes, y=n90_vals, mode="lines+markers", name="90% power", line=dict(color=AMBER)))
    fig.update_yaxes(title="Sample size per arm", type="log")
    fig.update_xaxes(title="MDE (pp)")
    return _apply(fig, "Sample size vs power tradeoff")


def duration_timeline(duration_days):
    fig = go.Figure(go.Bar(x=[duration_days], y=["Test duration"], orientation="h", marker_color=TEAL))
    fig.update_xaxes(title="Days")
    return _apply(fig, "Estimated test duration")


def guardrail_dashboard(guardrails):
    fig = go.Figure()
    for i, g in enumerate(guardrails):
        fig.add_trace(go.Bar(x=[g["metric"]], y=[1], marker_color=TEAL, showlegend=False,
                              hovertext=f'Safe: {g["safe_zone"]} · Kill: {g["kill_zone"]}'))
    fig.update_yaxes(visible=False)
    return _apply(fig, "Guardrail safe zones (hover for thresholds)")


def historical_outcomes(history):
    colors = {"SHIP": GREEN, "KILL": RED, "EXTEND": AMBER}
    fig = go.Figure(go.Bar(
        x=[h["experiment"] for h in history], y=[h["lift_pp"] for h in history],
        marker_color=[colors.get(h["verdict"], MUTED) for h in history]))
    fig.update_yaxes(title="Lift (pp)")
    return _apply(fig, "Historical experiment outcomes")


# ── Results & Learnings ──────────────────────────────────────────────
def win_rate_over_time(history):
    dates = [h["date"] for h in history]
    win_rate = []
    ship_count = 0
    for i, h in enumerate(history, start=1):
        if h["verdict"] == "SHIP":
            ship_count += 1
        win_rate.append(round(ship_count / i * 100))
    fig = go.Figure(go.Scatter(x=dates, y=win_rate, mode="lines+markers", line=dict(color=ACCENT)))
    fig.update_yaxes(title="Cumulative win rate %")
    return _apply(fig, "Win rate over time")


def verdict_distribution(dist):
    colors = {"SHIP": GREEN, "KILL": RED, "EXTEND": AMBER}
    labels = [k for k, v in dist.items() if v > 0]
    values = [v for v in dist.values() if v > 0]
    fig = go.Figure(go.Pie(labels=labels, values=values,
                            marker=dict(colors=[colors[l] for l in labels], line=dict(width=0)), hole=0.55))
    return _apply(fig, "Verdict distribution")


def cumulative_impact(impact_list):
    running = []
    total = 0
    for v in impact_list:
        total += v
        running.append(total)
    fig = go.Figure(go.Bar(x=[f"Exp {i+1}" for i in range(len(running))], y=running, marker_color=TEAL))
    fig.update_yaxes(title="Cumulative lift (pp)")
    return _apply(fig, "Cumulative impact")


def theme_cluster(themes):
    fig = go.Figure(go.Bar(
        x=[t["count"] for t in themes], y=[t["theme"] for t in themes],
        orientation="h", marker_color=ACCENT))
    fig.update_xaxes(title="Occurrences")
    return _apply(fig, "Recurring learning themes")
