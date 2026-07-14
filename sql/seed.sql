-- Growth Suite — demo seed data
-- Run once after schema.sql so the suite looks alive on first load.
-- Two fictional D2C brands with ~2 months of fabricated history.

insert into brands (id, name, category, discount_stance) values
  ('11111111-1111-1111-1111-111111111111', 'Verdant Skincare', 'D2C · Beauty & personal care', 'discount-light'),
  ('22222222-2222-2222-2222-222222222222', 'Hearth & Home Co', 'D2C · Home', 'discount-heavy')
on conflict (id) do nothing;

-- Verdant Skincare — funnel diagnosis
insert into funnel_diagnoses (id, brand_id, input_mode, computed_stats, diagnosed_leak, ranked_plays, narrative, created_at) values
('a1111111-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'order_level',
 '{"m1_m2_retention": 0.18, "discount_dependency": 0.41, "time_to_2nd_order_median_days": 34, "cohorts": [{"cohort":"Jan","m1":100,"m2":18,"m3":12,"m4":9},{"cohort":"Feb","m1":100,"m2":21,"m3":14,"m4":10},{"cohort":"Mar","m1":100,"m2":16,"m3":11,"m4":8}]}',
 'M1→M2 retention collapses to 18%, well under category benchmark, concentrated in the paid-social cohort and propped up by discount codes on 41% of repeats.',
 '[{"title":"WhatsApp win-back at day 35, no discount","impact":"High","rationale":"Fires before the M2 cliff, leads with education instead of a code."},{"title":"Bundle second-order incentive at checkout","impact":"Medium","rationale":"Seeds a non-monetary reason to return on order 1."},{"title":"Reduce discount depth on repeat codes","impact":"Medium","rationale":"Tests how price-elastic month-2 demand really is."}]',
 '{"interpreter":"Retention is being rented, not earned.","anomaly_explainer":"Feb cohort dips less steeply than Jan/Mar, coinciding with a smaller discount push.","benchmark_commentary":"Category benchmark for M1→M2 in beauty D2C sits near 27-32%; this brand is roughly 10pp under.","segment_insight":"Paid social cohort retains 6pp worse than organic.","synthesis":"The leak is a discount-dependent M2 cliff concentrated in paid social — fixable with earlier, code-free retention touchpoints."}',
 now() - interval '54 days');

-- Verdant Skincare — lifecycle journey (built from the diagnosis above)
insert into lifecycle_journeys (id, brand_id, diagnosis_id, stages, narrative, created_at) values
('b1111111-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'a1111111-0000-0000-0000-000000000001',
 '[{"day":0,"name":"Welcome","channel":"WhatsApp","message":"You are in — here is how to get the most out of your first order, no code needed.","rationale":"Sets product-education tone from day one.","tone_score":{"warmth":0.8,"urgency":0.1}},
   {"day":14,"name":"Habit-forming","channel":"WhatsApp","message":"How is it going so far? Here is a tip most first-timers miss.","rationale":"Reinforces value before the repeat window opens.","tone_score":{"warmth":0.75,"urgency":0.15}},
   {"day":28,"name":"At-risk","channel":"WhatsApp","message":"Running low? Reorder takes 30 seconds.","rationale":"Fires one week before the diagnosed M2 cliff at day 35.","tone_score":{"warmth":0.6,"urgency":0.4}},
   {"day":45,"name":"Lapsed","channel":"WhatsApp","message":"We miss you — no discount pitch, just checking in.","rationale":"Deliberately code-free to test true price elasticity.","tone_score":{"warmth":0.7,"urgency":0.3}},
   {"day":75,"name":"Win-back","channel":"WhatsApp","message":"Last call — here is a small thank-you for coming back.","rationale":"Only incentive-bearing stage, isolates true win-back cost.","tone_score":{"warmth":0.65,"urgency":0.6}}]',
 '{"synthesis":"Journey is intentionally code-light for four of five stages to test whether the M2 cliff is truly price-driven."}',
 now() - interval '50 days');

