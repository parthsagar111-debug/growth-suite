"""
Turns real input — an uploaded order-level CSV, or a manually entered
metrics snapshot — into the same `computed_stats` shape the rest of the
app already expects (see lib/data.py's SAMPLE_RESULTS for the reference
shape). This is what Funnel Diagnostics' file upload was missing: the
mode selector existed, but nothing actually parsed a file or computed
real numbers from it — n8n's Deterministic Analytics Engine always
returned the same fixture regardless of input.

Two entry points:
  - compute_stats_from_orders(df)   for uploaded order-level CSVs
  - compute_stats_from_snapshot(v)  for the manual metrics-snapshot form

Both are deterministic — no AI involved, consistent with the rest of
the app's design principle that every number is computed, not guessed.
"""
import io
import statistics
import pandas as pd

ORDER_CSV_COLUMNS = ["customer_id", "order_date", "order_number", "channel", "revenue", "discount_applied"]


def sample_order_csv_bytes() -> bytes:
    """A realistic-looking order-level template, cohorted across three
    months so the cohort heatmap and trend chart have something to show."""
    rows = []
    channels = ["Paid social", "Organic", "Email"]
    cohort_months = ["2026-01", "2026-02", "2026-03"]
    cid = 1000
    for mi, month in enumerate(cohort_months):
        n_customers = 40
        for i in range(n_customers):
            channel = channels[i % 3]
            first_date = f"{month}-{(i % 27) + 1:02d}"
            cid += 1
            rows.append([cid, first_date, 1, channel, round(38 + (i % 7) * 3.5, 2), False])
            # Roughly matches the app's ~18% M1->M2 retention, lower for paid social.
            repeat_odds = {"Paid social": 5, "Organic": 4, "Email": 4}[channel]
            if i % repeat_odds == 0:
                second_month = min(mi + 1, len(cohort_months) - 1)
                second_date = f"{cohort_months[second_month]}-{((i + 12) % 27) + 1:02d}"
                discount = (i % 2 == 0)
                rows.append([cid, second_date, 2, channel, round(35 + (i % 5) * 3, 2), discount])
                if i % (repeat_odds * 2) == 0 and second_month < len(cohort_months) - 1:
                    third_date = f"{cohort_months[second_month + 1]}-{((i + 5) % 27) + 1:02d}"
                    rows.append([cid, third_date, 3, channel, round(35 + (i % 4) * 3, 2), i % 2 == 0])
    df = pd.DataFrame(rows, columns=ORDER_CSV_COLUMNS)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def _validate_orders(df: pd.DataFrame):
    missing = [c for c in ORDER_CSV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}. "
                          f"Expected: {', '.join(ORDER_CSV_COLUMNS)}")


