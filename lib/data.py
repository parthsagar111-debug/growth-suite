"""
Data / memory layer.

Every page calls `call_workflow(tool, payload)` instead of talking to
Supabase or n8n directly. That function:

  1. Checks the kill switch (app_settings.is_live in Supabase, or
     GROWTH_SUITE_LIVE env var if Supabase isn't configured).
  2. If live and an n8n webhook URL is configured for that tool, POSTs
     the payload and returns the JSON response (which n8n has already
     written to Supabase via the Memory: Write sub-workflow).
  3. If not live, or no webhook is configured (e.g. running this demo
     locally without infra wired up yet), falls back to bundled sample
     data so every page still renders a full result.

This means the frontend never breaks even before n8n/Supabase exist —
which is also exactly how the kill switch is meant to work: flipping
n8n workflows to Inactive makes every tool silently fall back to
demo data instead of erroring for a stray visitor.
"""
import os
import json
import concurrent.futures
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

WEBHOOKS = {
    "funnel_diagnostics": os.getenv("N8N_WEBHOOK_FUNNEL", ""),
    "lifecycle_architect": os.getenv("N8N_WEBHOOK_LIFECYCLE", ""),
    "experiment_designer": os.getenv("N8N_WEBHOOK_EXPERIMENT", ""),
    "results_learnings": os.getenv("N8N_WEBHOOK_RESULTS", ""),
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Every Supabase call in this module is routed through this so a slow or
# unreachable project can never hang a page indefinitely — supabase-py's
# own client-level timeout options vary across versions, so this enforces
# a hard wall-clock cap at the application layer instead of trusting the
# library's defaults.
_SUPABASE_TIMEOUT_SECS = 10
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="supabase-call")


def _guarded(fn, default, label):
    """Runs `fn` with a hard timeout; returns `default` (and surfaces a
    warning) on timeout or any other failure instead of letting an
    unreachable backend freeze the page."""
    try:
        future = _EXECUTOR.submit(fn)
        return future.result(timeout=_SUPABASE_TIMEOUT_SECS)
    except concurrent.futures.TimeoutError:
        st.warning(f"{label} timed out after {_SUPABASE_TIMEOUT_SECS}s — showing demo data instead.")
        return default
    except Exception as e:
        st.warning(f"{label} failed ({e}) — showing demo data instead.")
        return default


def _supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


@st.cache_data(ttl=15)
def is_live() -> bool:
    """The kill switch. n8n's Active/Inactive toggle is the real switch
    (it stops the LLM/PDF calls); this flag just controls what the
    frontend shows a visitor while workflows are off."""
    sb = _supabase()
    if sb is None:
        return os.getenv("GROWTH_SUITE_LIVE", "true").lower() != "false"
    return _guarded(
        lambda: bool(sb.table("app_settings").select("value").eq("key", "is_live").single().execute().data["value"]),
        default=True, label="Kill-switch check",
    )


def set_live(value: bool):
    sb = _supabase()
    if sb is not None:
        _guarded(
            lambda: sb.table("app_settings").update({"value": value}).eq("key", "is_live").execute(),
            default=None, label="Kill-switch update",
        )
    is_live.clear()


@st.cache_data(ttl=30)
def get_brands():
    sb = _supabase()
    if sb is None:
        return SAMPLE_BRANDS
    return _guarded(
        lambda: (sb.table("brands").select("*").order("created_at").execute().data or SAMPLE_BRANDS),
        default=SAMPLE_BRANDS, label="Loading brands",
    )


