"""Shared design system for every page in the suite.

Corporate palette: Indigo (primary/brand), Emerald (positive), Slate
(neutral/muted), Crimson (negative). Amber stays on as a fifth accent
specifically for the three-state SHIP/EXTEND/KILL vocabulary, where a
neutral "pending decision" color reads more honestly than reusing Slate
(which already means "disabled/muted" elsewhere in this system) or
Emerald/Crimson (which are already claimed by SHIP/KILL).
"""
import streamlit as st

PALETTE = {
    "accent": "#4f46e5", "accent_bg": "#eef2ff",   # Indigo
    "teal": "#059669", "teal_bg": "#ecfdf5",         # Emerald
    "coral": "#dc2626", "coral_bg": "#fef2f2",       # Crimson
    "amber": "#b45309", "amber_bg": "#fffbeb",
    "green": "#059669", "green_bg": "#ecfdf5",
    "red": "#dc2626", "red_bg": "#fef2f2",
    "muted": "#64748b", "muted_bg": "#f1f5f9",       # Slate
    "text": "#0f172a", "text2": "#475569",
    "border": "#e2e8f0",
}

CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
/* Hide Streamlit's auto-generated page nav — we render one consistent
   custom nav via style.sidebar() instead, so the sidebar never shows
   two competing menus. */
[data-testid="stSidebarNav"] {display: none;}

html, body, [class*="css"] {font-family: Helvetica, Arial, sans-serif !important;}

/* Data-dense SaaS spacing — Streamlit's defaults are built for a blog
   post, not a workspace someone opens twenty times a day. */
