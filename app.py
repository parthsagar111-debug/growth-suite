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

st.title("Growth suite")
st.markdown('<p class="subtitle">Diagnose a funnel, design the fix, test it, and remember what happened — all under one roof.</p>', unsafe_allow_html=True)

cols = st.columns(4)
tools = [
    ("Funnel diagnostics", "coral", "Step 1 · Diagnose", "Upload funnel metrics or order history → a diagnosed leak, seven charts, and ranked plays.", "pages/1_Funnel_Diagnostics.py"),
    ("Lifecycle architect", "accent", "Step 2 · Design", "Describe a brand → a stage-by-stage WhatsApp journey with tone scoring and copy variants.", "pages/2_Lifecycle_Architect.py"),
    ("Experiment designer", "amber", "Step 3 · Test", "Type a hypothesis → a real z-test spec, guardrails, and a decision rule.", "pages/3_Experiment_Designer.py"),
    ("Results & learnings", "teal", "Step 4 · Learn", "Grade a shipped experiment against its own decision rule and log what was learned.", "pages/4_Results_Learnings.py"),
]
for col, (name, kind, step_label, desc, page) in zip(cols, tools):
    with col:
        with st.container(border=True):
            style.badge(step_label, kind)
            st.markdown(f"**{name}**")
            st.caption(desc)
            st.page_link(page, label="Open →")

st.divider()
with st.expander("How this works"):
    st.markdown(
        """
Every number on every page is computed by deterministic code — cohort math, z-test sample sizes,
trigger-day rules — never guessed by a model. AI's job is layered on top: multiple named agents per
tool interpret, compare, and narrate those numbers (interpreter, anomaly explainer, benchmark
commentary, risk assessment, and a final narrative synthesis), and every tool shows its full set of
charts and analysis before it shows a recommendation.

The one deliberate exception is grading: when an experiment ships and real results come in, the
SHIP/KILL/EXTEND call is made by comparing actuals against the thresholds you already committed to —
by code, not by a model. That's the one decision that shouldn't be left to AI.

Each tool is backed by its own n8n workflow. All four read from and write to a shared memory layer
(Supabase), scoped by brand, via two reusable sub-workflows — `Memory: Retrieve` and `Memory: Write`
— so Lifecycle Architect can ground a journey in a real diagnosis, and Experiment Designer can point
at a similar experiment that already ran.
        """
    )
