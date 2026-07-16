"""Shared design system for every page in the suite.

Corporate palette: Indigo (primary/brand), Emerald (positive), Slate
(neutral/muted), Crimson (negative). Amber stays on as a fifth accent
specifically for the three-state SHIP/EXTEND/KILL vocabulary, where a
neutral "pending decision" color reads more honestly than reusing Slate
(which already means "disabled/muted" elsewhere in this system) or
Emerald/Crimson (which are already claimed by SHIP/KILL).

A note on how the horizontal control strips actually get their card
look: an earlier version of this file wrapped each control strip in a
hand-rolled `<div class="gs-control-strip">...</div>` pair, opened in
one st.markdown() call and closed in another, with real Streamlit
widgets in between. That doesn't work — st.markdown() mounts its own
isolated element; widgets rendered after it are siblings in the DOM,
not children, so the div never actually wrapped anything. It was inert
styling that happened to do nothing. The correct way to card a row of
widgets is to target the real container Streamlit already renders
around every st.columns() call (`div[data-testid="stHorizontalBlock"]`)
— that div genuinely contains its children, so CSS on it genuinely
wraps them. That's what the global rule below does instead.
"""
import streamlit as st

PALETTE = {
    "accent": "#6366f1", "accent_bg": "#eef2ff",   # Indigo
    "teal": "#10b981", "teal_bg": "#ecfdf5",         # Emerald
    "coral": "#ef4444", "coral_bg": "#fef2f2",       # Crimson
    "amber": "#d97706", "amber_bg": "#fffbeb",
    "green": "#10b981", "green_bg": "#ecfdf5",
    "red": "#ef4444", "red_bg": "#fef2f2",
    "muted": "#94a3b8", "muted_bg": "#f1f5f9",       # Slate
    "text": "#1e293b", "text2": "#475569",
    "border": "#e2e8f0",
}

