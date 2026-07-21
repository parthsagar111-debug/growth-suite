"""
Growth Suite — FastAPI + Jinja2 + HTMX build.

Why this project exists: the original Streamlit app (../) hit real,
repeated UI ceilings — Streamlit's per-column minimum-width enforcement
causing grid-wrap bugs, no real control over the DOM for pixel-level
polish, CSS fights against BaseWeb's internals for basic things like a
disabled select's fill color. This project reuses every piece of real
business logic from that app's lib/ folder (decision_tree.py,
ai_diagnostic.py, sample_scenario.py ported verbatim; data.py adapted
to drop the Streamlit dependency) and renders it with plain server-side
templates + HTMX for interactivity, so the frontend is finally just
real HTML/CSS with zero framework DOM fighting.

Build order (per explicit instruction): Overview + First Response
first, the remaining four tools after. Their nav links and routes
already exist below as "coming soon" stubs so the sidebar is complete
and nothing 404s while the rest of the suite is built out.
"""
import io
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lib import decision_tree, ingest, chart_helpers
from lib import data as data_lib
from lib.sample_scenario import SCENARIOS

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Growth Suite")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

ICONS = {
    "chat": '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.42-4.03 8-9 8-1.5 0-2.9-.32-4.13-.9L3 20l1.2-3.6A7.94 7.94 0 0 1 3 12c0-4.42 4.03-8 9-8s9 3.58 9 8Z"/></svg>',
    "funnel": '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h18l-7 8.5v6.2l-4 2.1v-8.3L3 4Z"/></svg>',
    "map": '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 20 3 17V4l6 3 6-3 6 3v13l-6-3-6 3Z"/><path d="M9 7v13M15 4v13"/></svg>',
    "flask": '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6M10 3v5.7L4.6 18a1.9 1.9 0 0 0 1.65 2.85h11.5A1.9 1.9 0 0 0 19.4 18L14 8.7V3"/><path d="M7.5 14.5h9"/></svg>',
    "bars": '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
}

TOOLS = [
    {"name": "First Response", "kind": "indigo", "step": "Step 1 · Triage", "icon_svg": ICONS["chat"],
     "desc": "Get asked why a metric is down? Run a branching diagnostic chat — no data upload — "
             "that tells you exactly what to investigate, in what order, before touching the rest "
             "of the suite.",
     "href": "/first-response"},
    {"name": "Funnel Diagnostics", "kind": "rose", "step": "Step 2 · Diagnose", "icon_svg": ICONS["funnel"],
     "desc": "Upload funnel snapshots or order-level transaction history to capture customer leaks, "
             "inspect drop-off anomalies, and get an AI narrative alongside the full analysis "
             "dashboard.",
     "href": "/funnel-diagnostics"},
    {"name": "Lifecycle Architect", "kind": "blue", "step": "Step 3 · Design", "icon_svg": ICONS["map"],
     "desc": "Map a targeted customer retention journey — a stage-by-stage WhatsApp sequence, "
             "custom-written and scored against AI tone benchmarks.",
     "href": "/lifecycle-architect"},
    {"name": "Experiment Designer", "kind": "amber", "step": "Step 4 · Test", "icon_svg": ICONS["flask"],
     "desc": "Construct a statistically defensible test: translate a hypothesis into a sample-size "
             "spec, power calculations, and guardrails that isolate variant risk.",
     "href": "/experiment-designer"},
    {"name": "Results & Learnings", "kind": "emerald", "step": "Step 5 · Learn", "icon_svg": ICONS["bars"],
     "desc": "Grade a shipped experiment against the decision rule it committed to, and log what "
             "was learned back into shared memory context.",
     "href": "/results-learnings"},
]

# Maps a decision_tree.py handoff target's "page" (a Streamlit page path,
# kept as-is in the ported data so it stays a single source of truth
# shared with the other project) to this project's own route.
PAGE_TO_ROUTE = {
    "pages/3_Experiment_Designer.py": "/experiment-designer",
    "pages/1_Funnel_Diagnostics.py": "/funnel-diagnostics",
}


@app.get("/", response_class=HTMLResponse)
def overview(request: Request):
    return templates.TemplateResponse(request, "overview.html", {
        "active_page": "overview",
        "tools_row1": TOOLS[:3],
        "tools_row2": TOOLS[3:],
    })


@app.get("/first-response", response_class=HTMLResponse)
def first_response(request: Request):
    return templates.TemplateResponse(request, "first_response.html", {
        "active_page": "first_response",
        "categories": decision_tree.category_list(),
    })