def create_brand(name: str, category: str = "Other", discount_stance: str = "discount-light") -> str | None:
    """Promotes a ghost/draft workspace to a real brand row. Used by the
    'Rename & Save Workspace' nudge — the user gets to see a custom
    upload's full dashboard first, and only commits a name afterward if
    they want the workspace to persist and show up in the brand dropdown
    on future visits.

    Validates the name client-side (non-empty, sane length) before ever
    reaching Supabase — the caller already checks for a blank name, but
    a function that writes to the database shouldn't rely on callers to
    have done that correctly."""
    sb = _supabase()
    name = (name or "").strip()
    if sb is None or not name:
        return None
    if len(name) > 120:
        st.warning("Workspace name is too long (120 characters max).")
        return None

    def _insert():
        res = sb.table("brands").insert({
            "name": name, "category": category, "discount_stance": discount_stance,
        }).execute()
        return res.data[0]["id"] if res.data else None

    new_id = _guarded(_insert, default=None, label="Saving workspace")
    if new_id:
        get_brands.clear()
    return new_id


def get_experiments(brand_id: str):
    """Experiments for a brand, most recent first — lets Results & Learnings
    attach a grade to a specific experiment row instead of grading in a vacuum."""
    sb = _supabase()
    if sb is None or not brand_id:
        return []
    return _guarded(
        lambda: (sb.table("experiments")
                   .select("id,hypothesis,created_at")
                   .eq("brand_id", brand_id)
                   .order("created_at", desc=True)
                   .limit(20)
                   .execute().data or []),
        default=[], label="Loading experiments",
    )


def save_experiment_result(experiment_id: str, lift_pp: float, optout_pp: float,
                            support_delta: int, verdict: str, takeaway: str) -> bool:
    """Persist a graded outcome to experiment_results. This is the write that
    closes the memory loop — without it, Results & Learnings' dashboard and
    Experiment Designer's Similar-Experiment Analyst only ever see seed data,
    never anything a real user actually grades.

    Validates inputs before writing: verdict must be one of the three
    the schema's check constraint allows, and the metrics must actually
    be numbers — number_input widgets guarantee this client-side, but a
    write function shouldn't assume its caller always will.
    """
    sb = _supabase()
    if sb is None or not experiment_id:
        return False
    if verdict not in ("SHIP", "KILL", "EXTEND"):
        st.warning(f"Invalid verdict '{verdict}' — not saved.")
        return False
    try:
        lift_pp, optout_pp, support_delta = float(lift_pp), float(optout_pp), int(support_delta)
    except (TypeError, ValueError):
        st.warning("Grading inputs weren't numeric — not saved.")
        return False

    def _insert():
        sb.table("experiment_results").insert({
            "experiment_id": experiment_id,
            "actual_metrics": {
                "lift_pp": lift_pp,
                "opt_out_delta_pp": optout_pp,
                "support_ticket_delta": support_delta,
            },
            "verdict": verdict,
            "takeaway": takeaway,
        }).execute()
        return True

    return _guarded(_insert, default=False, label="Saving grade")


def call_workflow(tool: str, payload: dict) -> dict:
    """Call the n8n webhook for `tool`; fall back to sample data if the
    webhook isn't configured, the app is toggled off, or the call fails.
    Connect and read timeouts are set separately (5s / 45s) rather than
    one combined value, so a slow DNS lookup or a dead connection fails
    fast instead of burning the same budget as a slow-but-alive workflow."""
    url = WEBHOOKS.get(tool, "")
    if url and is_live():
        try:
            r = requests.post(url, json=payload, timeout=(5, 45))
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            st.warning("Live workflow call timed out — showing demo data instead.")
        except requests.exceptions.ConnectionError:
            st.warning("Couldn't reach the live workflow — showing demo data instead.")
        except Exception as e:
            st.warning(f"Live workflow call failed ({e}) — showing demo data instead.")
    return SAMPLE_RESULTS.get(tool, {})


# ── Bundled demo data (mirrors sql/seed.sql) ────────────────────────────
SAMPLE_BRANDS = [
    {"id": "11111111-1111-1111-1111-111111111111", "name": "Verdant Skincare",
     "category": "D2C · Beauty & personal care", "discount_stance": "discount-light"},
    {"id": "22222222-2222-2222-2222-222222222222", "name": "Hearth & Home Co",
     "category": "D2C · Home", "discount_stance": "discount-heavy"},
]

