# n8n build guide

## What's provided as ready-to-import JSON

- `memory-retrieve.json` — shared sub-workflow. Reads recent diagnoses, journeys, and experiments+results for a `brand_id` from Supabase, compacts them into a short `memory_context` string.
- `memory-write.json` — shared sub-workflow. Generic insert: takes `{ table, record }` and writes it to the given Supabase table.
- `funnel-diagnostics.json` — full reference workflow: webhook → memory retrieve → deterministic analytics (Code node) → six sequential Groq agents (Interpreter → Anomaly Explainer → Root Cause → Benchmark Commentary → Segment Insight → Prioritization & Play Designer) → Narrative Synthesis → compile → memory write → respond.

## Import steps

1. In n8n: Workflows → Import from File → select `memory-retrieve.json`, then `memory-write.json`. Note the workflow ID n8n assigns each (visible in the URL after opening it).
2. Import `funnel-diagnostics.json`. Open its **Memory: Retrieve** and **Memory: Write** nodes and replace the placeholder values `MEMORY_RETRIEVE_WORKFLOW_ID` / `MEMORY_WRITE_WORKFLOW_ID` with the real IDs from step 1.
3. Set environment variables on the n8n instance: `SUPABASE_URL`, `SUPABASE_KEY` (service role key), `GROQ_API_KEY`.
4. Copy the Webhook node's production URL into the frontend's `N8N_WEBHOOK_FUNNEL` env var.
5. Leave the workflow **Inactive** until you're ready to demo — see the kill switch note in the top-level README.

## Replicating the pattern for the other three workflows

Each of these follows the exact same shape as `funnel-diagnostics.json`: Webhook → Memory: Retrieve → one Code node with the deterministic math → a sequential chain of Groq HTTP Request agent nodes → a compile Code node → Memory: Write → Respond to Webhook. Duplicate `funnel-diagnostics.json` in the n8n UI and swap the pieces below.

### Lifecycle Architect (`N8N_WEBHOOK_LIFECYCLE`)

**Deterministic Code node** — trigger-day calculator: category defaults, repeat-gap inference, discount-timing rules (port from the original `rules.py` logic). Also compute the illustrative engagement funnel (open rate → click rate → conversion using labeled industry-typical rates).

**Agent chain, in order:**
1. Stage Copywriter — one call per journey stage (loop with a Split In Batches node over the stage list, or five near-identical HTTP Request nodes if you'd rather see them individually in the canvas). Writes the WhatsApp message for that stage.
2. Tone Scoring — scores warmth/urgency for each stage's message, returns JSON.
3. Rationale — writes the "why here" line per stage, grounded in the trigger-day math and any imported diagnosis in `memory_context`.
4. Benchmark Commentary — compares this journey's cadence to category-typical timing.
5. Variant Generator — 2-3 alternate copy options per stage.
6. Narrative Synthesis — ties the full journey together.

**Compile node** builds the same shape as `SAMPLE_RESULTS["lifecycle_architect"]` in `lib/data.py`: `stages[]` (each with `day, name, channel, message, rationale, tone_score, variants`), `engagement_funnel[]`, `cadence_benchmark`, `narrative.synthesis`.

**Memory: Write** target table: `lifecycle_journeys`.

### Experiment Designer (`N8N_WEBHOOK_EXPERIMENT`)

**Deterministic Code node** — two-proportion z-test sample size and duration (port from `stats.py`), plus the power curve (sample size at MDE = 1-6pp) and the 80%/90% power tradeoff series.

**Agent chain, in order:**
1. Guardrail Designer — proposes 3 hypothesis-specific guardrail metrics with safe/kill zones.
2. Risk Assessment — reasons about likely failure modes for this specific mechanism.
3. Similar-Experiment Analyst — reads `memory_context` for comparable past experiments and summarizes what happened.
4. Decision Rule Drafting — writes the SHIP/EXTEND/KILL thresholds, using the already-computed MDE.
5. Narrative Synthesis — combines stats, guardrails, risk, and history into one summary.

**Compile node** builds the shape of `SAMPLE_RESULTS["experiment_designer"]`: `spec` (including `power_curve`), `guardrails[]`, `decision_rule`, `historical_outcomes[]` (pull straight from the memory lookup), `narrative`.

**Memory: Write** target table: `experiments`.

### Results & Learnings (`N8N_WEBHOOK_RESULTS`)

This one is different: the grading step is a **Code node, not an LLM call** — deliberately. Given `experiment_id` and actual metrics, fetch the original `spec`/`decision_rule` from Supabase, compare actuals against the thresholds in plain JavaScript, and output `SHIP` / `KILL` / `EXTEND`. Only after that:

1. Takeaway Writer (Groq) — a short "what we learned / what to try next" paragraph, given the verdict and the actual numbers.
2. Pattern Recognition (Groq) — reads all past `experiment_results` for the brand/category from `memory_context` and surfaces a recurring pattern, if any.

**Compile node** appends the graded result and writes to `experiment_results`, then returns the shape of `SAMPLE_RESULTS["results_learnings"]` (`history[]`, `verdict_distribution`, `cumulative_impact_pp[]`, `themes[]`, `narrative.pattern_recognition`) by also querying the brand's full history for the charts.

## A note on the parallel-agent temptation

It's tempting to fan the deterministic output out to all the agent nodes at once so they run in parallel and finish faster. Don't wire it that way without a proper Merge node configured to wait for every branch — a naive fan-out where multiple nodes point at the same next node just causes that node to fire once per incoming branch, not once with everything merged. The sequential chain used here is slower but guaranteed correct, and it mirrors the proven pattern the original Funnel Diagnostics tool already used (Interpreter → Root Cause → Prioritization → Play Designer → Compiler).

## PDF export

Add a PDF.co "Generate PDF" HTTP Request node (`https://api.pdf.co/v1/pdf/convert/from/html`, header `x-api-key: {{$env.PDFCO_API_KEY}}`) right before **Memory: Write** in all four workflows, feeding it the compiled narrative as HTML. Store the returned URL in the record's `pdf_url` field.
