import streamlit as st
from lib import style, data

style.inject()

# ── Kill switch gate ──────────────────────────────────────────────────
# The real switch is each n8n workflow's Active/Inactive toggle (stops
# LLM/PDF spend outright). This is the friendly front-door version of
# the same switch: if app_settings.is_live is false in Supabase, every
# visitor sees this instead of the tool.
if not data.is_live():
    st.markdown(
        '<div class="gs-offline"><h2>This demo is currently offline</h2>'
        "<p>It's switched off between demos to avoid unattended traffic. "
        "Check back soon, or reach out if you'd like it turned on.</p></div>",
        unsafe_allow_html=True,
    )
    st.stop()

style.sidebar()

st.title("Growth Suite")
st.markdown('<p class="subtitle">Diagnose your conversion funnel, design targeted fixes, test improvements, and preserve workspace history — all under one roof.</p>', unsafe_allow_html=True)

tools = [
    ("Funnel Diagnostics", "coral", "Step 1 · Diagnose",
     "Upload funnel snapshots or order-level transaction history to capture customer leaks, "
     "inspect drop-off anomalies, and get an AI narrative alongside the full analysis dashboard.",
     "pages/1_Funnel_Diagnostics.py"),
    ("Lifecycle Architect", "blue", "Step 2 · Design",
     "Map a targeted customer retention journey — a stage-by-stage WhatsApp sequence, custom-written "
     "and scored against AI tone benchmarks.",
     "pages/2_Lifecycle_Architect.py"),
    ("Experiment Designer", "amber", "Step 3 · Test",
     "Construct a statistically defensible test: translate a hypothesis into a sample-size spec, "
     "power calculations, and guardrails that isolate variant risk.",
     "pages/3_Experiment_Designer.py"),
    ("Results & Learnings", "teal", "Step 4 · Learn",
     "Grade a shipped experiment against the decision rule it committed to, and log what was "
     "learned back into shared memory context.",
     "pages/4_Results_Learnings.py"),
]
# 2x2 grid, matching the mockup — not a single row of 4.
for row_start in (0, 2):
    row_cols = st.columns(2)
    for col, (name, kind, step_label, desc, page) in zip(row_cols, tools[row_start:row_start + 2]):
        with col:
            with st.container(border=True):
                style.badge(step_label, kind)
                st.markdown(f"**{name}**")
                st.caption(desc)
                st.markdown('<div class="gs-card-divider"></div>', unsafe_allow_html=True)
                st.page_link(page, label="Open Tools ↗")

st.divider()
with st.expander("How this works"):
    st.markdown(
        """
Every number on every page is computed by deterministic code — cohort math, z-test sample sizes,
trigger-day rules — never guessed by a model. AI's job is layered on top: multiple named agents per
tool interpret, compare, and narrate those numbers (anomaly explainer, benchmark commentary, risk
assessment, and a final narrative synthesis), and every tool shows its full set of charts and
analysis before it shows a recommendation.

The one deliberate exception is grading: when an experiment ships and real results come in, the
SHIP/KILL/EXTEND call is made by comparing actuals against the thresholds you already committed to —
by code, not by a model. That's the one decision that shouldn't be left to AI.

Each tool is backed by its own n8n workflow. All four read from and write to a shared memory layer
(Supabase), scoped by brand, via two reusable sub-workflows — `Memory: Retrieve` and `Memory: Write`
— so Lifecycle Architect can ground a journey in a real diagnosis, and Experiment Designer can point
at a similar experiment that already ran.
        """
    )