SAMPLE_RESULTS = {
    "funnel_diagnostics": {
        "computed_stats": {
            "m1_m2_retention": 0.18, "discount_dependency": 0.41,
            "time_to_2nd_order_median_days": 34,
            "cohorts": [
                {"cohort": "Jan", "m1": 100, "m2": 18, "m3": 12, "m4": 9},
                {"cohort": "Feb", "m1": 100, "m2": 21, "m3": 14, "m4": 10},
                {"cohort": "Mar", "m1": 100, "m2": 16, "m3": 11, "m4": 8},
            ],
            "trend": [{"period": f"W{i}", "value": v} for i, v in
                      enumerate([22, 24, 23, 19, 18, 12, 19, 20], start=1)],
            "segments": [{"segment": "Paid social", "value": 0.14},
                         {"segment": "Organic", "value": 0.24},
                         {"segment": "Email", "value": 0.21}],
            "funnel_stages": [{"stage": "Visit", "value": 100000},
                               {"stage": "Add to cart", "value": 32000},
                               {"stage": "Checkout", "value": 14000},
                               {"stage": "Purchase", "value": 9800},
                               {"stage": "Repeat (M2)", "value": 1764}],
            "benchmark": {"you": 18, "category_typical": 29},
        },
        "diagnosed_leak": "M1→M2 retention collapses to 18%, well under category benchmark, "
                           "concentrated in the paid-social cohort and propped up by discount "
                           "codes on 41% of repeats.",
        "ranked_plays": [
            {"title": "WhatsApp win-back at day 35, no discount", "impact": "High",
             "rationale": "Fires before the M2 cliff, leads with education instead of a code."},
            {"title": "Bundle second-order incentive at checkout", "impact": "Medium",
             "rationale": "Seeds a non-monetary reason to return on order 1."},
            {"title": "Reduce discount depth on repeat codes", "impact": "Medium",
             "rationale": "Tests how price-elastic month-2 demand really is."},
        ],
        "narrative": {
            "interpreter": "Retention is being rented, not earned — 41% of second orders lean on a code.",
            "anomaly_explainer": "The Feb cohort dips less steeply than Jan/Mar, coinciding with a smaller discount push that month.",
            "root_cause": "The cliff sits specifically between month 1 and month 2, not a gradual decline — consistent with a missing mid-funnel nudge rather than a product problem.",
            "benchmark_commentary": "Category benchmark for M1→M2 in beauty D2C sits near 27–32%; this brand is roughly 10pp under.",
            "segment_insight": "Paid social cohort retains 6pp worse than organic, suggesting acquisition quality is part of the story, not just lifecycle timing.",
            "synthesis": "The leak is a discount-dependent M2 cliff concentrated in paid social — fixable with earlier, code-free retention touchpoints rather than deeper discounting.",
        },
    },
    "lifecycle_architect": {
        "stages": [
            {"day": 0, "name": "Welcome", "channel": "WhatsApp",
             "message": "You're in — here's how to get the most out of your first order, no code needed.",
             "rationale": "Sets product-education tone from day one instead of training customers to wait for a discount.",
             "tone_score": {"warmth": 0.8, "urgency": 0.1},
             "variants": ["Quick start: 3 things to do with your first order.",
                          "Welcome! Here's the one tip most first-timers miss."]},
            {"day": 14, "name": "Habit-forming", "channel": "WhatsApp",
             "message": "How's it going so far? Here's a tip most first-timers miss.",
             "rationale": "Reinforces value before the natural repeat-purchase window opens.",
             "tone_score": {"warmth": 0.75, "urgency": 0.15},
             "variants": ["Two weeks in — here's what changes next.", "A quick check-in + a pro tip."]},
            {"day": 28, "name": "At-risk", "channel": "WhatsApp",
             "message": "Running low? Reorder takes 30 seconds.",
             "rationale": "Fires one week before the diagnosed M2 cliff at day 35.",
             "tone_score": {"warmth": 0.6, "urgency": 0.4},
             "variants": ["Don't run out — reorder in 30 seconds.", "Still loving it? Here's a faster way to restock."]},
            {"day": 45, "name": "Lapsed", "channel": "WhatsApp",
             "message": "We miss you — no discount pitch, just checking in.",
             "rationale": "Deliberately code-free, testing whether the M2 drop is truly price-elastic.",
             "tone_score": {"warmth": 0.7, "urgency": 0.3},
             "variants": ["It's been a while — how did it work out for you?", "Checking in, no strings attached."]},
            {"day": 75, "name": "Win-back", "channel": "WhatsApp",
             "message": "Last call — here's a small thank-you for coming back.",
             "rationale": "Only stage in the journey carrying an incentive, isolating true win-back cost.",
             "tone_score": {"warmth": 0.65, "urgency": 0.6},
             "variants": ["One last thing before we let go — a thank-you on us.", "Come back? Here's something small for you."]},
        ],
        "engagement_funnel": [{"stage": "Sent", "value": 1000}, {"stage": "Opened", "value": 620},
                               {"stage": "Clicked", "value": 190}, {"stage": "Converted", "value": 74}],
        "cadence_benchmark": {"you": [0, 14, 28, 45, 75], "category_typical": [0, 10, 21, 35, 60]},
        "narrative": {
            "synthesis": "Journey is intentionally code-light for four of five stages to test whether "
                          "the M2 cliff is truly price-driven, with the at-risk nudge deliberately timed "
                          "one week ahead of the diagnosed cliff.",
        },
    },
    "experiment_designer": {
        "spec": {"sample_size_per_arm": 1240, "duration_days": 3.9, "confidence": 0.95, "power": 0.8,
                  "power_curve": [{"mde": m, "n": n} for m, n in
                                  zip([1, 2, 3, 4, 5, 6], [11200, 2800, 1240, 700, 450, 310])]},
        "guardrails": [
            {"metric": "WhatsApp opt-out rate", "why": "Catches message fatigue from the added touchpoint",
             "safe_zone": "< +1.5pp", "kill_zone": ">= +1.5pp"},
            {"metric": "Full-price order share", "why": "Confirms the lift isn't pulled-forward discounted demand",
             "safe_zone": "flat or better", "kill_zone": "drops"},
            {"metric": "Support ticket volume", "why": "Flags confusion if the copy is unclear",
             "safe_zone": "flat", "kill_zone": "spikes"},
        ],
        "decision_rule": {"ship": "M2 lift ≥ 3pp with opt-out rate flat or better",
                           "extend": "Directionally positive but under-powered by day 4",
                           "kill": "Opt-out rate rises > 1.5pp regardless of lift"},
        "historical_outcomes": [{"experiment": "Day-28 nudge (Verdant)", "lift_pp": 3.4, "verdict": "SHIP"},
                                 {"experiment": "Checkout simplify (Hearth)", "lift_pp": 2.1, "verdict": "KILL"}],
        "narrative": {
            "risk_assessment": "Primary risk is message fatigue — this is the third WhatsApp touch in 28 days for this cohort.",
            "similar_experiment_analyst": "A comparable code-free nudge for this brand shipped with a 3.4pp lift and negligible opt-out impact — a good prior that this pattern works here.",
            "synthesis": "Small, fast test — the binding constraint is opt-out risk, not statistical power.",
        },
    },
    "results_learnings": {
        "history": [
            {"date": "2026-05-15", "brand": "Verdant Skincare", "verdict": "SHIP", "lift_pp": 3.4},
            {"date": "2026-06-04", "brand": "Hearth & Home Co", "verdict": "KILL", "lift_pp": 2.1},
        ],
        "verdict_distribution": {"SHIP": 1, "KILL": 1, "EXTEND": 0},
        "cumulative_impact_pp": [3.4, 3.4],
        "themes": [{"theme": "Code-free nudges outperform discount-led ones", "count": 2},
                   {"theme": "Guardrails catch real risk, not just noise", "count": 2}],
        "narrative": {
            "pattern_recognition": "Across both brands, guardrail metrics — not the primary lift — decided the "
                                    "verdict. Worth treating guardrail design as seriously as the hypothesis itself.",
        },
    },
}