@app.get("/first-response/category/{tree_id}", response_class=HTMLResponse)
def first_response_category(request: Request, tree_id: str):
    if tree_id not in decision_tree.TREES:
        return HTMLResponse("<div class='fr-result-card'>Unknown category.</div>", status_code=404)

    tree = decision_tree.get_tree(tree_id)
    scenario = SCENARIOS[tree_id]
    diagnosis = scenario["diagnosis"]
    handoff_route = None
    if diagnosis.get("handoff"):
        handoff_route = PAGE_TO_ROUTE.get(diagnosis["handoff"]["page"])

    return templates.TemplateResponse(request, "partials/fr_result.html", {
        "tree_id": tree_id,
        "tree": tree,
        "scenario": scenario,
        "handoff_route": handoff_route,
    })


@app.get("/first-response/clear", response_class=HTMLResponse)
def first_response_clear():
    return HTMLResponse("")


# ── Funnel Diagnostics ───────────────────────────────────────────────
@app.get("/funnel-diagnostics", response_class=HTMLResponse)
def funnel_diagnostics_page(request: Request):
    return templates.TemplateResponse(request, "funnel_diagnostics.html", {
        "active_page": "funnel_diagnostics",
        "brands": data_lib.get_brands(),
        "order_csv_columns": ingest.ORDER_CSV_COLUMNS,
    })