.block-container {padding-top: 1rem !important; padding-bottom: 2rem; max-width: 1120px;}
div[data-testid="stVerticalBlock"] > div {gap: 0.6rem;}
h1 {font-size: 24px !important; font-weight: 700 !important; margin-bottom: 2px !important; color:#0f172a;}
h2 {font-size: 17px !important; font-weight: 600 !important;}
h3 {font-size: 13px !important; font-weight: 700 !important; text-transform:uppercase; letter-spacing:0.03em;
    color:#475569 !important; margin-top: 0.4rem !important;}
.subtitle {color: #475569; font-size: 13.5px; margin-bottom: 1rem;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 10px !important;}

/* Executive scorecards — st.metric gets a card shell; Streamlit already
   renders the colored ↑/↓ delta arrow natively, so we don't reinvent it. */
div[data-testid="stMetric"] {
  background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px;
}
div[data-testid="stMetricValue"] {font-size: 26px !important; font-weight: 700 !important; color:#0f172a;}
div[data-testid="stMetricLabel"] {font-size: 12px !important; color:#64748b !important; font-weight:600;
  text-transform:uppercase; letter-spacing:0.02em;}

/* Horizontal control strip — the row of selectors every tool page opens
   with (brand, mode, and whatever page-specific filters apply). */
.gs-control-strip {background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
  padding:14px 16px 4px 16px; margin-bottom:14px;}

.gs-badge {display:inline-block; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; margin-bottom:6px;}
.gs-badge-teal {background:#ecfdf5; color:#059669;}
.gs-badge-coral {background:#fef2f2; color:#dc2626;}
.gs-badge-amber {background:#fffbeb; color:#b45309;}
.gs-badge-accent {background:#eef2ff; color:#4f46e5;}
.gs-badge-muted {background:#f1f5f9; color:#64748b;}

/* Compact inline status pill — replaces static "nothing found" boxes
   with a single-line acknowledgement that doesn't eat vertical space. */
.gs-pill {display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
  padding:5px 12px; border-radius:20px; margin: 4px 0 10px 0;}
.gs-pill-ok {background:#ecfdf5; color:#059669;}
.gs-pill-warn {background:#fffbeb; color:#b45309;}
.gs-pill-muted {background:#f1f5f9; color:#64748b;}

.gs-flow-banner {display:flex; align-items:center; gap:10px; background:#eef2ff; color:#3730a3;
  border-radius:8px; padding:12px 16px; font-size:13px; margin:10px 0; border:1px solid #c7d2fe;}
.gs-agent-card {border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px; margin-bottom:10px; background:#fff;}
.gs-agent-label {font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:#64748b; margin-bottom:4px;}
.gs-stage-msg {background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; font-size:13px; margin-top:6px;}
.gs-offline {text-align:center; padding: 4rem 1rem; color:#475569;}

.gs-zone {font-size:13px; font-weight:600; padding:4px 0;}
.gs-zone-safe {color:#059669;}
.gs-zone-kill {color:#dc2626;}

.gs-empty {text-align:center; color:#64748b; font-size:13px; padding:2.5rem 1rem;
  border:1px dashed #e2e8f0; border-radius:10px; margin-top:0.5rem;}

/* "Next playbook action" — the one place every page's routing button
   and PDF export live, instead of scattered blue banners + orphan buttons. */
.gs-next-action {background:#fff; border:1px solid #e2e8f0; border-left:3px solid #4f46e5;
  border-radius:10px; padding:14px 16px; margin-top:1.2rem;}

/* Journey stage cards — left-aligned day indicator instead of a plain
   two-column split, closer to a real step-tracker component. */
.gs-step-day {display:inline-flex; align-items:center; justify-content:center; min-width:52px;
  height:52px; border-radius:10px; background:#eef2ff; color:#4f46e5; font-weight:700;
  font-size:13px; text-align:center; line-height:1.15;}

/* Ghost-identity workspace placeholder — visually distinct "draft" state
   for the brand selector when a custom upload/snapshot is in progress. */
.gs-ghost-brand {display:flex; align-items:center; gap:8px; background:#f8fafc; border:1px dashed #cbd5e1;
  border-radius:8px; padding:9px 12px; font-size:14px; color:#475569; font-weight:500;}
</style>
"""

VERDICT_COLOR = {"SHIP": "teal", "KILL": "coral", "EXTEND": "amber"}
IMPACT_COLOR = {"High": "teal", "Medium": "amber", "Low": "muted"}


def inject():
    st.set_page_config(page_title="Growth Suite", page_icon="\U0001F4C8", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


NAV_PAGES = [
    ("app.py", "Home", "\U0001F3E0"),
    ("pages/1_Funnel_Diagnostics.py", "Funnel diagnostics", "\U0001FA7A"),
    ("pages/2_Lifecycle_Architect.py", "Lifecycle architect", "\U0001F504"),
    ("pages/3_Experiment_Designer.py", "Experiment designer", "\U0001F9EA"),
    ("pages/4_Results_Learnings.py", "Results & learnings", "\U0001F4CA"),
]


def sidebar():
    """Navigation only. The brand/workspace selector used to live here
    too, but it's now part of each page's own horizontal control strip
    (see brand_selector()) — a scoping choice belongs next to the other
    filters that define the current analysis, not buried in the sidebar."""
    with st.sidebar:
        st.markdown("### Growth suite")
        st.caption("Diagnose → Design → Test → Learn")
        st.divider()
        for page, label, icon in NAV_PAGES:
            st.page_link(page, label=label, icon=icon)


def brand_selector(label="Brand / workspace", locked=False, locked_text="✨ My Custom Brand"):
    """Renders inline (not in the sidebar) as one column of a page's
    horizontal control strip. When `locked`, swaps to a disabled ghost
    placeholder instead of the real dropdown — used while a custom
    upload/snapshot is active and hasn't been named yet, so the user
    gets straight to the analysis instead of filling out a brand form
    first. Returns the resolved brand_id, or None while locked."""
    from . import data as _data

    if locked:
        st.markdown(f'<label style="font-size:14px; font-weight:400;">{label}</label>', unsafe_allow_html=True)
        st.markdown(f'<div class="gs-ghost-brand">{locked_text}</div>', unsafe_allow_html=True)
        return None

    brands = _data.get_brands()
    brand_names = [b["name"] for b in brands]
    if not brand_names:
        st.selectbox(label, ["No brands yet"], disabled=True)
        return None
    if "brand_id" not in st.session_state or st.session_state.brand_id not in [b["id"] for b in brands]:
        st.session_state.brand_id = brands[0]["id"]
    current_name = next((b["name"] for b in brands if b["id"] == st.session_state.brand_id), brand_names[0])
    choice = st.selectbox(label, brand_names, index=brand_names.index(current_name))
    st.session_state.brand_id = next(b["id"] for b in brands if b["name"] == choice)
    return st.session_state.brand_id


def workspace_save_nudge(default_name="My custom brand", category_options=None, on_saved=None):
    """The 'Rename & Save Workspace' banner — shown after a ghost/draft
    workspace has produced a real result. Lets the user commit a name to
    a permanent brand row *after* they've already seen the value, instead
    of gating the analysis behind a naming form up front."""
    from . import data as _data

    st.markdown(
        '<div class="gs-flow-banner">✨ Running custom analytics pipeline on an unsaved draft workspace.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Rename & save workspace", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            name = st.text_input("Workspace name", value=default_name, key="ghost_save_name")
        with c2:
            category = st.selectbox("Category", category_options or
                                     ["D2C · Beauty & personal care", "D2C · Home", "D2C · Food & bev", "Other"],
                                     key="ghost_save_category")
        if st.button("Save as a brand →", type="primary"):
            new_id = _data.create_brand(name, category)
            if new_id:
                st.session_state["brand_id"] = new_id
                st.session_state["ghost_brand_id"] = new_id
                st.session_state["ghost_saved_name"] = name
                if on_saved:
                    on_saved()
                st.rerun()
            else:
                st.error("Couldn't save — Supabase isn't reachable right now.")


def badge(text, kind="accent"):
    st.markdown(f'<span class="gs-badge gs-badge-{kind}">{text}</span>', unsafe_allow_html=True)


def flow_banner(text):
    st.markdown(f'<div class="gs-flow-banner">→ {text}</div>', unsafe_allow_html=True)


def zone(label, kind="safe"):
    st.markdown(f'<div class="gs-zone gs-zone-{kind}">{label}</div>', unsafe_allow_html=True)


def empty_state(text):
    st.markdown(f'<div class="gs-empty">{text}</div>', unsafe_allow_html=True)


def status_pill(text, kind="muted"):
    """Compact single-line status, e.g. '✓ 0 Anomalies Flagged' — used
    instead of rendering a whole empty container when an array is empty
    but that fact is still worth a one-line acknowledgement."""
    st.markdown(f'<span class="gs-pill gs-pill-{kind}">{text}</span>', unsafe_allow_html=True)


def export_pdf_button(pdf_url, label="Export PDF"):
    if pdf_url:
        st.link_button(f"{label} ↗", pdf_url, use_container_width=True)
    else:
        st.button(
            label, disabled=True, use_container_width=True,
            help="PDF export needs the live n8n workflow — this result is demo data.",
        )


def agent_card(label, text):
    st.markdown(
        f'<div class="gs-agent-card"><div class="gs-agent-label">{label}</div>{text}</div>',
        unsafe_allow_html=True,
    )


_NO_PDF = object()


def next_action(text, button_label=None, button_page=None, button_state=None, pdf_url=_NO_PDF, extra=None):
    """Unified 'Next Playbook Action' container — every tool page ends
    with exactly one of these instead of a loose flow_banner + scattered
    buttons. `button_state` is a (key, value) tuple stashed in
    session_state right before switching pages, e.g. handing a result
    forward to the next tool in the chain."""
    with st.container(border=True):
        st.markdown('<div class="gs-agent-label">Next playbook action</div>', unsafe_allow_html=True)
        st.markdown(text)
        b1, b2 = st.columns([3, 1])
        with b1:
            if button_label and button_page:
                if st.button(button_label, type="primary"):
                    if button_state:
                        key, value = button_state
                        st.session_state[key] = value
                    st.switch_page(button_page)
        with b2:
            if pdf_url is not _NO_PDF:
                export_pdf_button(pdf_url)
        if extra:
            extra()
