"""
First Response — the 10 diagnostic decision trees, as real Python data
structures instead of freeform AI prompting.

This is the actual product. Every check, branch, outcome, and handoff
rule below is a deterministic fact the AI is not allowed to override —
its job (see ai_diagnostic.py) is narrow: classify a free-text answer
into one of the branch keys defined here, judge whether enough signal
has accumulated to stop, and phrase the question/diagnosis in natural
language using the outcome text already written below. It never
invents a new branch, a new diagnosis, or a new handoff on the fly.

Source: first_response_decision_trees.md (all 10 trees + the cross-tree
principles section). Two corrections applied per direct confirmation:
  - The doc's "Retention Autopsy" handoff target does not exist in this
    build — it's Funnel Diagnostics (already a real page in this app),
    substituted everywhere the source doc says "Retention Autopsy."
  - "Experiment Designer" is also a real page in this same app, so that
    handoff is an in-app link, not an external one.

Handoff logic beyond what the source doc states explicitly (which only
names a handoff for tree 3 and tree 5) was extended per instruction —
those additions are marked "judgment call, not from source doc" in the
comments below so they're easy to find and adjust later.

Ported verbatim from the Streamlit app's lib/decision_tree.py — zero
framework dependency, so this file is byte-for-byte identical across
both projects.
"""

MAX_QUESTIONS = 5

HANDOFF_TARGETS = {
    "experiment_designer": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py"},
    "funnel_diagnostics": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py"},
}

# Order matches the mockup's category grid exactly.
CATEGORY_ORDER = [
    "page_views", "engagement", "conversion", "revenue", "repeat_rate",
    "aov", "cart_abandon", "search_conv", "payment_success", "performance",
]

