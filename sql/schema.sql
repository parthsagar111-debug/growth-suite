-- Growth Suite — Supabase schema
-- Run once against a new Supabase (Postgres) project.

create extension if not exists "uuid-ossp";

-- ── App-wide kill switch ─────────────────────────────────────────────
create table if not exists app_settings (
  key text primary key,
  value boolean not null default true,
  updated_at timestamptz not null default now()
);
insert into app_settings (key, value) values ('is_live', true)
  on conflict (key) do nothing;

-- ── Brands (the memory-scoping key for everything) ──────────────────
create table if not exists brands (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  category text not null,
  discount_stance text not null default 'discount-light',
  created_at timestamptz not null default now()
);

-- ── Funnel Diagnostics ────────────────────────────────────────────────
create table if not exists funnel_diagnoses (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid references brands(id) on delete cascade,
  input_mode text not null check (input_mode in ('metrics_snapshot','order_level')),
  computed_stats jsonb not null,          -- deterministic engine output
  diagnosed_leak text,
  ranked_plays jsonb,                      -- array of {title, impact, rationale}
  narrative jsonb,                         -- interpreter/root-cause/benchmark/segment/synthesis text
  pdf_url text,
  created_at timestamptz not null default now()
);

-- ── Lifecycle Architect ───────────────────────────────────────────────
create table if not exists lifecycle_journeys (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid references brands(id) on delete cascade,
  diagnosis_id uuid references funnel_diagnoses(id),
  stages jsonb not null,                   -- array of {day, name, channel, message, rationale, tone_score, variants}
  narrative jsonb,
  pdf_url text,
  created_at timestamptz not null default now()
);

-- ── Experiment Designer ───────────────────────────────────────────────
create table if not exists experiments (
  id uuid primary key default uuid_generate_v4(),
  brand_id uuid references brands(id) on delete cascade,
  journey_id uuid references lifecycle_journeys(id),
  hypothesis text not null,
  baseline_rate numeric,
  mde numeric,
  daily_traffic integer,
  spec jsonb not null,                     -- sample_size, duration_days, power_curve points
  guardrails jsonb,                        -- array of {metric, why, safe_zone, kill_zone}
  decision_rule jsonb,                     -- {ship, extend, kill}
  narrative jsonb,
  pdf_url text,
  created_at timestamptz not null default now()
);

-- ── Results & Learnings ───────────────────────────────────────────────
create table if not exists experiment_results (
  id uuid primary key default uuid_generate_v4(),
  experiment_id uuid references experiments(id) on delete cascade,
  actual_metrics jsonb not null,           -- {lift_pp, opt_out_delta_pp, ...}
  verdict text check (verdict in ('SHIP','KILL','EXTEND')),
  takeaway text,
  created_at timestamptz not null default now()
);

create index if not exists idx_diag_brand on funnel_diagnoses(brand_id);
create index if not exists idx_journey_brand on lifecycle_journeys(brand_id);
create index if not exists idx_exp_brand on experiments(brand_id);
create index if not exists idx_result_exp on experiment_results(experiment_id);
