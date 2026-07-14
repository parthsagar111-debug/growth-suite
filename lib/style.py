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

def badge(text, kind="accent"):
    st.markdown(f'<span class="gs-badge gs-badge-{kind}">{text}</span>', unsafe_allow_html=True)

def flow_banner(text):
    st.markdown(f'<div class="gs-flow-banner">→ {text}</div>', unsafe_allow_html=True)

def agent_card(label, text):
    st.markdown(
        f'<div class="gs-agent-card"><div class="gs-agent-label">{label}</div>{text}</div>',
        unsafe_allow_html=True,
    )