@app.get("/funnel-diagnostics/sample-csv")
def funnel_diagnostics_sample_csv():
    from fastapi.responses import Response
    return Response(
        content=ingest.sample_order_csv_bytes(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=order_level_template.csv"},
    )


def _build_funnel_dashboard_context(stats: dict, is_real_data: bool, brand_name: str,
                                     narrative: dict | None = None, ranked_plays: list | None = None) -> dict:
    """Shared shaping logic between the sample-demo and real-data paths —
    both need the same derived chart-ready values, just computed from a
    different `stats` dict. `narrative`/`ranked_plays` come from the live
    n8n workflow when it's reachable, or the bundled fixture otherwise —
    see funnel_diagnostics_run for how those are resolved."""
    raw_stages = stats["funnel_stages"]
    max_funnel = max((s["value"] for s in raw_stages), default=1) or 1
    funnel_stages = []
    for i, s in enumerate(raw_stages):
        step_drop_pct = None
        if i > 0 and raw_stages[i - 1]["value"]:
            step_drop_pct = round((raw_stages[i - 1]["value"] - s["value"]) / raw_stages[i - 1]["value"] * 100)
        funnel_stages.append({
            "stage": s["stage"], "value": s["value"],
            "pct": round(s["value"] / max_funnel * 100, 1),
            "step_drop_pct": step_drop_pct,
        })
    last_stage = funnel_stages[-1] if funnel_stages else None
    first_stage = funnel_stages[0] if funnel_stages else None

    cohorts = []
    for c in stats["cohorts"]:
        cells = []
        for k in ("m1", "m2", "m3", "m4"):
            if k not in c:
                continue
            v = c[k]
            cells.append({"label": k.upper(), "value": v, "color": chart_helpers.heat_color(v)})
        cohorts.append({"cohort": c["cohort"], "cells": cells})

    anomalies = chart_helpers.detect_anomalies(stats.get("trend", []))
    retention_gap = stats["m1_m2_retention"] * 100 - stats["benchmark"]["category_typical"]

    base = data_lib.SAMPLE_RESULTS["funnel_diagnostics"]
    return {
        "stats": stats,
        "funnel_stages": funnel_stages,
        "last_stage": last_stage,
        "first_stage": first_stage,
        "cohorts": cohorts,
        "anomalies_count": len(anomalies),
        "retention_gap": retention_gap,
        "narrative": narrative or base["narrative"],
        "ranked_plays": ranked_plays or base["ranked_plays"],
        "is_real_data": is_real_data,
        "brand_name": brand_name,
        "note": stats.get("_funnel_note") or stats.get("_cohort_note"),
    }


@app.post("/funnel-diagnostics/run", response_class=HTMLResponse)
async def funnel_diagnostics_run(
    request: Request,
    mode: str = Form(...),
    brand_id: str = Form(""),
    snap_m1m2: float = Form(18.0),
    snap_discount: float = Form(41.0),
    snap_days: int = Form(34),
    snap_benchmark: float = Form(29.0),
    snap_paid: float = Form(14.0),
    snap_organic: float = Form(24.0),
    snap_email: float = Form(21.0),
    fn_visit: int = Form(100000),
    fn_cart: int = Form(32000),
    fn_checkout: int = Form(14000),
    fn_purchase: int = Form(9800),
    fn_repeat: int = Form(1764),
    order_csv: UploadFile | None = File(None),
):
    brand_name = next((b["name"] for b in data_lib.get_brands() if b["id"] == brand_id), "Demo workspace")

    computed_stats = None
    if mode == "order_level":
        if order_csv is None or not order_csv.filename:
            return HTMLResponse(
                '<div class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">'
                'Upload a CSV before running diagnosis.</div>', status_code=400)
        try:
            contents = await order_csv.read()
            df = pd.read_csv(io.BytesIO(contents))
            computed_stats = ingest.compute_stats_from_orders(df)
        except Exception as e:
            return HTMLResponse(
                f'<div class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">'
                f'Couldn\'t parse that file: {e}</div>', status_code=400)
    elif mode == "metrics_snapshot":
        computed_stats = ingest.compute_stats_from_snapshot({
            "m1_m2_retention": snap_m1m2, "discount_dependency": snap_discount,
            "days_to_2nd": snap_days, "benchmark": snap_benchmark,
            "seg_paid_social": snap_paid, "seg_organic": snap_organic, "seg_email": snap_email,
            "fn_visit": fn_visit, "fn_cart": fn_cart, "fn_checkout": fn_checkout,
            "fn_purchase": fn_purchase, "fn_repeat": fn_repeat,
        })

    is_real_data = computed_stats is not None

    if is_real_data:
        # Real upload/snapshot: ask the live n8n workflow for AI narrative +
        # ranked plays grounded in these actual numbers. call_workflow() falls
        # back to the SAMPLE_RESULTS fixture wholesale if the webhook is
        # unreachable/unconfigured — fine for narrative/ranked_plays, but the
        # user's real numbers must never be silently swapped for fixture
        # numbers just because the AI call failed, so `stats` stays local.
        result = data_lib.call_workflow("funnel_diagnostics", {
            "brand_id": brand_id, "mode": mode, "computed_stats": computed_stats,
        })
        stats = computed_stats
        narrative, ranked_plays = result.get("narrative"), result.get("ranked_plays")
    else:
        # Sample/demo mode: no real data was submitted, so there's nothing for
        # a live workflow to reason about — stay on the free bundled fixture
        # rather than spending real Groq/PDF.co calls on a walkthrough click.
        stats = data_lib.SAMPLE_RESULTS["funnel_diagnostics"]["computed_stats"]
        narrative, ranked_plays = None, None

    ctx = _build_funnel_dashboard_context(
        stats, is_real_data=is_real_data, brand_name=brand_name,
        narrative=narrative, ranked_plays=ranked_plays,
    )
    return templates.TemplateResponse(request, "partials/funnel_dashboard.html", ctx)


# ── Lifecycle Architect ──────────────────────────────────────────────
@app.get("/lifecycle-architect", response_class=HTMLResponse)
def lifecycle_architect_page(request: Request):
    return templates.TemplateResponse(request, "lifecycle_architect.html", {
        "active_page": "lifecycle_architect",
        "brands": data_lib.get_brands(),
    })


@app.post("/lifecycle-architect/run", response_class=HTMLResponse)
async def lifecycle_architect_run(
    request: Request,
    brand_id: str = Form(""),
    category: str = Form("D2C · Beauty & personal care"),
    discount_stance: str = Form("Discount-light (earn loyalty)"),
    diagnosis: str = Form(""),
):
    result = data_lib.call_workflow("lifecycle_architect", {
        "brand_id": brand_id, "category": category,
        "discount_stance": discount_stance, "diagnosis": diagnosis,
    })
    stages = result["stages"]
    funnel = result["engagement_funnel"]
    avg_warmth = (sum(s["tone_score"]["warmth"] for s in stages) / len(stages)) if stages else 0.0
    convert_rate = (funnel[-1]["value"] / funnel[0]["value"] * 100) if funnel and funnel[0]["value"] else 0.0

    max_funnel = max((f["value"] for f in funnel), default=1) or 1
    funnel_bars = [
        {"stage": f["stage"], "value": f["value"], "pct": round(f["value"] / max_funnel * 100, 1)}
        for f in funnel
    ]

    days = [s["day"] for s in stages]
    min_day, max_day = (min(days), max(days)) if days else (0, 1)
    span = (max_day - min_day) or 1
    timeline_points = [
        {"day": s["day"], "name": s["name"], "left_pct": round((s["day"] - min_day) / span * 100, 1)}
        for s in stages
    ]

    return templates.TemplateResponse(request, "partials/lifecycle_dashboard.html", {
        "stages": stages,
        "funnel_bars": funnel_bars,
        "timeline_points": timeline_points,
        "avg_warmth": avg_warmth,
        "convert_rate": convert_rate,
        "narrative": result["narrative"],
    })


# ── Experiment Designer ──────────────────────────────────────────────
@app.get("/experiment-designer", response_class=HTMLResponse)
def experiment_designer_page(request: Request):
    return templates.TemplateResponse(request, "experiment_designer.html", {
        "active_page": "experiment_designer",
        "brands": data_lib.get_brands(),
    })


@app.post("/experiment-designer/run", response_class=HTMLResponse)
async def experiment_designer_run(
    request: Request,
    brand_id: str = Form(""),
    baseline: str = Form("18%"),
    mde: str = Form("+3pp"),
    traffic: str = Form("640 customers/day"),
    hypothesis: str = Form(...),
):
    result = data_lib.call_workflow("experiment_designer", {
        "brand_id": brand_id, "hypothesis": hypothesis,
        "baseline": baseline, "mde": mde, "traffic": traffic,
    })
    spec = result["spec"]
    max_n = max((c["n"] for c in spec["power_curve"]), default=1) or 1
    power_curve = [{"mde": c["mde"], "n": c["n"], "pct": round(c["n"] / max_n * 100, 1)} for c in spec["power_curve"]]
    max_lift = max([abs(h["lift_pp"]) for h in result["historical_outcomes"]], default=1) or 1

    return templates.TemplateResponse(request, "partials/experiment_dashboard.html", {
        "spec": spec,
        "power_curve": power_curve,
        "guardrails": result["guardrails"],
        "decision_rule": result["decision_rule"],
        "historical_outcomes": result["historical_outcomes"],
        "max_lift": max_lift,
        "narrative": result["narrative"],
        "hypothesis": hypothesis,
    })


# ── Results & Learnings ──────────────────────────────────────────────
VERDICT_STYLE = {
    "SHIP": "bg-emerald-50 text-emerald-700 border-emerald-200",
    "KILL": "bg-rose-50 text-rose-700 border-rose-200",
    "EXTEND": "bg-amber-50 text-amber-700 border-amber-200",
}


@app.get("/results-learnings", response_class=HTMLResponse)
def results_learnings_page(request: Request):
    brands = data_lib.get_brands()
    return templates.TemplateResponse(request, "results_learnings.html", {
        "active_page": "results_learnings",
        "brands": brands,
        "verdict_style": VERDICT_STYLE,
        **_results_learnings_context(brands[0]["id"] if brands else ""),
    })


def _results_learnings_context(brand_id: str) -> dict:
    experiments = data_lib.get_experiments(brand_id)
    result = data_lib.call_workflow("results_learnings", {"brand_id": brand_id})
    history = result["history"]
    dist = result["verdict_distribution"]
    total_graded = sum(dist.values())
    win_rate = round(dist.get("SHIP", 0) / total_graded * 100) if total_graded else 0
    cum_impact = result["cumulative_impact_pp"][-1] if result["cumulative_impact_pp"] else 0

    running, total = [], 0
    for v in result["cumulative_impact_pp"]:
        total += v
        running.append(total)
    max_running = max([abs(r) for r in running], default=1) or 1
    cumulative_bars = [{"label": f"Exp {i+1}", "value": r, "pct": round(abs(r) / max_running * 100, 1)}
                        for i, r in enumerate(running)]

    max_theme = max((t["count"] for t in result["themes"]), default=1) or 1
    themes = [{"theme": t["theme"], "count": t["count"], "pct": round(t["count"] / max_theme * 100, 1)}
              for t in result["themes"]]

    return {
        "brand_id": brand_id,
        "experiments": experiments,
        "history": history,
        "verdict_distribution": dist,
        "total_graded": total_graded,
        "win_rate": win_rate,
        "cum_impact": cum_impact,
        "cumulative_bars": cumulative_bars,
        "themes": themes,
        "narrative": result["narrative"],
    }


@app.get("/results-learnings/for-brand", response_class=HTMLResponse)
def results_learnings_for_brand(request: Request, brand_id: str = ""):
    return templates.TemplateResponse(request, "partials/results_dashboard.html", {
        "verdict_style": VERDICT_STYLE,
        **_results_learnings_context(brand_id),
    })


@app.post("/results-learnings/grade", response_class=HTMLResponse)
async def results_learnings_grade(
    request: Request,
    brand_id: str = Form(""),
    experiment_id: str = Form(""),
    lift: float = Form(3.4),
    optout: float = Form(0.3),
    support: int = Form(0),
):
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
    saved = False
    if experiment_id:
        saved = data_lib.save_experiment_result(experiment_id, lift, optout, support, verdict, takeaway)

    return templates.TemplateResponse(request, "partials/grade_result.html", {
        "verdict": verdict, "lift": lift, "optout": optout, "takeaway": takeaway,
        "saved": saved, "verdict_style": VERDICT_STYLE,
    })