def compute_stats_from_orders(df: pd.DataFrame) -> dict:
    """Real cohort/retention/discount math from raw order rows. Upper-funnel
    steps (Visit, Add to cart, Checkout) aren't derivable from order data
    alone — those come from web analytics, not a transactions export — so
    the funnel chart in this mode only shows Purchase -> Repeat (M2)."""
    _validate_orders(df)
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["order_number"] = df["order_number"].astype(int)
    df["discount_applied"] = df["discount_applied"].astype(bool)
    df["cohort_month"] = df["order_date"].dt.to_period("M")

    first_orders = df[df["order_number"] == 1]
    second_orders = df[df["order_number"] == 2]
    n_first = first_orders["customer_id"].nunique()
    n_second = second_orders["customer_id"].nunique()
    m1_m2_retention = round(n_second / n_first, 4) if n_first else 0.0

    repeat_orders = df[df["order_number"] >= 2]
    discount_dependency = (round(repeat_orders["discount_applied"].mean(), 4)
                            if len(repeat_orders) else 0.0)

    merged = first_orders[["customer_id", "order_date"]].merge(
        second_orders[["customer_id", "order_date"]], on="customer_id", suffixes=("_1", "_2"))
    if len(merged):
        days = (merged["order_date_2"] - merged["order_date_1"]).dt.days
        time_to_2nd_order_median_days = int(statistics.median(days))
    else:
        time_to_2nd_order_median_days = 0

    cohorts = []
    for month, group in sorted(first_orders.groupby("cohort_month")):
        cohort_customers = set(group["customer_id"])
        size = len(cohort_customers)
        if size == 0:
            continue
        row = {"cohort": month.strftime("%b")}
        row["m1"] = 100
        for k in (2, 3, 4):
            n_at_k = df[(df["order_number"] == k) & (df["customer_id"].isin(cohort_customers))]["customer_id"].nunique()
            row[f"m{k}"] = round(100 * n_at_k / size) if size else 0
        cohorts.append(row)
    cohorts = cohorts[-3:]  # most recent 3 cohorts, matching the demo shape

    df["week"] = df["order_date"].dt.to_period("W")
    trend = []
    for i, (week, group) in enumerate(sorted(df.groupby("week"))[-8:], start=1):
        repeat_share = round(100 * (group["order_number"] > 1).mean())
        trend.append({"period": f"W{i}", "value": repeat_share})

    segments = []
    for channel, group in first_orders.groupby("channel"):
        chan_customers = set(group["customer_id"])
        chan_second = df[(df["order_number"] == 2) & (df["customer_id"].isin(chan_customers))]["customer_id"].nunique()
        segments.append({"segment": channel, "value": round(chan_second / len(chan_customers), 4) if chan_customers else 0.0})

    funnel_stages = [
        {"stage": "Purchase", "value": int(n_first)},
        {"stage": "Repeat (M2)", "value": int(n_second)},
    ]

    return {
        "m1_m2_retention": m1_m2_retention,
        "discount_dependency": discount_dependency,
        "time_to_2nd_order_median_days": time_to_2nd_order_median_days,
        "cohorts": cohorts,
        "trend": trend,
        "segments": segments,
        "funnel_stages": funnel_stages,
        "benchmark": {"you": round(m1_m2_retention * 100), "category_typical": 29},
        "_funnel_note": "Visit / Add to cart / Checkout aren't in an order-level export — "
                         "this funnel only shows what the upload can prove.",
    }


def compute_stats_from_snapshot(v: dict) -> dict:
    """Build computed_stats from a handful of headline numbers a marketer
    already has on hand. Cohort and weekly-trend detail can't be derived
    from a snapshot, so both are flat estimates built off the headline
    retention rate rather than fabricated detail."""
    m1_m2 = v["m1_m2_retention"] / 100
    m2_flat = round(v["m1_m2_retention"])
    cohorts = [{"cohort": "All customers", "m1": 100, "m2": m2_flat,
                "m3": round(m2_flat * 0.75), "m4": round(m2_flat * 0.6)}]
    trend = [{"period": f"W{i}", "value": m2_flat} for i in range(1, 9)]
    segments = [
        {"segment": "Paid social", "value": round(v["seg_paid_social"] / 100, 4)},
        {"segment": "Organic", "value": round(v["seg_organic"] / 100, 4)},
        {"segment": "Email", "value": round(v["seg_email"] / 100, 4)},
    ]
    funnel_stages = [
        {"stage": "Visit", "value": v["fn_visit"]},
        {"stage": "Add to cart", "value": v["fn_cart"]},
        {"stage": "Checkout", "value": v["fn_checkout"]},
        {"stage": "Purchase", "value": v["fn_purchase"]},
        {"stage": "Repeat (M2)", "value": v["fn_repeat"]},
    ]
    return {
        "m1_m2_retention": round(m1_m2, 4),
        "discount_dependency": round(v["discount_dependency"] / 100, 4),
        "time_to_2nd_order_median_days": int(v["days_to_2nd"]),
        "cohorts": cohorts,
        "trend": trend,
        "segments": segments,
        "funnel_stages": funnel_stages,
        "benchmark": {"you": round(v["m1_m2_retention"]), "category_typical": int(v["benchmark"])},
        "_cohort_note": "Built from your headline numbers, not a real cohort breakdown — "
                         "upload order-level data for the real thing.",
    }