CSS = """
<style>
#MainMenu, footer {visibility: hidden;}
/* The native Streamlit header bar (data-testid=stHeader) is kept visible
   but restyled into a slim glass strip below — its own contents
   (hamburger menu, "Deploy" button) are hidden via #MainMenu above, so
   what's left is just a clean, branded top edge instead of a hard cut. */
div[data-testid="stHeader"] {
    background: rgba(248, 250, 252, 0.85) !important;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-bottom: 1px solid #e2e8f0 !important;
}
/* Hide Streamlit's auto-generated page nav — we render one consistent
   custom nav via style.sidebar() instead, so the sidebar never shows
   two competing menus. */
[data-testid="stSidebarNav"] {display: none;}

html, body, [class*="css"] {font-family: Helvetica, Arial, sans-serif !important;}

/* Strip heavy margins & set premium workspace background */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1280px !important;
    background-color: #f8fafc !important;
}
div[data-testid="stVerticalBlock"] > div {gap: 0.6rem;}
h1 {font-size: 32px !important; font-weight: 700 !important; margin-bottom: 8px !important; color:#0f172a;
    letter-spacing: -0.03em !important;}
h2 {font-size: 17px !important; font-weight: 600 !important;}
h3 {font-size: 13px !important; font-weight: 700 !important; text-transform:uppercase; letter-spacing:0.03em;
    color:#475569 !important; margin-top: 0.4rem !important;}
.subtitle {color: #64748b; font-size: 16px; margin-bottom: 1.5rem;}
/* The one real source of "card" styling in the app: every intentional
   card (control strips, next_action, guardrail/journey/play/learnings
   entries) is a genuine st.container(border=True), so this single rule
   is the only place card visuals need to live. */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    background-color: #ffffff !important;
}

/* Premium B2B KPI Scorecard Grid — used by style.kpi_row(), a plain CSS
   grid of real divs instead of st.columns()+st.metric(), so the exact
   card visual (grid, shadow, padding) is fully our own rather than
   inherited from Streamlit's built-in metric widget. */
.kpi-row-layout {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
    margin-bottom: 2rem;
}
.kpi-card-custom {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

/* Spacing only for every st.columns() row — NOT a card. An earlier
   version of this rule also gave every stHorizontalBlock a white
   background + border + shadow, on the theory that it would fix the
   div-wrap control-strip bug described above. It did fix that, but it
   also indiscriminately carded EVERY OTHER columns() row in the app —
   chart-pair rows, guardrail rows, the button row inside next_action(),
   even the home page's row of 4 already-bordered tool cards — producing
   nested "card inside a card" artifacts (an extra white box floating
   inside an intentional one) and uneven spacing. The real, correct fix
   for a control strip's card look is to wrap THAT specific row in a
   genuine `st.container(border=True)` (see each page's control strip),
   which renders its own distinct, intentional container instead of
   piggybacking on every columns row in the app. */
div[data-testid="stHorizontalBlock"] {
    gap: 1.5rem !important;
}
/* Bottom-align each column's own content (label + widget) independently,
   rather than aligning the row as a single flex cross-axis block — this
   is what actually keeps a text label and a selectbox lined up at their
   baseline when neighboring columns have captions of different heights. */
div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
}

/* Widget labels as small uppercase micro-labels, matching the KPI card
   label treatment, instead of Streamlit's plain default text. */
div[data-testid="stWidgetLabel"] p {
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    color: #1e293b !important;
}

/* Soften rigid native element inputs. Streamlit selects/inputs fill
   100% of their column's width by design — fine in a narrow column, but
   in a wide one (e.g. a lone filter next to a big empty spacer column)
   that reads as the dropdown "stretching across the workspace." Capping
   the rendered box (not the outer wrapper, so column layout is
   untouched) keeps every input a sane, consistent width regardless of
   how wide its column happens to be. */
div[data-baseweb="select"], div[data-baseweb="input"] {
    border-radius: 6px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff !important;
}
div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
    max-width: 420px !important;
    background-color: #ffffff !important;
}
/* The rule above targets the OUTER select wrapper — but BaseWeb paints
   the actual visible fill on an INNER div one level down (the clickable
   value box), which for a *disabled* select (used by the locked "Scope
   Memory Context" placeholder, and the "no brands yet" state) gets its
   own muted gray fill + dimmed text that sits on top and hides the white
   set above. Force that inner layer white and full-strength too, so a
   disabled select still reads as a normal, intentional white box instead
   of a grayed-out/broken one. */
div[data-baseweb="select"] > div > div,
div[data-testid="stSelectbox"] [aria-disabled="true"] {
    background-color: #ffffff !important;
    color: #1e293b !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #1e293b !important;
}
div[data-testid="stSelectbox"],
div[data-testid="stSelectbox"] * {
    opacity: 1 !important;
}
/* Buttons get the same rounded, softened treatment — but NOT a forced
   background-color, since that would flatten primary CTA buttons
   (type="primary") to white along with everything else. */
.stButton button {
    border-radius: 6px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.05s ease;
}
.stButton button:active {
    transform: scale(0.98);
}

/* st.metric still appears in a couple of places outside kpi_row (e.g.
   third-party components); keep it card-styled too so it never looks
   like a bare, un-themed widget if it shows up. */
div[data-testid="stMetric"] {
  background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px;
}
div[data-testid="stMetricValue"] {font-size: 26px !important; font-weight: 700 !important; color:#1e293b;}
div[data-testid="stMetricLabel"] {font-size: 12px !important; color:#94a3b8 !important; font-weight:600;
  text-transform:uppercase; letter-spacing:0.02em;}

.gs-badge {display:inline-block; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; margin-bottom:6px;}
.gs-badge-teal {background:#ecfdf5; color:#10b981;}
.gs-badge-coral {background:#fef2f2; color:#ef4444;}
.gs-badge-amber {background:#fffbeb; color:#d97706;}
.gs-badge-accent {background:#eef2ff; color:#6366f1;}
.gs-badge-muted {background:#f1f5f9; color:#94a3b8;}
.gs-badge-blue {background:#eff6ff; color:#3b82f6;}

/* Thin separator above the "Open Tools ↗" link on home-page tool cards,
   matching the mockup's card-action-row border-top — a standalone rule
   element, not a wrapping div, so it doesn't hit the div-wrap bug. */
.gs-card-divider {border-top: 1px solid #f1f5f9; margin-top: 0.9rem; padding-top: 0.1rem;}

/* Compact inline status pill — replaces static "nothing found" boxes
   with a single-line acknowledgement that doesn't eat vertical space. */
.gs-pill {display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
  padding:5px 12px; border-radius:20px; margin: 4px 0 10px 0;}
.gs-pill-ok {background:#ecfdf5; color:#10b981;}
.gs-pill-warn {background:#fffbeb; color:#d97706;}
.gs-pill-muted {background:#f1f5f9; color:#94a3b8;}

.gs-flow-banner {display:flex; align-items:center; gap:10px; background:#eef2ff; color:#3730a3;
  border-radius:8px; padding:12px 16px; font-size:13px; margin:10px 0; border:1px solid #c7d2fe;}
/* Readable AI narrative card — line-height + a distinct headline style
   are what actually fix a "wall of text" (tight default line-height on
   a long unbroken paragraph), not hiding content behind a line-clamp.
   Every agent_card() call bolds its lead sentence via markdown (**text**),
   which st.markdown renders as a real <strong> even inside this raw div,
   so styling that tag gives every card a clear headline/detail hierarchy
   for free without touching each page's call site. */
.gs-agent-card {
    border:1px solid #e2e8f0; border-radius:10px; padding:16px 20px;
    margin-bottom:10px; background:#fff; line-height:1.6; font-size:13.5px; color:#334155;
}
.gs-agent-card strong {
    display:block; font-size:15px; color:#1e293b; margin-bottom:8px; line-height:1.4;
}
.gs-agent-label {font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; color:#94a3b8; margin-bottom:8px;}
.gs-stage-msg {background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 12px; font-size:13px; margin-top:6px;}
.gs-offline {text-align:center; padding: 4rem 1rem; color:#475569;}

.gs-zone {font-size:13px; font-weight:600; padding:4px 0;}
.gs-zone-safe {color:#10b981;}
.gs-zone-kill {color:#ef4444;}

.gs-empty {text-align:center; color:#94a3b8; font-size:13px; padding:2.5rem 1rem;
  border:1px dashed #e2e8f0; border-radius:10px; margin-top:0.5rem;}

.gs-step-day {display:inline-flex; align-items:center; justify-content:center; min-width:52px;
  height:52px; border-radius:10px; background:#eef2ff; color:#6366f1; font-weight:700;
  font-size:13px; text-align:center; line-height:1.15;}

/* ── Dark sidebar theme ───────────────────────────────────────────────
   Mirrors the mockup's slate-900 <aside>: dark panel, gradient wordmark,
   muted nav text that brightens on hover, and a left-border indigo
   accent on whichever page link Streamlit marks as current via
   aria-current="page" (it does this natively — no extra state needed). */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b;
}
section[data-testid="stSidebar"] * {
    color: #cbd5e1;
}
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-size: 21.6px !important;
    font-weight: 700 !important;
    text-transform: none !important;
    letter-spacing: -0.4px !important;
    margin-top: 0 !important;
}
/* Mockup renders the wordmark as two solid-color spans ("Growth" white,
   "Suite" indigo), not a gradient — this is the exact color it uses. */
section[data-testid="stSidebar"] h3 span {
    color: #818cf8 !important;
}
section[data-testid="stSidebar"] hr {border-color: #1e293b !important;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] small {
    color: #94a3b8 !important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"] {
    border-radius: 8px;
    margin-bottom: 2px;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"] p {
    color: #94a3b8 !important;
    font-weight: 500 !important;
    font-size: 15px !important;
}
section[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
    background: rgba(255,255,255,0.02) !important;
}
section[data-testid="stSidebar"] a[aria-current="page"] {
    background: rgba(255,255,255,0.06) !important;
    border-left: 4px solid #6366f1 !important;
    border-radius: 0 8px 8px 0 !important;
}
section[data-testid="stSidebar"] a[aria-current="page"] p {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ── Segmented control (Data Source Mode toggle) ─────────────────────
   Streamlit's native st.segmented_control already renders as a bordered
   pill group; these are light touch-ups so it reads as one connected
   toggle instead of three loose buttons. Forcing nowrap here is a
   safety net on top of giving the widget a wide enough column: without
   it, the three options silently stack into separate full-width rows
   whenever the column is too narrow, instead of shrinking — that's the
   "three stacked buttons" bug seen when this column was too tight. */
div[data-testid="stSegmentedControl"] {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 2px;
    background: #ffffff;
}
div[data-testid="stSegmentedControl"] > div {
    flex-wrap: nowrap !important;
}
div[data-testid="stSegmentedControl"] button {
    font-size: 13px !important;
    padding: 6px 12px !important;
    white-space: nowrap !important;
}

/* ── Native file uploader restyle ─────────────────────────────────────
   Reskins Streamlit's real dropzone (still fully functional) to match
   the mockup's dashed drop area instead of building a fake HTML one
   that wouldn't actually accept a file. */
div[data-testid="stFileUploaderDropzone"] {
    background: #f8fafc !important;
    border: 2px dashed #cbd5e1 !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #6366f1 !important;
}

/* ── Connected control-strip + upload-drawer panel (Funnel Diagnostics
   upload modes) — one real st.container(border=True) styled so its
   dashed internal divider reads as the seam between "controls" and
   "drop your file here", matching the mockup's two-part card. */
.gs-drawer-seam {
    border-top: 1px dashed #e2e8f0;
    margin: 1rem 0 1rem 0;
}
</style>
"""