-- Verdant Skincare — experiment testing the day-28 play
insert into experiments (id, brand_id, journey_id, hypothesis, baseline_rate, mde, daily_traffic, spec, guardrails, decision_rule, narrative, created_at) values
('c1111111-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'b1111111-0000-0000-0000-000000000001',
 'Sending a day-28 no-discount WhatsApp nudge to at-risk customers will lift M2 repeat-purchase rate.',
 0.18, 0.03, 640,
 '{"sample_size_per_arm": 1240, "duration_days": 3.9, "confidence": 0.95, "power": 0.8}',
 '[{"metric":"WhatsApp opt-out rate","why":"Catches message fatigue","safe_zone":"< +1.5pp","kill_zone":">= +1.5pp"},{"metric":"Full-price order share","why":"Confirms lift is not pulled-forward discount demand","safe_zone":"flat or better","kill_zone":"drops"},{"metric":"Support ticket volume","why":"Flags unclear copy","safe_zone":"flat","kill_zone":"spikes"}]',
 '{"ship":"M2 lift >= 3pp with opt-out flat or better","extend":"Directionally positive but under-powered by day 4","kill":"Opt-out rises > 1.5pp regardless of lift"}',
 '{"risk_assessment":"Primary risk is message fatigue given this is the third WhatsApp touch in 28 days.","synthesis":"Small, fast test — the main watch item is opt-out rate, not statistical power."}',
 now() - interval '40 days');

-- Verdant Skincare — the experiment shipped, here is the graded result
insert into experiment_results (id, experiment_id, actual_metrics, verdict, takeaway, created_at) values
('d1111111-0000-0000-0000-000000000001', 'c1111111-0000-0000-0000-000000000001',
 '{"lift_pp": 3.4, "opt_out_delta_pp": 0.3, "support_tickets_delta": 0}',
 'SHIP',
 'The code-free at-risk nudge cleared the 3pp bar with opt-out well within tolerance — confirms the M2 cliff was retention-driven, not purely price-driven. Worth extending the same no-discount pattern to the lapsed-stage message.',
 now() - interval '30 days');

-- Hearth & Home Co — a second brand with a KILLed experiment, for variety
insert into funnel_diagnoses (id, brand_id, input_mode, computed_stats, diagnosed_leak, ranked_plays, narrative, created_at) values
('a2222222-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222', 'metrics_snapshot',
 '{"activation_rate": 0.52, "checkout_completion": 0.61, "delta_vs_prior_period": -0.06}',
 'Checkout completion dropped 6pp period over period, concentrated in mobile web.',
 '[{"title":"Simplify mobile checkout to 2 steps","impact":"High","rationale":"Mobile drop-off is 2x desktop."},{"title":"Add saved-address autofill","impact":"Medium","rationale":"Reduces manual entry friction."}]',
 '{"synthesis":"A mobile checkout regression, not a demand problem — activation is flat."}',
 now() - interval '25 days');

insert into experiments (id, brand_id, hypothesis, baseline_rate, mde, daily_traffic, spec, guardrails, decision_rule, narrative, created_at) values
('c2222222-0000-0000-0000-000000000001', '22222222-2222-2222-2222-222222222222',
 'Reducing mobile checkout from 4 steps to 2 will lift checkout completion rate.',
 0.61, 0.05, 1200,
 '{"sample_size_per_arm": 980, "duration_days": 2.1, "confidence": 0.95, "power": 0.8}',
 '[{"metric":"Cart abandonment rate","why":"Confirms simplification is not just moving the drop-off point","safe_zone":"flat or better","kill_zone":"worsens"},{"metric":"Refund rate","why":"Fewer steps could mean more accidental orders","safe_zone":"< +1pp","kill_zone":">= +1pp"}]',
 '{"ship":"Completion lift >= 5pp with refund rate flat","extend":"Positive but under-powered","kill":"Refund rate rises >= 1pp"}',
 '{"synthesis":"Low-risk UI test, main watch item is accidental-order refunds."}',
 now() - interval '18 days');

insert into experiment_results (id, experiment_id, actual_metrics, verdict, takeaway, created_at) values
('d2222222-0000-0000-0000-000000000001', 'c2222222-0000-0000-0000-000000000001',
 '{"lift_pp": 2.1, "refund_rate_delta_pp": 1.8}',
 'KILL',
 'Completion rate did lift, but refund rate rose past the guardrail — the shorter flow was letting through accidental orders. Next iteration should keep the 2-step flow but add an order-review screen before the refund-prone step is removed.',
 now() - interval '10 days');
