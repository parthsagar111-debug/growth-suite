"""
First Response — scripted walkthroughs for every one of the 10 trees.

No Groq calls, no latency, no "unclear answer" risk — every category
button loads a pre-written, instant conversation instead of depending
on a live AI classification round-trip. Every question is copied
verbatim from lib/decision_tree.py; every outcome/pull-step/handoff is
grounded directly in that same tree's real branch data, not invented
fresh — this is a presentation-speed shortcut, not a change to what
First Response actually diagnoses.

SCENARIOS is keyed by tree_id (same ids as decision_tree.CATEGORY_ORDER).
Each entry: {"vp_question", "transcript": [...], "stopped_at",
"pending_question" (optional — only page_views has one, matching the
original mockup exactly), "diagnosis": {...}}.
"""

SCENARIOS = {

    "page_views": {
        "vp_question": "Why are page views down this week?",
        "transcript": [
            {"check_label": "Tracking",
             "question": "Any deploy, tag change, or GA4/GTM update in the last 7 days?",
             "answer": "No deploys that I know of.",
             "branch_note": "tracking ruled out, now isolating where it's happening"},
            {"check_label": "Concentration",
             "question": "Is the drop uniform across devices, or concentrated on one — mobile or desktop?",
             "answer": "Mostly mobile, desktop looks normal.",
             "branch_note": "device isolated to mobile, narrowing to acquisition source"},
            {"check_label": "Channel",
             "question": "Within that, which channel dropped — organic, paid, direct, or referral?",
             "answer": "Direct mostly, organic looks okay.",
             "branch_note": "narrowed to direct"},
        ],
        "stopped_at": 4,
        "pending_question": {
            "check_label": "Comparison window",
            "question": "Is this down vs. the same day last week AND last month, or just one of those?",
        },
        "diagnosis": {
            "title": "This looks like a mobile app deep-link or tracking issue, not a real traffic drop.",
            "body": ("Mobile-direct-specific drops, with desktop and organic both normal, almost never "
                      "indicate a genuine demand decline — direct traffic doesn't behave that way on its "
                      "own. The pattern matches a broken deep link, an app tracking SDK issue, or a silent "
                      "GA4 consent-mode change more than an actual user drop-off."),
            "pull_steps": [
                "GA4 → Reports → Tech → Overview → filter device = mobile, channel = direct, last 14 days",
                "Check app deep-link redirect logs (or Branch/AppsFlyer dashboard if you use one) for "
                "failed opens in the same window",
                "Ask engineering: any GTM container publish or consent-mode change in the last 7 days, "
                "even a minor one",
            ],
            "handoff": None,
            "handoff_line": ("Not a Funnel Diagnostics case — yet. This reads as a tracking/technical "
                              "issue, not a genuine engagement problem. If GA4 confirms the numbers are "
                              "real (not a tracking artifact), bring the corrected data back here to check "
                              "if it's a retention pattern."),
            "reply_draft": ("Looking into it — early signal points to mobile-direct traffic specifically, "
                             "which usually means a tracking or deep-link issue rather than a real drop. "
                             "Confirming with GA4 and eng, will have a clean answer by EOD."),
        },
    },

    "engagement": {
        "vp_question": "Why is time on site down this month?",
        "transcript": [
            {"check_label": "Bot/spam filter",
             "question": "Any spike in sessions with 0-second duration or single-page bounces from "
                          "unfamiliar geographies?",
             "answer": "No, doesn't look like bot traffic.",
             "branch_note": "not a bot/spam issue, keep isolating"},
            {"check_label": "Content change",
             "question": "Was a page redesigned, a hero banner changed, or content removed in the "
                          "affected period?",
             "answer": "No changes that I'm aware of.",
             "branch_note": "no content change"},
            {"check_label": "Page-level concentration",
             "question": "Is the drop sitewide, or concentrated on specific page types — PDP, blog, "
                          "homepage?",
             "answer": "Mostly on PDP pages, blog and homepage look normal.",
             "branch_note": "concentrated on specific page types"},
            {"check_label": "New user mix",
             "question": "Has the new-vs-returning visitor ratio shifted toward more first-time visitors?",
             "answer": "Yes actually, we just launched a big paid campaign and new visitors are way up.",
             "branch_note": "more first-time visitors in the mix"},
        ],
        "stopped_at": 4,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like acquisition-driven dilution, not a real engagement decline.",
            "body": ("A new paid campaign is bringing in a much larger share of first-time visitors, and "
                      "first-time visitors naturally engage less deeply than returning ones — that mix "
                      "shift alone can drag the average down with nothing actually declining in quality."),
            "pull_steps": [
                "GA4 → Audience → New vs Returning — compare new-visitor share before vs. after the "
                "campaign start date",
                "Segment engagement metrics (time on site, pages/session) by new vs. returning "
                "separately — check if returning-visitor engagement held steady",
                "Confirm campaign launch date and spend with marketing to correlate timing exactly",
            ],
            "handoff": None,
            "handoff_line": ("Not a Funnel Diagnostics case — yet. This reads as a mix-shift from "
                              "acquisition, not a genuine engagement quality drop. If per-segment "
                              "engagement is also down after isolating new vs. returning, it's worth "
                              "revisiting."),
            "reply_draft": ("Early read: this looks like dilution from the new paid campaign, not "
                             "declining engagement — new visitors naturally have a lower baseline. "
                             "Confirming with segmented GA4 data, will follow up shortly."),
        },
    },

    "conversion": {
        "vp_question": "Why did our conversion rate drop this week?",
        "transcript": [
            {"check_label": "Funnel stage isolation",
             "question": "Which specific step dropped — PDP view→Add to Cart, Cart→Checkout start, or "
                          "Checkout→Purchase?",
             "answer": "Cart to checkout start is where we're seeing the drop.",
             "branch_note": "isolated to Cart→Checkout"},
            {"check_label": "Payment/checkout errors",
             "question": "Any spike in checkout errors, failed payment attempts, or gateway timeouts?",
             "answer": "No, error rates look normal.",
             "branch_note": "no checkout errors"},
            {"check_label": "Price/inventory change",
             "question": "Any price increase, out-of-stock spike, or promo code expiration in the window?",
             "answer": "No, prices and inventory are unchanged.",
             "branch_note": "no price/inventory change"},
            {"check_label": "A/B test contamination",
             "question": "Is there an active or recently-ended experiment touching this funnel?",
             "answer": "Actually yes, we have a checkout redesign test running right now.",
             "branch_note": "an experiment is live or just ended on this funnel"},
        ],
        "stopped_at": 4,
        "pending_question": None,
        "diagnosis": {
            "title": "This is likely a live A/B test dragging the blended average down, not a real "
                      "conversion problem.",
            "body": ("The \"drop\" may actually be a losing variant, or a test that hasn't been reverted "
                      "yet, rather than a genuine conversion decline — the Experiment Designer decision "
                      "rule should have caught this if one was running."),
            "pull_steps": [
                "Check the experiment platform for the checkout redesign test — confirm it's still "
                "running and which variant is dominant in traffic",
                "Pull conversion rate split by variant (control vs. treatment) instead of the blended "
                "average",
                "Check the Experiment Designer decision rule for this test — see if a kill/extend "
                "threshold was already tripped",
            ],
            "handoff": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py",
                        "soft": False, "key": "experiment_designer"},
            "handoff_line": ("Worth routing through Experiment Designer — the \"drop\" may just be a "
                              "losing variant or a test that hasn't been reverted yet."),
            "reply_draft": ("Early signal: we have a checkout redesign test live right now, so this is "
                             "probably a losing variant dragging the blended rate down, not a real "
                             "conversion issue. Pulling the per-variant split to confirm, will have a "
                             "clean read shortly."),
        },
    },

    "revenue": {
        "vp_question": "Why is revenue down this week?",
        "transcript": [
            {"check_label": "Volume vs. value",
             "question": "Did order count drop, or did AOV drop while order count held steady?",
             "answer": "Order count is down, AOV looks about the same.",
             "branch_note": "order count itself dropped"},
            {"check_label": "Refunds/cancellations",
             "question": "Any spike in refund or cancellation rate in the same window?",
             "answer": "No, refunds are steady.",
             "branch_note": "no refund/cancellation spike"},
            {"check_label": "Category/SKU concentration",
             "question": "Is the drop sitewide or concentrated in specific categories?",
             "answer": "Mostly concentrated in our home goods category.",
             "branch_note": "concentrated in specific categories"},
            {"check_label": "Seasonality/calendar",
             "question": "Any holiday, payday cycle, or known seasonal dip this maps to?",
             "answer": "Actually yes, we usually see a dip this time of year in home goods specifically.",
             "branch_note": "a seasonal/calendar pattern applies"},
        ],
        "stopped_at": 4,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like a known seasonal dip in home goods, not a structural revenue "
                      "problem.",
            "body": ("Order count is down specifically in one category with a documented seasonal "
                      "pattern — worth comparing to the same period last year before treating this as a "
                      "real decline."),
            "pull_steps": [
                "Pull home goods revenue for the same period last year — confirm the seasonal pattern "
                "repeats",
                "Check whether other categories are flat or growing in the same window, to isolate this "
                "to home goods specifically",
                "Loop in the category manager to confirm the known seasonal calendar for home goods",
            ],
            "handoff": None,
            "handoff_line": ("Not a Funnel Diagnostics case — yet. This reads as calendar-driven, not a "
                              "retention or acquisition problem. If the dip is deeper than last year's "
                              "seasonal pattern, it's worth a second look."),
            "reply_draft": ("Early read: order count is down specifically in home goods, and this matches "
                             "a seasonal dip we've seen before in this category. Confirming against last "
                             "year's numbers, will confirm by EOD."),
        },
    },

    "repeat_rate": {
        "vp_question": "Why is our repeat purchase rate down?",
        "transcript": [
            {"check_label": "Cohort vs. blended",
             "question": "Is this the blended repeat rate across all customers, or a specific cohort's "
                          "repeat rate?",
             "answer": "It's the blended rate across everyone.",
             "branch_note": "blended rate — could just be new-cohort dilution"},
            {"check_label": "Discount dependency",
             "question": "Was a first-order discount reduced or removed recently?",
             "answer": "Yes, we cut the first-order 20% code down to 10% last month.",
             "branch_note": "a first-order discount was reduced/removed"},
        ],
        "stopped_at": 2,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like discount-acquired customers repeating less, not a broad loyalty "
                      "decline.",
            "body": ("Discount-acquired customers may simply not be repeating at the rate they used to be "
                      "subsidized to — a smaller first-order discount changes the customer mix that reaches "
                      "month two, not necessarily the underlying loyalty of any given customer."),
            "pull_steps": [
                "Pull cohort-level repeat rate split by discount code used on order 1, compare pre/post "
                "the code change",
                "Run this cohort data through Funnel Diagnostics to separate genuine cohort decline from "
                "blended dilution",
                "Check first-order AOV/margin trade-off to confirm the discount cut is working as intended",
            ],
            "handoff": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py",
                        "soft": False, "key": "funnel_diagnostics"},
            "handoff_line": ("Worth a Funnel Diagnostics pass — cohort-level data will show whether this "
                              "is genuine or just the discount change working as intended."),
            "reply_draft": ("Early read: we cut the first-order discount last month, so this probably "
                             "reflects less-subsidized customers repeating less, not a broad loyalty "
                             "issue. Pulling cohort-level data to confirm, will follow up shortly."),
        },
    },

    "aov": {
        "vp_question": "Why is our average order value trending down?",
        "transcript": [
            {"check_label": "Mix shift",
             "question": "Has the product/category mix of orders shifted toward lower-priced items?",
             "answer": "No, mix looks about the same.",
             "branch_note": "mix unchanged"},
            {"check_label": "Discount depth",
             "question": "Has discount percentage or coupon usage increased?",
             "answer": "No, discount depth is flat.",
             "branch_note": "discount usage unchanged"},
            {"check_label": "Bundle/upsell performance",
             "question": "Has a bundle, \"frequently bought together,\" or upsell module been removed or "
                          "broken?",
             "answer": "No, that's all still live and working.",
             "branch_note": "bundle/upsell module unchanged"},
            {"check_label": "New customer mix",
             "question": "Are new customers — who typically order smaller, exploratory first orders — a "
                          "larger share of orders this period?",
             "answer": "Yes, we ran a big awareness campaign and new customers are way up.",
             "branch_note": "new customers are a larger share of orders"},
        ],
        "stopped_at": 4,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like healthy acquisition dilution, not a per-customer spending decline.",
            "body": ("New customers typically place smaller, exploratory first orders — a surge in "
                      "new-customer share can pull blended AOV down even if no individual customer is "
                      "spending less than before."),
            "pull_steps": [
                "Split AOV by new vs. returning customers for this period",
                "Compare per-cohort AOV — new customers this period vs. their own historical first-order "
                "AOV",
                "Confirm the awareness campaign's timing lines up with the AOV dip start date",
            ],
            "handoff": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py",
                        "soft": True, "key": "funnel_diagnostics"},
            "handoff_line": ("Worth checking with Funnel Diagnostics — cohort-level data would confirm "
                              "this is dilution, not decline, though it's not urgent."),
            "reply_draft": ("Early read: the AOV dip lines up with a new-customer surge from the "
                             "awareness campaign, so this is likely healthy dilution, not a real "
                             "per-customer decline. Confirming with cohort-split data, will follow up "
                             "soon."),
        },
    },

    "cart_abandon": {
        "vp_question": "Why is cart abandonment up this week?",
        "transcript": [
            {"check_label": "Checkout friction",
             "question": "Any new field added to checkout — extra verification, mandatory account "
                          "creation?",
             "answer": "Yes, we just added a mandatory phone verification step.",
             "branch_note": "new checkout friction confirmed"},
        ],
        "stopped_at": 1,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like added checkout friction from the new phone verification step.",
            "body": ("Added friction is the most common and most fixable cause of abandonment — a "
                      "mandatory verification step that wasn't there before is a strong candidate, "
                      "especially if the timing lines up."),
            "pull_steps": [
                "Pull abandonment rate specifically at the verification step in the funnel breakdown",
                "Compare completion time and drop-off before vs. after the verification step was added",
                "Loop in eng/product on whether verification can be made optional or deferred "
                "post-purchase",
            ],
            "handoff": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py",
                        "soft": True, "key": "experiment_designer"},
            "handoff_line": ("Worth routing the rollback or a lighter version through Experiment Designer "
                              "to validate before removing it outright."),
            "reply_draft": ("Early signal: the new mandatory phone verification step lines up almost "
                             "exactly with the abandonment increase. Pulling step-level funnel data to "
                             "confirm, will have a clean answer shortly."),
        },
    },

    "search_conv": {
        "vp_question": "Why is on-site search conversion down?",
        "transcript": [
            {"check_label": "Zero-result rate",
             "question": "Has the percentage of searches returning zero results increased?",
             "answer": "Yes, zero-result rate is up noticeably.",
             "branch_note": "zero-result rate increased"},
        ],
        "stopped_at": 1,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like a catalog/inventory sync issue, not a search relevance problem.",
            "body": ("A rising zero-result rate is most often a catalog/inventory sync issue, or a new "
                      "query pattern not mapped to any SKU — not a change in how well search understands "
                      "what people want."),
            "pull_steps": [
                "Pull the top zero-result queries and check if they map to recently out-of-stock or "
                "delisted SKUs",
                "Check catalog sync job logs for failures or delays in the affected window",
                "Spot-check a few zero-result queries manually in live search to confirm they should "
                "return something",
            ],
            "handoff": None,
            "handoff_line": ("Not a suite handoff case — yet. This reads as a catalog/sync issue, not a "
                              "retention or experiment question. If sync logs are clean, it's worth a "
                              "second pass on ranking logic."),
            "reply_draft": ("Early read: zero-result rate has spiked, which usually points to a catalog "
                             "sync issue rather than a relevance problem. Checking sync logs now, will "
                             "confirm shortly."),
        },
    },

    "payment_success": {
        "vp_question": "Why is our payment success rate down?",
        "transcript": [
            {"check_label": "Gateway-specific isolation",
             "question": "Is the drop concentrated on one payment gateway or method — UPI, cards, "
                          "netbanking, wallets?",
             "answer": "Yes, it's specifically UPI transactions.",
             "branch_note": "concentrated on one gateway/method"},
            {"check_label": "Bank/issuer specific",
             "question": "Within the affected method, is it concentrated on specific banks or card "
                          "issuers?",
             "answer": "Yes, mostly one specific bank's UPI handle.",
             "branch_note": "concentrated on specific banks/issuers"},
        ],
        "stopped_at": 2,
        "pending_question": None,
        "diagnosis": {
            "title": "This looks like a bank-side outage or risk-rule tightening, not a problem on our "
                      "end.",
            "body": ("Isolating to one gateway and then one specific bank's UPI handle points to a "
                      "bank-side outage or a stricter fraud/risk rule on their end, rather than anything "
                      "in our own payment integration."),
            "pull_steps": [
                "Pull UPI success rate filtered to that specific bank/handle, compare to other banks in "
                "the same window",
                "Check the gateway's status page or support channel for known issues with that bank",
                "Reach out to the payment gateway account manager to confirm if it's bank-side",
            ],
            "handoff": None,
            "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not a retention or "
                              "experiment question."),
            "reply_draft": ("Early read: the payment failures are concentrated on one specific bank's UPI "
                             "handle, which points to a bank-side issue rather than something on our end. "
                             "Confirming with the gateway, will update shortly."),
        },
    },

    "performance": {
        "vp_question": "Why did our site suddenly get slower?",
        "transcript": [
            {"check_label": "Recent deploy correlation",
             "question": "Did the slowdown start right after a deploy, a third-party script addition, or "
                          "a CDN change?",
             "answer": "Yes, it started right after yesterday's deploy.",
             "branch_note": "deploy-correlated"},
        ],
        "stopped_at": 1,
        "pending_question": None,
        "diagnosis": {
            "title": "This is almost certainly deploy-correlated.",
            "body": ("Performance regressions that start right after a deploy are deploy-correlated far "
                      "more often than not — check what shipped in that window before looking anywhere "
                      "else."),
            "pull_steps": [
                "Pull yesterday's deploy diff — check for anything touching page load, scripts, or the "
                "asset pipeline",
                "Compare Core Web Vitals before vs. after the exact deploy timestamp",
                "If nothing obvious, run a quick rollback test on a canary/staging environment to confirm",
            ],
            "handoff": None,
            "handoff_line": ("Not a suite handoff case — this is a deploy/infra issue, not retention or "
                              "experiment-shaped."),
            "reply_draft": ("Early read: the slowdown lines up almost exactly with yesterday's deploy. "
                             "Pulling the deploy diff now, will confirm the specific change shortly."),
        },
    },
}

# Backwards-compat aliases (previous single-scenario module shape) — kept
# so nothing else importing the old names breaks.
CATEGORY = "page_views"
VP_QUESTION = SCENARIOS["page_views"]["vp_question"]
TRANSCRIPT = SCENARIOS["page_views"]["transcript"]
STOPPED_AT_QUESTION = SCENARIOS["page_views"]["stopped_at"]
PENDING_QUESTION = SCENARIOS["page_views"]["pending_question"]
DIAGNOSIS = SCENARIOS["page_views"]["diagnosis"]
