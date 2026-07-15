# Growth Suite — Architecture Review

Written after taking the system from local demo to a live deployment (Streamlit on Render, four n8n Cloud workflows, Supabase, Groq, PDF.co). This is a candid pass over what's solid, what's fragile, and what's outright missing — organized by how much it should worry you, not by which layer it's in.

## The one gap that undermines the product's own pitch

The README's core promise is a shared memory layer: "Experiment Designer can point at a similar experiment that already ran," and "Lifecycle Architect can ground a journey in a real diagnosis." That loop is real for the seeded demo data, but it's broken for anything a live user actually does.

Look at `pages/4_Results_Learnings.py`: the "Grade this experiment" button computes SHIP/KILL/EXTEND locally in Python and displays it — deliberately, correctly, without AI, per the README's own design principle. But it never writes that verdict anywhere. It doesn't call the `results_learnings` webhook, doesn't POST to Supabase, nothing. The dashboard below it and the Similar-Experiment Analyst agent in Experiment Designer are reading `experiment_results` rows that only ever came from `sql/seed.sql`. A visitor can grade twenty experiments today and the "memory" the product advertises won't reflect a single one of them tomorrow. This is the highest-value fix available: wire the grade button to actually persist through `Memory: Write`.

## Secrets are hardcoded in plaintext, not in n8n's credential store

Every n8n workflow node that calls Supabase, Groq, or PDF.co has the literal key pasted into its HTTP header parameters. This was a pragmatic call mid-build (n8n Cloud's `$env` access is restricted for custom variables, and it unblocked us fast), but it has real costs: anyone with access to the n8n workspace can read every key by opening any node; rotating a compromised key means manually editing it in roughly a dozen places across six workflow files instead of one credential; and it's *why* `n8n/*.json` had to be excluded from git entirely — GitHub's push protection already caught the Groq key once, and the Supabase service-role key (which bypasses row-level security) and PDF.co key would have been just as exposed if the scanner's pattern-matching had caught them too. The fix is mechanical: create three n8n Credentials (HTTP Header Auth) once, and point every node at the credential instead of a literal string. Worth doing before this ever handles anything beyond demo data.

## The webhooks have no authentication at all

The four webhook URLs are unauthenticated public POST endpoints. The path names are predictable, not secret. Anyone who finds one can call it directly — bypassing the Streamlit app, bypassing the `app_settings.is_live` kill switch entirely (that flag only gates the frontend, not the webhook), and running up real Groq and PDF.co charges with no rate limit and no ceiling. The n8n Active/Inactive toggle is the only real stop, and that requires you to notice and act. A cheap fix: an IF node at the top of each workflow checking a shared-secret header the frontend sends, with the value stored in `.env`/Render env vars, not the URL itself.

## PDF export and downstream writes have no failure isolation

In every workflow, `Attach PDF URL` runs unconditionally after `PDF Export` — there's no branch for a PDF.co error, timeout, or malformed response. If PDF.co has a bad day, `$json.url` comes back `undefined`, `pdf_url` silently becomes an empty string, and nothing surfaces that anything went wrong; the record still writes, the webhook still responds "successfully." Multiply that by four workflows and it's an invisible failure mode a user would only notice by clicking a dead Export PDF link. Same story for `Memory: Write`: there's no retry and no idempotency key, so a retried or double-clicked request creates duplicate Supabase rows with nothing to tell them apart later.

## The frontend/backend contract is duplicated by hand, with nothing enforcing it matches

`lib/data.py`'s `SAMPLE_RESULTS` and each n8n workflow's `Compile Response` node both independently define the exact JSON shape the frontend expects — twice, by hand, with no shared schema. We hit this directly during the build: `charts.sample_size_tradeoff()` crashed in production because the shape being passed didn't match what the function assumed, a bug that had nothing to do with n8n and had clearly never been exercised end-to-end before. There's no contract test catching this class of drift, and there's no `JSON.parse()` error handling in any Compile Response node — if a Groq call ever returns malformed JSON (a model hiccup, a truncated response), the whole webhook throws an unhandled exception with no graceful fallback.

## Zero automated tests, minimal observability

Nothing is under test: not the deterministic math (z-test sample sizes, cohort retention math), not the chart builders, not the n8n Code nodes' parsing logic. The only execution history is n8n's own Executions tab (finite retention on this plan) and Render's basic request logs — no structured logging, no failure-rate alerting, no cost tracking for Groq/PDF.co spend. If this ran unattended for a week, a broken workflow or a runaway cost spike would surface only when someone happened to look, or when a demo failed live.

## Smaller, real gaps worth knowing about

The `experiments.journey_id` column exists specifically to link an experiment back to the lifecycle journey that produced it, but the "Send to Experiment Designer" flow only ever passes a hypothesis string — the column is schema-ready and never populated, so that relationship never actually gets wired end to end. Separately, Render's free tier spins down after ~15 minutes idle and takes 30-50 seconds to cold-start on the next request — fine for a portfolio piece, worth knowing before pointing a live demo audience at it cold. And the deployed app has no login; that's presumably intentional given the kill-switch design, but it's worth being a deliberate choice rather than an assumption.

## What's actually solid

Worth naming, since a review that's all gaps is as misleading as one that's none: the demo/live fallback in `call_workflow()` is a genuinely good resilience pattern — a live outage degrades to sample data instead of a broken page, and it's why this app never fully broke even mid-build. The deterministic-vs-AI split is a real, consistently-followed design principle, not just README marketing — every number traces to code, every narrative traces to a named agent, and grading is the one place that's correctly kept AI-free end to end. And the brand-scoped memory model (`brand_id` threading through every table) is a clean foundation — the gap isn't the schema, it's that one write path into it never got connected.

## If I had to pick three things to fix next

1. Wire `Results & Learnings`' grade button to actually persist to Supabase — the memory loop is the whole pitch, and it's currently a demo-only illusion.
2. Move the three hardcoded API keys into n8n Credentials — mechanical, low-risk, and removes the reason `n8n/*.json` can't be versioned safely.
3. Add a shared-secret header check on the four webhooks — an afternoon of work that closes the biggest unbounded-cost exposure in the whole system.
