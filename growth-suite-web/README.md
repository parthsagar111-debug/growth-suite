# Growth Suite — web build (FastAPI + Jinja2 + HTMX)

A ground-up rebuild of the Growth Suite frontend, replacing Streamlit
with plain server-rendered HTML/CSS + HTMX. Same business logic, same
visual language, but full native control over layout — no more fighting
Streamlit's column min-width enforcement or BaseWeb's internal styling.

This is a **separate project** from `../` (the original Streamlit app),
living in its own folder so both can run independently. `../` keeps
working exactly as-is; nothing there was touched.

## Status

Built so far: **Overview** and **First Response**, matching the
Streamlit versions' content and behavior exactly (First Response uses
the same scripted, zero-latency demo walkthrough — no live Groq calls
in the default flow). The other four tools (Funnel Diagnostics,
Lifecycle Architect, Experiment Designer, Results & Learnings) are
"coming soon" stub pages for now — same build order as requested, one
phase at a time.

## Why this stack

- **FastAPI** — reuses `lib/decision_tree.py`, `lib/ai_diagnostic.py`,
  `lib/sample_scenario.py` from the Streamlit app verbatim (they have
  zero Streamlit dependency), and `lib/data.py` with only its caching
  and warning mechanism swapped out.
- **Jinja2 templates, server-rendered** — no separate REST API/frontend
  split to maintain; routes call the business logic directly and render
  HTML.
- **HTMX** — for the one genuinely interactive piece (clicking a First
  Response category swaps in its diagnosis without a full page reload)
  without needing a JS framework or build step.
- No React/npm/Node tooling — the whole project is Python + HTML/CSS,
  matching the stated preference for something maintainable without a
  frontend build pipeline.

## Run locally

```
cd growth-suite-web
pip install -r requirements.txt
uvicorn main:app --reload
```

Opens at `http://127.0.0.1:8000`.

## Project layout

```
main.py                    FastAPI app — routes for every page
lib/
  decision_tree.py          First Response's 10 decision trees (ported verbatim)
  ai_diagnostic.py          First Response's Groq calls (ported verbatim, not yet wired to a route)
  sample_scenario.py        First Response's scripted walkthrough data (ported verbatim)
  data.py                   webhook caller + demo-mode sample data (Streamlit dependency removed)
  cache.py                  tiny TTL-cache decorator, stands in for st.cache_data
templates/
  base.html                 shared shell — dark sidebar nav + content area
  overview.html              /
  first_response.html        /first-response (category grid)
  partials/
    fr_result.html           HTMX fragment — transcript + diagnosis for one category
  stub.html                  "coming soon" page for the four not-yet-built tools
static/
  css/style.css              full design system — same palette as the Streamlit app
```

## Design system

Same palette as the Streamlit app's `lib/style.py` (Indigo primary,
Emerald/Crimson/Amber/Blue accents, slate-900 dark sidebar), expressed
as CSS custom properties in `static/css/style.css` — see `:root` at the
top of that file for every token.

## What's next

1. Port `lib/charts.py` and `lib/ingest.py`.
2. Build Funnel Diagnostics (upload flow + full dashboard + AI narrative).
3. Build Lifecycle Architect, Experiment Designer, Results & Learnings.
4. Wire up real Supabase/n8n infra (optional — demo mode works out of
   the box, same as the original app).
5. Deploy as its own Render web service, separate from the Streamlit
   app's deployment. Build command `pip install -r requirements.txt`,
   start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
