"""
Small presentation-layer helpers for turning computed_stats into the
shapes the Jinja dashboard templates render directly — funnel bar
widths, cohort heatmap cell colors, and the anomaly-detection rule the
original Streamlit app's lib/charts.py used for its status pill.

Charts themselves are a mix of plain CSS (funnel bars, cohort heatmap —
both render more crisply as real HTML/CSS than as a JS chart library
output, and it's one less thing to wire through HTMX swaps) and
Chart.js for the rest (donut, bar). No server-side chart image
rendering — everything here just prepares plain numbers/colors for the
template to draw.
"""


def detect_anomalies(trend: list) -> list:
    """Points more than 25% off the mean — same rule as the original
    Streamlit app's charts.py, ported verbatim."""
    y = [t["value"] for t in trend]
    if not y:
        return []
    mean = sum(y) / len(y)
    return [t for t in trend if abs(t["value"] - mean) > mean * 0.25]


_HEAT_STOPS = [
    (0.0, (254, 242, 242)),   # #fef2f2 — red-tinted low end
    (0.5, (253, 230, 138)),   # #fde68a — amber midpoint
    (1.0, (16, 185, 129)),    # #10b981 — emerald high end
]


def heat_color(value: float, vmax: float = 100.0) -> str:
    """Maps a 0..vmax value onto the same red→amber→emerald gradient the
    original Plotly cohort heatmap used, for a plain HTML/CSS table cell
    background instead of a chart image."""
    if vmax <= 0:
        return "#e2e8f0"
    t = max(0.0, min(1.0, value / vmax))
    for (t0, c0), (t1, c1) in zip(_HEAT_STOPS, _HEAT_STOPS[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            r = round(c0[0] + (c1[0] - c0[0]) * f)
            g = round(c0[1] + (c1[1] - c0[1]) * f)
            b = round(c0[2] + (c1[2] - c0[2]) * f)
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#e2e8f0"


def heat_text_color(value: float, vmax: float = 100.0) -> str:
    """Dark text reads fine on the pale red/amber end; the emerald high
    end is dark enough that dark text still passes, so this always
    returns the same slate — kept as a function in case that changes."""
    return "#1e293b"
