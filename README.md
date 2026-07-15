# Growth Suite

One URL, four tools: Funnel Diagnostics, Lifecycle Architect, Experiment Designer, and Results & Learnings. Deterministic math is computed in code, AI reasons expansively on top of it through named agent chains in n8n, and everything is scoped to a brand in a shared Supabase memory layer.

Runs fully in **demo mode** out of the box — no Supabase or n8n required to see every page, every chart, and every AI-agent narrative, using bundled sample data that mirrors two seeded fictional brands (`sql/seed.sql`). Wire in real infra when you're ready; nothing needs to change in the frontend.

## Run locally

```
cd growth-suite
pip install -r requirements.txt
streamlit run app.py
```

Opens in demo mode automatically since no webhook URLs are set.

## Wire up the real thing

1. **Supabase** — create a project, run `sql/schema.sql` then `sql/seed.sql` in the SQL editor. Copy the project URL and service-role key into `.env` (`SUPABASE_URL`, `SUPABASE_KEY`).
2. **n8n** — follow `n8n/BUILD_GUIDE.md`. Import the two memory sub-workflows and `funnel-diagnostics.json` as-is; build the other three workflows by duplicating that pattern per the guide. Copy each workflow's webhook URL into the matching `.env` variable (`N8N_WEBHOOK_FUNNEL`, `N8N_WEBHOOK_LIFECYCLE`, `N8N_WEBHOOK_EXPERIMENT`, `N8N_WEBHOOK_RESULTS`).
3. **Deploy** — Render → New → Web Service → connect this repo. Build command `pip install -r requirements.txt`, start command `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`. Add the same env vars from `.env`.

## The kill switch

Two layers, use both:

- **n8n Active/Inactive toggle** (the one that matters for cost) — flip each of the four workflows to Inactive when you're not demoing. Their webhooks stop responding, so no Groq or PDF.co call can fire, at zero cost. Flip them Active again right before you need it.
- **Supabase `app_settings.is_live`** (the one that matters for a stray visitor's experience) — set to `false` and every page shows a clean "this demo is currently offline" message instead of a broken form. Toggle it directly in Supabase's table editor, no redeploy needed.

## Project layout

```
app.py                     home hub, brand selector, kill-switch gate
pages/
  1_Funnel_Diagnostics.py
  2_Lifecycle_Architect.py
  3_Experiment_Designer.py
  4_Results_Learnings.py
lib/
  style.py                 shared design system
  data.py                  webhook caller + demo-mode sample data
  charts.py                every chart, plotly
  ingest.py                order-level CSV parsing + metrics-snapshot form → real computed_stats
sql/
  schema.sql
  seed.sql                 two fictional brands, ~2 months of fabricated history
n8n/
  memory-retrieve.json      importable
  memory-write.json         importable
  funnel-diagnostics.json   importable, full reference workflow
  BUILD_GUIDE.md            how to build the other three from this pattern
```

## Real data in, not just demo data

Funnel Diagnostics accepts real input two ways, both computed deterministically in `lib/ingest.py` — no AI involved in turning your data into numbers:

- **Order-level data** — download the sample CSV for the expected columns (`customer_id, order_date, order_number, channel, revenue, discount_applied`), upload your own, and pandas computes real M1→M2 retention, cohort tables, discount dependency, and per-channel retention from it. Upper-funnel steps (Visit, Add to cart, Checkout) aren't derivable from order data alone — that funnel chart only shows Purchase → Repeat (M2) in this mode, and says so.
- **Metrics snapshot** — already know your headline numbers? Type them into the form instead of exporting a file. Cohort and weekly-trend detail become flat estimates off those headline numbers rather than fabricated detail, and the dashboard says so.

Either way, the real `computed_stats` flow through to n8n and the AI agents reason on your actual numbers, not the fixture. Demo mode (no upload) still uses the fixture so the whole chain stays exercisable with zero setup.

## Design principles carried through

- Every number is computed by code — cohort math, z-test sample sizes, trigger-day rules — never guessed by a model.
- AI is used expansively on top of those numbers: each tool runs a chain of distinctly-named agents (interpreter, anomaly explainer, benchmark commentary, risk assessment, similar-experiment analyst, narrative synthesis) rather than one generic call.
- Grading a shipped experiment's outcome is the one place AI usage stays at zero — that verdict is decided by code comparing actuals against a threshold someone already committed to.
- Every tool shows its full dashboard of charts and agent analysis before showing a recommendation.