VERDICT_COLOR = {"SHIP": "teal", "KILL": "coral", "EXTEND": "amber"}
IMPACT_COLOR = {"High": "teal", "Medium": "amber", "Low": "muted"}


def inject():
    st.set_page_config(page_title="Growth Suite", page_icon="\U0001F4C8", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


NAV_PAGES = [
    ("app.py", "Overview"),
    ("pages/1_Funnel_Diagnostics.py", "Funnel Diagnostics"),
    ("pages/2_Lifecycle_Architect.py", "Lifecycle Architect"),
    ("pages/3_Experiment_Designer.py", "Experiment Designer"),
    ("pages/4_Results_Learnings.py", "Results & Learnings"),
]


def sidebar():
    """Navigation only — the brand/workspace selector lives in each
    page's own horizontal control strip instead (see brand_selector()).
    Matches the reference mockup exactly: wordmark, then nav links
    directly underneath — no tagline caption, no divider, no icons."""
    with st.sidebar:
        st.markdown('### Growth<span>Suite</span>', unsafe_allow_html=True)
        for page, label in NAV_PAGES:
            st.page_link(page, label=label)


def brand_selector(label="Scope Memory Context", locked=False, locked_text="✨ My Custom Brand"):
    """Renders inline as one column of a page's horizontal control
    strip. When `locked`, swaps to a disabled ghost placeholder instead
    of the real dropdown. Returns the resolved brand_id, or None while
    locked or if no brands exist yet."""
    from . import data as _data

    if locked:
        # A real disabled st.selectbox, not a hand-styled div standing in
        # for one. Two rounds of hand-tuned CSS (.gs-fake-widget-label +
        # .gs-ghost-brand) still drifted out of alignment with the real
        # selects next to it, because a div can never be guaranteed to
        # match Streamlit's internal widget box model exactly. A real
        # (disabled) selectbox is bit-for-bit the same component as every
        # other selectbox in the row, so it lines up by construction —
        # this bug class is now closed for good.
        st.selectbox(label, [locked_text], disabled=True)
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
    workspace has produced a real result."""
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
            if not name.strip():
                st.error("Give the workspace a name first.")
            else:
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


def kpi_row(items):
    """Executive scorecard grid. `items` is a list of dicts:
    {"label": str, "value": str, "delta": str (optional), "positive": bool|None}.
    `positive=True` renders a green ↑, `False` a red ↓, `None`/omitted
    renders the delta text in neutral slate with no arrow. Built as one
    single st.markdown() call (no split div-wrap), so unlike the old
    control-strip bug, this one actually renders as a real card grid."""
    cards = []
    for item in items:
        delta = item.get("delta")
        positive = item.get("positive")
        delta_html = ""
        if delta:
            if positive is True:
                delta_html = f'<div style="color:#10b981; font-size:13px; font-weight:600; margin-top:4px;">↑ {delta}</div>'
            elif positive is False:
                delta_html = f'<div style="color:#ef4444; font-size:13px; font-weight:600; margin-top:4px;">↓ {delta}</div>'
            else:
                delta_html = f'<div style="color:#94a3b8; font-size:13px; font-weight:600; margin-top:4px;">{delta}</div>'
        cards.append(
            '<div class="kpi-card-custom">'
            f'<div style="font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.02em; color:#94a3b8;">{item["label"]}</div>'
            f'<div style="font-size:28px; font-weight:700; color:#1e293b; margin-top:6px;">{item["value"]}</div>'
            f'{delta_html}'
            '</div>'
        )
    st.markdown(f'<div class="kpi-row-layout">{"".join(cards)}</div>', unsafe_allow_html=True)


_NO_PDF = object()


def next_action(text, button_label=None, button_page=None, button_state=None, pdf_url=_NO_PDF, extra=None):
    """Unified 'Next Playbook Action' container — every tool page ends
    with exactly one of these instead of a loose flow_banner + scattered
    buttons."""
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


# ── State-bug guard ──────────────────────────────────────────────────
# A cached result (e.g. st.session_state["funnel_result"]) used to keep
# showing a stale dashboard after the brand/workspace selector changed,
# because nothing ever invalidated it — the page would happily display
# Brand A's diagnosis while the dropdown read "Brand B". remember_result
# tags a cached result with the brand it was computed for; stale_guard
# clears it the moment that tag stops matching the current selection.
def remember_result(key, value, brand_id):
    st.session_state[key] = value
    st.session_state[f"{key}__brand"] = brand_id


def stale_guard(key, brand_id):
    tracker = f"{key}__brand"
    if key in st.session_state and st.session_state.get(tracker) != brand_id:
        del st.session_state[key]
        st.session_state.pop(tracker, None)