TREES = {

    # ── 1. Page Views / Traffic ─────────────────────────────────────────
    "page_views": {
        "name": "Page Views", "icon": "📄", "metric_tag": "Traffic",
        "checks": [
            {
                "id": "tracking", "label": "Tracking",
                "question": "Any deploy, tag change, or GA4/GTM update in the last 7 days?",
                "boring_gate": True,
                "branches": {
                    "yes": {"note": "tracking change confirmed — suspect a break before anything else",
                            "outcome": "a tracking break — a bad tag fire, a broken GA4/GTM config, or a "
                                       "misfired event — rather than a real drop in visitors",
                            "terminal": True},
                    "no": {"note": "tracking ruled out, now isolating where it's happening",
                           "outcome": None, "terminal": False},
                },
            },
            {
                "id": "concentration", "label": "Concentration",
                "question": "Is the drop uniform across devices, or concentrated on one — mobile or desktop?",
                "branches": {
                    "mobile": {"note": "device isolated to mobile, narrowing to acquisition source",
                               "outcome": None, "terminal": False},
                    "desktop": {"note": "device isolated to desktop, narrowing to acquisition source",
                                "outcome": None, "terminal": False},
                    "uniform": {"note": "not device-specific — likely a broader, real pattern",
                                "outcome": None, "terminal": False},
                },
            },
            {
                "id": "channel", "label": "Channel",
                "question": "Within that, which channel dropped — organic, paid, direct, or referral?",
                "branches": {
                    "organic": {"note": "narrowed to organic", "outcome": "check Search Console for "
                                "indexing or ranking drops", "terminal": False},
                    "paid": {"note": "narrowed to paid", "outcome": "check for a paused campaign or "
                             "exhausted budget", "terminal": False},
                    "direct": {"note": "narrowed to direct", "outcome": None, "terminal": False},
                    "referral": {"note": "narrowed to referral", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "comparison_window", "label": "Comparison window",
                "question": "Is this down vs. the same day last week AND last month, or just one of those?",
                "branches": {
                    "only_last_week": {"note": "only down vs. last week", "outcome": "likely day-of-week "
                                        "noise, not a real trend", "terminal": True},
                    "both": {"note": "down vs. both windows — more likely a real trend", "outcome": None,
                              "terminal": False},
                },
            },
            {
                "id": "compliance", "label": "Local/compliance",
                "question": "Any recent consent-banner, cookie policy, or DPDP-related change?",
                "branches": {
                    "yes": {"note": "consent/compliance change confirmed", "outcome": "consent-mode "
                            "changes silently suppress GA4 sessions — check unconsented traffic isn't "
                            "being undercounted", "terminal": True},
                    "no": {"note": "no compliance change", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "A mobile+direct-only drop with everything else flat almost never indicates "
                               "a genuine demand decline — direct traffic doesn't behave that way on its "
                               "own. It usually points to a broken deep link, an app tracking SDK issue, or "
                               "a silent GA4 consent-mode change.",
        "default_handoff": None,
    },

    # ── 2. Engagement ────────────────────────────────────────────────────
    "engagement": {
        "name": "Engagement", "icon": "⏱️", "metric_tag": "Time / Bounce",
        "checks": [
            {
                "id": "bot_spam", "label": "Bot/spam filter",
                "question": "Any spike in sessions with 0-second duration or single-page bounces from "
                             "unfamiliar geographies?",
                "boring_gate": True,
                "branches": {
                    "yes": {"note": "bot/spam spike confirmed", "outcome": "bot/spam traffic inflating "
                            "session count and dragging down average engagement metrics", "terminal": True},
                    "no": {"note": "not a bot/spam issue, keep isolating", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "content_change", "label": "Content change",
                "question": "Was a page redesigned, a hero banner changed, or content removed in the "
                             "affected period?",
                "branches": {
                    "yes": {"note": "a content change happened in-window", "outcome": "check whether the "
                            "removed content was what people were actually engaging with — don't assume "
                            "the redesign is neutral", "terminal": False},
                    "no": {"note": "no content change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "page_concentration", "label": "Page-level concentration",
                "question": "Is the drop sitewide, or concentrated on specific page types — PDP, blog, "
                             "homepage?",
                "branches": {
                    "concentrated": {"note": "concentrated on specific page types", "outcome": "investigate "
                                     "that page type specifically, not the whole site", "terminal": False},
                    "sitewide": {"note": "sitewide, not page-specific", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "new_user_mix", "label": "New user mix",
                "question": "Has the new-vs-returning visitor ratio shifted toward more first-time visitors?",
                "branches": {
                    "yes": {"note": "more first-time visitors in the mix", "outcome": "this may be a "
                            "mix-shift artifact from a successful acquisition campaign, not declining "
                            "content quality", "terminal": False},
                    "no": {"note": "visitor mix unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "site_speed", "label": "Site speed",
                "question": "Any recent increase in page load time or Core Web Vitals scores?",
                "branches": {
                    "yes": {"note": "load time regressed — this is really a Performance question",
                            "outcome": "slow pages suppress engagement independent of content quality",
                            "terminal": False, "redirect_tree": "performance"},
                    "no": {"note": "load time unchanged", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "Engagement average dropping because a successful acquisition campaign "
                               "brought in colder, lower-intent traffic — not a quality problem.",
        "default_handoff": None,
    },

    # ── 3. Conversion Rate ───────────────────────────────────────────────
    "conversion": {
        "name": "Conversion", "icon": "🎯", "metric_tag": "PDP→Cart",
        "checks": [
            {
                "id": "funnel_stage", "label": "Funnel stage isolation",
                "question": "Which specific step dropped — PDP view→Add to Cart, Cart→Checkout start, or "
                             "Checkout→Purchase?",
                "branches": {
                    "pdp_to_cart": {"note": "isolated to PDP→Cart", "outcome": None, "terminal": False},
                    "cart_to_checkout": {"note": "isolated to Cart→Checkout", "outcome": None, "terminal": False},
                    "checkout_to_purchase": {"note": "isolated to Checkout→Purchase", "outcome": None,
                                              "terminal": False},
                },
            },
            {
                "id": "payment_errors", "label": "Payment/checkout errors",
                "question": "Any spike in checkout errors, failed payment attempts, or gateway timeouts?",
                "branches": {
                    "yes": {"note": "checkout errors confirmed — this is really a Payment Success question",
                            "outcome": "this looks like a Payment Success issue wearing a "
                                       "conversion-rate costume", "terminal": False,
                            "redirect_tree": "payment_success"},
                    "no": {"note": "no checkout errors", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "price_inventory", "label": "Price/inventory change",
                "question": "Any price increase, out-of-stock spike, or promo code expiration in the window?",
                "branches": {
                    "yes": {"note": "a price/inventory change happened", "outcome": "check whether the drop "
                            "correlates with specific SKUs, not the whole catalog", "terminal": False},
                    "no": {"note": "no price/inventory change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "ab_test", "label": "A/B test contamination",
                "question": "Is there an active or recently-ended experiment touching this funnel?",
                "branches": {
                    "yes": {"note": "an experiment is live or just ended on this funnel",
                            "outcome": "the \"drop\" may actually be a losing variant, or a test that "
                                       "hasn't been reverted yet — the Experiment Designer decision rule "
                                       "should have caught this if one was running",
                            "terminal": True, "handoff": "experiment_designer"},
                    "no": {"note": "no experiment running here", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "device_browser", "label": "Device/browser specific",
                "question": "Is it concentrated on one browser or device, especially an older OS version?",
                "branches": {
                    "yes": {"note": "concentrated on a specific browser/device", "outcome": "likely a "
                            "checkout UI rendering bug on that specific environment, not a real preference "
                            "change", "terminal": True},
                    "no": {"note": "not device/browser specific", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "A live A/B test nobody remembers is still running and dragging the blended "
                               "average down.",
        "default_handoff": None,
    },

    # ── 4. Revenue / GMV ─────────────────────────────────────────────────
    "revenue": {
        "name": "Revenue", "icon": "💰", "metric_tag": "GMV",
        "checks": [
            {
                "id": "volume_vs_value", "label": "Volume vs. value",
                "question": "Did order count drop, or did AOV drop while order count held steady?",
                "branches": {
                    "count_dropped": {"note": "order count itself dropped", "outcome": "this points to an "
                                      "acquisition or conversion issue, not a revenue-specific one",
                                      "terminal": False},
                    "aov_dropped": {"note": "AOV dropped, not volume — this is really an AOV question",
                                    "outcome": "this points to a mix-shift or discount issue",
                                    "terminal": False, "redirect_tree": "aov"},
                },
            },
            {
                "id": "refunds", "label": "Refunds/cancellations",
                "question": "Any spike in refund or cancellation rate in the same window?",
                "branches": {
                    "yes": {"note": "refund/cancellation spike confirmed", "outcome": "gross revenue may "
                            "look fine but net revenue is being eaten after the fact", "terminal": True},
                    "no": {"note": "no refund/cancellation spike", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "category_concentration", "label": "Category/SKU concentration",
                "question": "Is the drop sitewide or concentrated in specific categories?",
                "branches": {
                    "concentrated": {"note": "concentrated in specific categories", "outcome": "investigate "
                                     "that category's supply, pricing, or demand specifically",
                                     "terminal": False},
                    "sitewide": {"note": "sitewide, not category-specific", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "seasonality", "label": "Seasonality/calendar",
                "question": "Any holiday, payday cycle, or known seasonal dip this maps to?",
                "branches": {
                    "yes": {"note": "a seasonal/calendar pattern applies", "outcome": "compare to the same "
                            "period last year, not just last week, before calling it a real decline",
                            "terminal": True},
                    "no": {"note": "no seasonal pattern", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "reporting", "label": "Currency/reporting",
                "question": "Any change in how revenue is being attributed or reported — gross vs. net, "
                             "timezone cutoff?",
                "branches": {
                    "yes": {"note": "a reporting change confirmed", "outcome": "this may be a reporting "
                            "artifact, not an actual revenue change", "terminal": True},
                    "no": {"note": "no reporting change", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "A timezone or reporting-cutoff change shifts orders between \"yesterday\" "
                               "and \"today,\" making both days look wrong.",
        "default_handoff": None,
    },

    # ── 5. Repeat Purchase Rate ──────────────────────────────────────────
    # Per direct correction: every terminal branch here hands off to Funnel
    # Diagnostics (the source doc's "Retention Autopsy" doesn't exist in
    # this build; Funnel Diagnostics is the real, already-built page that
    # computes cohort-level data — the doc's "almost always ends in pull
    # cohort data and run it through [that tool]" applies to every branch,
    # not just one, so default_handoff covers the case the cap is hit
    # before any single branch resolves it).
    "repeat_rate": {
        "name": "Repeat Rate", "icon": "🔁", "metric_tag": "Retention",
        "checks": [
            {
                "id": "cohort_vs_blended", "label": "Cohort vs. blended",
                "question": "Is this the blended repeat rate across all customers, or a specific cohort's "
                             "repeat rate?",
                "branches": {
                    "blended": {"note": "blended rate — could just be new-cohort dilution",
                                "outcome": "blended rate drops naturally when a large new-acquisition "
                                           "cohort is added — check cohort-level data before panicking",
                                "terminal": False, "handoff": "funnel_diagnostics"},
                    "cohort_specific": {"note": "a specific cohort's rate is down",
                                        "outcome": "a genuine cohort-level decline, worth chasing further "
                                                   "with cohort-level data", "terminal": False,
                                        "handoff": "funnel_diagnostics"},
                },
            },
            {
                "id": "discount_dependency", "label": "Discount dependency",
                "question": "Was a first-order discount reduced or removed recently?",
                "branches": {
                    "yes": {"note": "a first-order discount was reduced/removed", "outcome": "discount-"
                            "acquired customers may simply not be repeating at the rate they used to be "
                            "subsidized to", "terminal": False, "handoff": "funnel_diagnostics"},
                    "no": {"note": "no discount change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "crm_disruption", "label": "CRM/lifecycle disruption",
                "question": "Was a WhatsApp/email/push campaign paused, or did a CRM tool change or break?",
                "branches": {
                    "yes": {"note": "a lifecycle campaign or CRM tool changed", "outcome": "this may be a "
                            "re-engagement delivery failure, not a genuine loyalty decline", "terminal": False,
                            "handoff": "funnel_diagnostics"},
                    "no": {"note": "no CRM/lifecycle disruption", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "time_window", "label": "Time window",
                "question": "Is the measurement window shorter than your typical repeat-purchase gap?",
                "branches": {
                    "yes": {"note": "measurement window may be too short", "outcome": "you may be measuring "
                            "too early — customers due to repeat haven't hit their window yet",
                            "terminal": True, "handoff": "funnel_diagnostics"},
                    "no": {"note": "window is long enough", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "competitive_event", "label": "Competitive event",
                "question": "Any known competitor promo, price war, or new entrant in the market during "
                             "this period?",
                "branches": {
                    "yes": {"note": "a competitive event is happening", "outcome": "this may be temporary "
                            "share-shift, not structural churn", "terminal": True,
                            "handoff": "funnel_diagnostics"},
                    "no": {"note": "no competitive event", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": None,
        "default_handoff": "funnel_diagnostics",
    },

    # ── 6. Average Order Value ───────────────────────────────────────────
    "aov": {
        "name": "AOV", "icon": "🧾", "metric_tag": "Order Value",
        "checks": [
            {
                "id": "mix_shift", "label": "Mix shift",
                "question": "Has the product/category mix of orders shifted toward lower-priced items?",
                "branches": {
                    "yes": {"note": "mix has shifted toward lower-priced items", "outcome": "check whether "
                            "a promotion or campaign specifically drove traffic to lower-AOV SKUs",
                            "terminal": False},
                    "no": {"note": "mix unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "discount_depth", "label": "Discount depth",
                "question": "Has discount percentage or coupon usage increased?",
                "branches": {
                    "yes": {"note": "discount usage increased", "outcome": "gross AOV may be flat but net "
                            "(post-discount) AOV is what's actually dropping", "terminal": True},
                    "no": {"note": "discount usage unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "bundle_upsell", "label": "Bundle/upsell performance",
                "question": "Has a bundle, \"frequently bought together,\" or upsell module been removed or "
                             "broken?",
                "branches": {
                    "yes": {"note": "a bundle/upsell module changed", "outcome": "check whether the module "
                            "is still rendering correctly on PDP/cart", "terminal": True},
                    "no": {"note": "bundle/upsell module unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                # Judgment call, not from source doc: this branch's dilution-vs-decline
                # question is conceptually identical to tree 5's core move, so it gets
                # the same soft Funnel Diagnostics handoff for cohort-level verification.
                "id": "new_customer_mix", "label": "New customer mix",
                "question": "Are new customers — who typically order smaller, exploratory first orders — a "
                             "larger share of orders this period?",
                "branches": {
                    "yes": {"note": "new customers are a larger share of orders", "outcome": "this may be a "
                            "healthy acquisition-driven dilution, not a per-customer spending decline",
                            "terminal": False, "handoff": "funnel_diagnostics",
                            "handoff_soft": True},
                    "no": {"note": "new-customer share unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "payment_method", "label": "Payment method shift",
                "question": "Has there been a shift toward COD or a payment method associated with smaller "
                             "average baskets?",
                "branches": {
                    "yes": {"note": "a payment-method shift confirmed", "outcome": "some payment methods "
                            "correlate with basket size — check whether this is a payment-mix artifact",
                            "terminal": True},
                    "no": {"note": "no payment-method shift", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "A successful low-AOV acquisition campaign (e.g., a trial-size SKU) makes "
                               "blended AOV look like it's declining when per-cohort AOV is unchanged.",
        "default_handoff": None,
    },

    # ── 7. Cart Abandonment Rate ─────────────────────────────────────────
    "cart_abandon": {
        "name": "Cart Abandon", "icon": "🛒", "metric_tag": "Checkout",
        "checks": [
            {
                # Judgment call, not from source doc: an unvalidated checkout change
                # is exactly the kind of thing Experiment Designer exists to test
                # before a full rollout, so this gets a soft handoff there.
                "id": "checkout_friction", "label": "Checkout friction",
                "question": "Any new field added to checkout — extra verification, mandatory account "
                             "creation?",
                "boring_gate": True,
                "branches": {
                    "yes": {"note": "new checkout friction confirmed", "outcome": "added friction is the "
                            "most common and most fixable cause of abandonment", "terminal": True,
                            "handoff": "experiment_designer", "handoff_soft": True},
                    "no": {"note": "no new checkout friction", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "payment_options", "label": "Payment options",
                "question": "Has a popular payment method — UPI, a specific wallet — had an outage or been "
                             "removed?",
                "branches": {
                    "yes": {"note": "a payment method outage/removal confirmed", "outcome": "check payment "
                            "gateway status/uptime for the affected window", "terminal": True},
                    "no": {"note": "no payment method disruption", "outcome": None, "terminal": False},
                },
            },
            {
                # Judgment call, not from source doc: same reasoning as checkout_friction above.
                "id": "shipping_surprise", "label": "Shipping cost/timeline surprise",
                "question": "Was shipping cost or delivery estimate changed, or made visible later in the "
                             "flow than before?",
                "branches": {
                    "yes": {"note": "a shipping disclosure change confirmed", "outcome": "surprise costs at "
                            "checkout are a top abandonment driver — check where shipping info is disclosed "
                            "in the flow", "terminal": True, "handoff": "experiment_designer",
                            "handoff_soft": True},
                    "no": {"note": "no shipping disclosure change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "device_browser", "label": "Device/browser specific",
                "question": "Is it concentrated on mobile web specifically, vs. app or desktop?",
                "branches": {
                    "yes": {"note": "concentrated on mobile web", "outcome": "mobile web checkout friction "
                            "— form fields, autofill failures — is disproportionately common", "terminal": False},
                    "no": {"note": "not mobile-web-specific", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "retargeting", "label": "Retargeting/reminder disruption",
                "question": "Has an abandoned-cart email/WhatsApp reminder flow been paused or broken?",
                "branches": {
                    "yes": {"note": "a reminder flow disruption confirmed", "outcome": "this affects "
                            "recovery rate, which can look like abandonment increasing even if the initial "
                            "abandon rate is stable", "terminal": True},
                    "no": {"note": "no reminder flow disruption", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "Confusing \"abandonment increased\" with \"recovery flow broke\" — they "
                               "need different fixes.",
        "default_handoff": None,
    },

    # ── 8. Search Conversion ─────────────────────────────────────────────
    "search_conv": {
        "name": "Search Conv.", "icon": "🔍", "metric_tag": "On-site Search",
        "checks": [
            {
                "id": "zero_result", "label": "Zero-result rate",
                "question": "Has the percentage of searches returning zero results increased?",
                "boring_gate": True,
                "branches": {
                    "yes": {"note": "zero-result rate increased", "outcome": "likely a catalog/inventory "
                            "sync issue, or a new query pattern not mapped to any SKU", "terminal": True},
                    "no": {"note": "zero-result rate unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                # Judgment call, not from source doc: same "unvalidated change"
                # reasoning as the cart_abandon soft handoffs above.
                "id": "ranking_change", "label": "Ranking/relevance change",
                "question": "Was the search ranking algorithm, synonym list, or personalization logic "
                             "changed recently?",
                "branches": {
                    "yes": {"note": "a ranking/relevance change confirmed", "outcome": "check whether a "
                            "recent \"improvement\" actually regressed relevance for common queries",
                            "terminal": True, "handoff": "experiment_designer", "handoff_soft": True},
                    "no": {"note": "no ranking/relevance change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "query_pattern", "label": "Query pattern shift",
                "question": "Has the mix of query types changed — more brand-name searches vs. category "
                             "searches?",
                "branches": {
                    "yes": {"note": "query mix has shifted", "outcome": "different query types have "
                            "different baseline conversion rates — a mix shift can look like a conversion "
                            "drop", "terminal": False},
                    "no": {"note": "query mix unchanged", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "autocomplete", "label": "Autocomplete/typo tolerance",
                "question": "Any recent change to autocomplete suggestions or fuzzy-match/typo-tolerance "
                             "settings?",
                "branches": {
                    "yes": {"note": "an autocomplete/typo-tolerance change confirmed", "outcome": "reduced "
                            "typo tolerance silently increases zero-result rate for common misspellings",
                            "terminal": True},
                    "no": {"note": "no autocomplete/typo-tolerance change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "inventory_top_results", "label": "Inventory at top results",
                "question": "Are the top-ranked results for common queries out of stock?",
                "branches": {
                    "yes": {"note": "top results are out of stock", "outcome": "ranking may be technically "
                            "correct but pointing users at unavailable products", "terminal": True},
                    "no": {"note": "top results in stock", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": "A \"relevance improvement\" that optimized for a metric other than "
                               "conversion (e.g., click-through) and traded it away.",
        "default_handoff": None,
    },

    # ── 9. Payment Success Rate ──────────────────────────────────────────
    "payment_success": {
        "name": "Payment Success", "icon": "💳", "metric_tag": "Funnel",
        "checks": [
            {
                "id": "gateway_isolation", "label": "Gateway-specific isolation",
                "question": "Is the drop concentrated on one payment gateway or method — UPI, cards, "
                             "netbanking, wallets?",
                "branches": {
                    "yes": {"note": "concentrated on one gateway/method", "outcome": "isolate to that "
                            "gateway before investigating broadly — don't treat it as a sitewide issue",
                            "terminal": False},
                    "no": {"note": "not gateway-specific — broader issue", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "bank_issuer", "label": "Bank/issuer specific",
                "question": "Within the affected method, is it concentrated on specific banks or card "
                             "issuers?",
                "branches": {
                    "yes": {"note": "concentrated on specific banks/issuers", "outcome": "likely a "
                            "bank-side outage or a stricter fraud/risk rule on their end, not your system",
                            "terminal": True},
                    "no": {"note": "not bank/issuer specific", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "integration_change", "label": "Recent integration change",
                "question": "Any recent change to payment gateway version, API integration, or tokenization "
                             "flow?",
                "boring_gate": True,
                "branches": {
                    "yes": {"note": "a recent integration change confirmed", "outcome": "check deployment "
                            "logs for anything touching the payment flow, even if described as unrelated",
                            "terminal": True},
                    "no": {"note": "no recent integration change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "fraud_rule", "label": "Fraud/risk rule change",
                "question": "Was a fraud-detection threshold or risk rule tightened recently, internally or "
                             "by the gateway?",
                "branches": {
                    "yes": {"note": "a fraud/risk rule change confirmed", "outcome": "legitimate "
                            "transactions may be getting falsely declined — check the false-positive rate, "
                            "not just the failure rate", "terminal": True},
                    "no": {"note": "no fraud/risk rule change", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "timeout_latency", "label": "Timeout/latency",
                "question": "Has payment gateway response time increased, causing timeouts rather than "
                             "explicit declines?",
                "branches": {
                    "yes": {"note": "latency increase confirmed", "outcome": "this presents as \"failure\" "
                            "but is actually a latency/infra issue — a different fix, infra rather than "
                            "payment logic", "terminal": True},
                    "no": {"note": "no latency increase", "outcome": None, "terminal": False},
                },
            },
        ],
        "common_false_alarm": None,
        "grounding_note": "This tree draws directly on a JioMart B2B payment-funnel investigation "
                           "(~50%→80%+ recovery via UPI intent diagnosis) — gateway/method isolation before "
                           "broad investigation is the exact sequence that worked there.",
        "default_handoff": None,
    },

    # ── 10. App/Site Performance ─────────────────────────────────────────
    "performance": {
        "name": "Performance", "icon": "⚡", "metric_tag": "Load Time",
        "checks": [
            {
                "id": "deploy_correlation", "label": "Recent deploy correlation",
                "question": "Did the slowdown start right after a deploy, a third-party script addition, or "
                             "a CDN change?",
                "boring_gate": True,
                "branches": {
                    "yes": {"note": "deploy-correlated", "outcome": "almost always deploy-correlated — "
                            "check what shipped in that window before anything else", "terminal": True},
                    "no": {"note": "not deploy-correlated", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "third_party_script", "label": "Third-party script audit",
                "question": "Any new tracking pixel, chat widget, or ad script added recently?",
                "branches": {
                    "yes": {"note": "a new third-party script confirmed", "outcome": "third-party scripts "
                            "are a top cause of silent performance regression — check the network waterfall "
                            "for new blocking requests", "terminal": True},
                    "no": {"note": "no new third-party script", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "geography_cdn", "label": "Geography/CDN concentration",
                "question": "Is the slowdown global, or concentrated in specific regions?",
                "branches": {
                    "concentrated": {"note": "concentrated in specific regions", "outcome": "likely a CDN "
                                     "edge-node or regional infrastructure issue, not an application problem",
                                     "terminal": True},
                    "global": {"note": "global slowdown", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "image_asset", "label": "Image/asset size",
                "question": "Were new images, banners, or video assets added without compression?",
                "branches": {
                    "yes": {"note": "uncompressed new assets confirmed", "outcome": "check asset sizes on "
                            "the affected pages specifically", "terminal": True},
                    "no": {"note": "no uncompressed new assets", "outcome": None, "terminal": False},
                },
            },
            {
                "id": "device_connection", "label": "Device/connection type",
                "question": "Is it concentrated on mobile/slower connections, or uniform across all users?",
                "branches": {
                    "concentrated_mobile": {"note": "concentrated on mobile/slow connections",
                                             "outcome": "likely a render-blocking resource or unoptimized "
                                                        "mobile bundle, not a backend issue", "terminal": True},
                    "uniform": {"note": "uniform across all users/connections", "outcome": None,
                                "terminal": False},
                },
            },
        ],
        "common_false_alarm": None,
        "grounding_note": "If performance is confirmed as the root cause for a different metric (this tree "
                           "is often reached via a redirect from Engagement or Conversion), say so "
                           "explicitly — it's often the actual answer underneath a different symptom.",
        "default_handoff": None,
    },
}


def get_tree(tree_id: str) -> dict:
    return TREES[tree_id]


def get_check(tree_id: str, check_id: str) -> dict:
    for check in TREES[tree_id]["checks"]:
        if check["id"] == check_id:
            return check
    raise KeyError(f"No check '{check_id}' in tree '{tree_id}'")


def category_list() -> list:
    """Ordered list of (tree_id, name, icon, metric_tag) for the Phase 0 picker."""
    return [(tid, TREES[tid]["name"], TREES[tid]["icon"], TREES[tid]["metric_tag"])
            for tid in CATEGORY_ORDER]


def resolve_handoff(tree_id: str, resolved_steps: list, hit_cap: bool) -> dict | None:
    """Deterministic handoff resolution — never decided by the AI layer.

    `resolved_steps` is the ordered list of step dicts already answered in
    THIS tree, each carrying a "branch_data" dict. Walks them back-to-front
    looking for the most recent branch that carries a "handoff" key; falls
    back to the tree's own default_handoff only if the session ended by
    hitting the question cap rather than a clean terminal match. Returns
    None if nothing applies — callers must render the explicit non-handoff
    card in that case, per the cross-tree principle of saying so plainly
    rather than force-fitting one.
    """
    tree = TREES[tree_id]
    for step in reversed(resolved_steps):
        branch = step.get("branch_data") or {}
        if branch.get("handoff"):
            target = HANDOFF_TARGETS[branch["handoff"]]
            return {**target, "soft": bool(branch.get("handoff_soft")), "key": branch["handoff"]}
    if hit_cap and tree.get("default_handoff"):
        target = HANDOFF_TARGETS[tree["default_handoff"]]
        return {**target, "soft": False, "key": tree["default_handoff"]}
    return None
