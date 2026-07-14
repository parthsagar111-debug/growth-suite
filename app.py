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

# ── Brand context (persists across pages via session_state) ───────────
brands = data.get_brands()
brand_names = [b["name"] for b in brands]
if "brand_id" not in st.session_state:
    st.session_state.brand_id = brands[0]["id"] if brands else None

with st.sidebar:
    st.markdown("### Growth suite")
    choice = st.selectbox("Brand", brand_names, index=0)
    st.session_state.brand_id = next(b["id"] for b in brands if b["name"] == choice)
    st.caption("All four tools below scope their memory to this brand.")
    st.divider()
    st.page_link("app.py", label="Home", icon="\U0001F3E0")
    st.page_link("pages/1_Funnel_Diagnostics.py", label="Funnel diagnostics", icon="\U0001FA7A")
    st.page_link("pages/2_Lifecycle_Architect.py", label="Lifecycle architect", icon="\U0001F504")
    st.page_link("pages/3_Experiment_Designer.py", label="Experiment designer", icon="\U0001F9EA")
    st.page_link("pages/4_Results_Learnings.py", label="Results & learnings", icon="\U0001F4CA")

st.title("Growth suite")
st.markdown('<p class="subtitle">Diagnose a funnel, design the fix, test it, and remember what happened — all under one roof.</p>', unsafe_allow_html=True)

cols = st.columns(4)
tools = [
    ("Funnel diagnostics", "coral", "Upload funnel metrics or order history → a diagnosed leak, seven charts, and ranked plays.", "pages/1_Funnel_Diagnostics.py"),
    ("Lifecycle architect", "accent", "Describe a brand → a stage-by-stage WhatsApp journey with tone scoring and copy variants.", "pages/2_Lifecycle_Architect.py"),
    ("Experiment designer", "amber", "Type a hypothesis → a real z-test spec, guardrails, and a decision rule.", "pages/3_Experiment_Designer.py"),
    ("Results & learnings", "teal", "Grade a shipped experiment against its own decision rule and log what was learned.", "pages/4_Results_Learnings.py"),
]
for col, (name, kind, desc, page) in zip(cols, tools):
    with col:
        with st.container(border=True):
            style.badge(kind.capitalize(), kind)
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
