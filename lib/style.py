"""Shared design system for every page in the suite."""
import streamlit as st

PALETTE = {
    "accent": "#185fa5", "accent_bg": "#e6f1fb",
    "teal": "#0f6e56", "teal_bg": "#e1f5ee",
    "coral": "#993c1d", "coral_bg": "#faece7",
    "amber": "#854f0b", "amber_bg": "#faeeda",
    "green": "#3b6d11", "green_bg": "#eaf3de",
    "red": "#a32d2d", "red_bg": "#fcebeb",
    "text": "#1c1b18", "text2": "#5f5e58", "muted": "#8c8a82",
    "border": "#e3e1da",
}

CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
/* Hide Streamlit's auto-generated page nav — we render one consistent
   custom nav (with the brand selector) via style.sidebar() instead,
   so the sidebar never shows two competing menus. */
[data-testid="stSidebarNav"] {display: none;}
.block-container {padding-top: 2rem; max-width: 980px;}
h1 {font-size: 26px !important; font-weight: 700 !important; margin-bottom: 2px !important;}
h2 {font-size: 18px !important; font-weight: 600 !important;}
h3 {font-size: 15px !important; font-weight: 600 !important;}
.subtitle {color: #5f5e58; font-size: 14px; margin-bottom: 1.5rem;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 12px !important;}
.gs-badge {display:inline-block; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; margin-bottom:6px;}
.gs-badge-teal {background:#e1f5ee; color:#0f6e56;}
.gs-badge-coral {background:#faece7; color:#993c1d;}
.gs-badge-amber {background:#faeeda; color:#854f0b;}
.gs-badge-accent {background:#e6f1fb; color:#185fa5;}
.gs-flow-banner {display:flex; align-items:center; gap:10px; background:#e6f1fb; color:#0c447c;
  border-radius:8px; padding:12px 16px; font-size:13px; margin:16px 0; border:1px solid #b5d4f4;}
.gs-agent-card {border:1px solid #e3e1da; border-radius:10px; padding:12px 16px; margin-bottom:10px; background:#fff;}
.gs-agent-label {font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:#8c8a82; margin-bottom:4px;}
.gs-stage-msg {background:#faf9f6; border:1px solid #e3e1da; border-radius:8px; padding:10px 12px; font-size:13px; margin-top:6px;}
.gs-offline {text-align:center; padding: 4rem 1rem; color:#5f5e58;}
</style>
"""

def inject():
    st.set_page_config(page_title="Growth Suite", page_icon="\U0001F4C8", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


NAV_PAGES = [
    ("app.py", "Home", "\U0001F3E0"),
    ("pages/1_Funnel_Diagnostics.py", "Funnel diagnostics", "\U0001FA82"),
    ("pages/2_Lifecycle_Architect.py", "Lifecycle architect", "\U0001F504"),
    ("pages/3_Experiment_Designer.py", "Experiment designer", "\U0001F9EA"),
    ("pages/4_Results_Learnings.py", "Results & learnings", "\U0001F4CA"),
]


def sidebar():
    """The one and only sidebar: brand selector + page nav. Call this on
    every page (Home included) right after inject() so the sidebar is
    identical everywhere, instead of each page building its own."""
    from . import data as _data

    brands = _data.get_brands()
    brand_names = [b["name"] for b in brands]
    if "brand_id" not in st.session_state and brands:
        st.session_state.brand_id = brands[0]["id"]

    current_name = next(
        (b["name"] for b in brands if b["id"] == st.session_state.get("brand_id")),
        brand_names[0] if brand_names else None,
    )

    with st.sidebar:
        st.markdown("### Growth suite")
        if brand_names:
            choice = st.selectbox(
                "Brand", brand_names,
                index=brand_names.index(current_name) if current_name in brand_names else 0,
            )
            st.session_state.brand_id = next(b["id"] for b in brands if b["name"] == choice)
            st.caption("Every tool below scopes its memory to this brand.")
        st.divider()
        for page, label, icon in NAV_PAGES:
            st.page_link(page, label=label, icon=icon)

def badge(text, kind="accent"):
    st.markdown(f'<span class="gs-badge gs-badge-{kind}">{text}</span>', unsafe_allow_html=True)

def flow_banner(text):
    st.markdown(f'<div class="gs-flow-banner">→ {text}</div>', unsafe_allow_html=True)

def export_pdf_button(pdf_url, label="Export PDF"):
    """A real link to the PDF.co-generated file when the tool ran live;
    a clearly-disabled button (not a fake download) in demo mode."""
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
