"""
First Response — the "live" interactive pilot.

Every other tree in this tool (see sample_scenario.py) is a pre-scripted
walkthrough: pick a category, see the whole resolved conversation
instantly. That's fast for a demo, but it doesn't feel like you're
actually answering anything.

This module is the opposite for exactly one tree, Payment Success,
picked as the pilot: the first question really is a live fork with
real, method-specific options (not a yes/no gate), and every question
after it is chosen dynamically based on what you clicked — walking a
real branching graph instead of replaying a script. If this pilot
lands well, the same pattern (LIVE_TREES[tree_id] = {vp_question, root,
nodes, terminals}) can be extended to the other 9 categories later.

Shape:
  LIVE_TREES[tree_id] = {
    "vp_question": str,
    "root": <node_id>,
    "nodes": {
      <node_id>: {
        "check_label": str, "question": str,
        "options": [{"key": str, "label": str}, ...],
        "next": {option_key: <node_id or "TERMINAL_xxx">, ...},
      }, ...
    },
    "terminals": {
      "TERMINAL_xxx": {"title", "body", "pull_steps", "handoff",
                         "handoff_line", "reply_draft"}, ...   # same
                         shape as sample_scenario.py's "diagnosis" dict
    },
  }

Every question/outcome below stays grounded in the same real checks
already defined in decision_tree.py's payment_success tree
(gateway isolation -> bank/issuer -> integration change -> fraud rule)
— this just gives gateway_isolation real per-method branches instead of
a yes/no gate, and adds a couple of method-specific follow-ups
(3DS/tokenization for cards, portal-specific for netbanking, provider-
specific for wallets) so every one of the 5 top-level answers leads
somewhere real instead of converging back onto one path.
"""

LIVE_TREES = {

    "payment_success": {
        "vp_question": "Why is our payment success rate down?",
        "root": "gateway_isolation",

        "nodes": {

            "gateway_isolation": {
                "check_label": "Gateway-specific isolation",
                "question": "Is the drop concentrated on one payment gateway or method — UPI, cards, "
                            "netbanking, wallets?",
                "options": [
                    {"key": "uniform", "label": "Uniform — across all methods"},
                    {"key": "upi", "label": "UPI"},
                    {"key": "cards", "label": "Cards"},
                    {"key": "netbanking", "label": "Netbanking"},
                    {"key": "wallets", "label": "Wallets"},
                ],
                "next": {
                    "uniform": "broad_integration_check",
                    "upi": "upi_bank_check",
                    "cards": "card_scope_check",
                    "netbanking": "netbanking_scope_check",
                    "wallets": "wallet_scope_check",
                },
            },

            # ── Uniform / all-methods branch ────────────────────────────
            "broad_integration_check": {
                "check_label": "Recent integration change",
                "question": "Any recent change to your payment gateway version, checkout API, or overall "
                            "integration?",
                "options": [
                    {"key": "yes", "label": "Yes, something changed"},
                    {"key": "no", "label": "No changes on our side"},
                ],
                "next": {"yes": "TERMINAL_integration_regression", "no": "TERMINAL_gateway_outage"},
            },

            # ── UPI branch ───────────────────────────────────────────────
            "upi_bank_check": {
                "check_label": "Bank/issuer specific",
                "question": "Within UPI, is it concentrated on one specific bank/handle, or spread across "
                            "banks?",
                "options": [
                    {"key": "one_bank", "label": "One specific bank"},
                    {"key": "spread", "label": "Spread across banks"},
                ],
                "next": {"one_bank": "TERMINAL_bank_outage", "spread": "upi_fraud_check"},
            },
            "upi_fraud_check": {
                "check_label": "Fraud/risk rule change",
                "question": "Was a fraud-detection threshold or risk rule tightened on UPI recently, "
                            "internally or by the gateway?",
                "options": [
                    {"key": "yes", "label": "Yes, tightened recently"},
                    {"key": "no", "label": "No changes there"},
                ],
                "next": {"yes": "TERMINAL_fraud_false_decline", "no": "TERMINAL_upi_latency"},
            },

            # ── Cards branch ─────────────────────────────────────────────
            "card_scope_check": {
                "check_label": "Card concentration",
                "question": "Is it concentrated on one card network or issuing bank, or affecting all cards?",
                "options": [
                    {"key": "concentrated", "label": "One network / issuer"},
                    {"key": "all", "label": "All cards"},
                ],
                "next": {"concentrated": "TERMINAL_card_issuer_outage", "all": "card_3ds_check"},
            },
            "card_3ds_check": {
                "check_label": "3DS/OTP flow",
                "question": "Any recent change to the 3DS/OTP verification flow or card tokenization?",
                "options": [
                    {"key": "yes", "label": "Yes, something changed"},
                    {"key": "no", "label": "No changes there"},
                ],
                "next": {"yes": "TERMINAL_3ds_regression", "no": "TERMINAL_card_processing"},
            },

            # ── Netbanking branch ────────────────────────────────────────
            "netbanking_scope_check": {
                "check_label": "Netbanking concentration",
                "question": "Is it concentrated on specific banks' netbanking portals, or spread across "
                            "banks?",
                "options": [
                    {"key": "concentrated", "label": "Specific banks"},
                    {"key": "spread", "label": "Spread across banks"},
                ],
                "next": {"concentrated": "TERMINAL_netbanking_bank_outage", "spread": "TERMINAL_netbanking_redirect"},
            },

            # ── Wallets branch ───────────────────────────────────────────
            "wallet_scope_check": {
                "check_label": "Wallet concentration",
                "question": "Is it concentrated on one specific wallet provider, or affecting all wallets?",
                "options": [
                    {"key": "one", "label": "One specific wallet"},
                    {"key": "all", "label": "All wallets"},
                ],
                "next": {"one": "TERMINAL_wallet_outage", "all": "TERMINAL_wallet_integration"},
            },
        },

        "terminals": {

            "TERMINAL_integration_regression": {
                "title": "This looks like a technical regression from a recent integration change, "
                          "not something method-specific.",
                "body": ("The drop hits every payment method equally and lines up with a recent gateway "
                          "version, checkout API, or integration change — that combination points to a "
                          "regression in the shared checkout/payment code, not any one method's issue."),
                "pull_steps": [
                    "Pull the deployment diff for the exact change and check anything touching the "
                    "payment/checkout path",
                    "Compare success rate immediately before vs. after the change's rollout timestamp",
                    "Roll back the change on a canary/staging environment to confirm it's the cause",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a deploy/integration issue, not "
                                  "retention or experiment-shaped."),
                "reply_draft": ("Early read: the drop is uniform across payment methods and lines up with "
                                  "a recent integration change, so this looks like a shared checkout "
                                  "regression. Pulling the deploy diff now, will confirm shortly."),
            },
            "TERMINAL_gateway_outage": {
                "title": "This looks like a gateway-side outage or capacity issue, not a problem in our "
                          "integration.",
                "body": ("Every payment method is affected equally, and nothing changed on our side — that "
                          "points to the payment gateway itself having a broad outage or capacity issue "
                          "rather than anything in our checkout code."),
                "pull_steps": [
                    "Check the gateway's public status page and support channel for an active incident",
                    "Compare gateway API response times/error rates across the affected window",
                    "Reach out to the gateway account manager to confirm and get an ETA",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not retention or "
                                  "experiment-shaped."),
                "reply_draft": ("Early read: every payment method is affected equally with no change on our "
                                  "side, which points to a gateway-side outage. Checking their status page "
                                  "and reaching out now, will update shortly."),
            },

            "TERMINAL_bank_outage": {
                "title": "This looks like a bank-side outage or risk-rule tightening, not a problem on our "
                          "end.",
                "body": ("Isolating to UPI and then one specific bank's handle points to a bank-side outage "
                          "or a stricter fraud/risk rule on their end, rather than anything in our own "
                          "payment integration."),
                "pull_steps": [
                    "Pull UPI success rate filtered to that specific bank/handle, compare to other banks in "
                    "the same window",
                    "Check the gateway's status page or support channel for known issues with that bank",
                    "Reach out to the payment gateway account manager to confirm if it's bank-side",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not a retention "
                                  "or experiment question."),
                "reply_draft": ("Early read: the payment failures are concentrated on one specific bank's "
                                  "UPI handle, which points to a bank-side issue rather than something on "
                                  "our end. Confirming with the gateway, will update shortly."),
            },
            "TERMINAL_fraud_false_decline": {
                "title": "This looks like a tightened fraud rule causing false declines, not a real payment "
                          "failure.",
                "body": ("The drop is UPI-specific but spread across banks, not concentrated on one issuer, "
                          "with no bank-side outage — that points to a fraud/risk threshold tightened "
                          "recently, likely flagging legitimate transactions as risky rather than a genuine "
                          "payment problem."),
                "pull_steps": [
                    "Pull the false-positive rate on declined UPI transactions from the risk team, not just "
                    "the raw decline rate",
                    "Compare decline reason codes before vs. after the threshold change to confirm the "
                    "timing",
                    "Ask the gateway/risk team to roll back or loosen the specific rule that changed, on a "
                    "test cohort",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a risk/fraud-rule tuning issue, not a "
                                  "retention or experiment question."),
                "reply_draft": ("Early read: a fraud/risk threshold was tightened on UPI recently, which "
                                  "likely means legitimate transactions are getting falsely declined rather "
                                  "than a real payment issue. Pulling the false-positive rate to confirm, "
                                  "will update shortly."),
            },
            "TERMINAL_upi_latency": {
                "title": "This looks like a UPI-wide latency or timeout issue at the gateway level.",
                "body": ("The drop is spread across banks with no fraud-rule change — that pattern usually "
                          "means transactions are timing out before completing rather than being actively "
                          "declined, which points to gateway-side latency rather than a risk decision."),
                "pull_steps": [
                    "Pull UPI response-time percentiles (p50/p95/p99) for the affected window",
                    "Check the split between explicit declines and timeouts in the failure reason codes",
                    "Ask the gateway for their UPI switch/NPCI-side latency metrics for the same window",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is an infra/latency issue, not retention "
                                  "or experiment-shaped."),
                "reply_draft": ("Early read: UPI failures are spread across banks with no fraud-rule "
                                  "change, which points to a latency/timeout issue at the gateway rather "
                                  "than declines. Pulling response-time data now, will confirm shortly."),
            },

            "TERMINAL_card_issuer_outage": {
                "title": "This looks like a single card network or issuer outage, not a broad card-"
                          "processing problem.",
                "body": ("The drop is concentrated on one card network or issuing bank rather than all "
                          "cards — that's most consistent with an outage or risk-rule change on that "
                          "specific issuer's side."),
                "pull_steps": [
                    "Pull card success rate filtered to that network/issuer, compare to other issuers in "
                    "the same window",
                    "Check the gateway's status page for known issues with that specific network/issuer",
                    "Reach out to the gateway account manager to confirm if it's issuer-side",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not retention or "
                                  "experiment-shaped."),
                "reply_draft": ("Early read: card failures are concentrated on one network/issuer, which "
                                  "points to an issue on their side rather than ours. Confirming with the "
                                  "gateway, will update shortly."),
            },
            "TERMINAL_3ds_regression": {
                "title": "This looks like a 3DS/OTP or tokenization regression, not a broad card-processing "
                          "issue.",
                "body": ("The drop hits all cards, not one network or issuer, and lines up with a recent "
                          "change to the 3DS/OTP flow or tokenization — that combination points to a "
                          "regression in verification, not the underlying card processing."),
                "pull_steps": [
                    "Pull OTP delivery/verification success rate before vs. after the change",
                    "Check whether the 3DS challenge is failing to render or timing out on any specific "
                    "bank/device combination",
                    "Roll back the 3DS/tokenization change on a canary environment to confirm it's the "
                    "cause",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a deploy/integration issue, not "
                                  "retention or experiment-shaped."),
                "reply_draft": ("Early read: card failures hit everyone and line up with a recent 3DS/OTP "
                                  "or tokenization change, so this looks like a verification-flow "
                                  "regression. Pulling OTP success-rate data now, will confirm shortly."),
            },
            "TERMINAL_card_processing": {
                "title": "This looks like a broader card-processing issue at the gateway, not a "
                          "verification-flow regression.",
                "body": ("The drop hits all cards with no recent 3DS/tokenization change — that points to "
                          "something further down the processing chain at the gateway itself, rather than "
                          "the verification step."),
                "pull_steps": [
                    "Pull card decline reason codes across the affected window to see where in the flow "
                    "they're failing",
                    "Check the gateway's card-processing uptime/status for the same window",
                    "Escalate to the gateway with a sample of failed transaction IDs for root-cause",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not retention or "
                                  "experiment-shaped."),
                "reply_draft": ("Early read: card failures hit everyone with no verification-flow change on "
                                  "our side, which points to a gateway-side processing issue. Escalating "
                                  "with failed transaction samples now, will update shortly."),
            },

            "TERMINAL_netbanking_bank_outage": {
                "title": "This looks like specific banks' netbanking portals having an outage, not a "
                          "gateway-wide issue.",
                "body": ("The drop is concentrated on particular banks' netbanking portals rather than "
                          "spread across all banks — that points to an outage or maintenance window on "
                          "those specific banks' side."),
                "pull_steps": [
                    "Pull netbanking success rate filtered to the affected banks, compare to unaffected "
                    "banks in the same window",
                    "Check those banks' own status pages or known maintenance windows",
                    "Reach out to the gateway account manager to confirm if it's bank-side",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not retention or "
                                  "experiment-shaped."),
                "reply_draft": ("Early read: netbanking failures are concentrated on specific banks' "
                                  "portals, which points to an issue on their side rather than ours. "
                                  "Confirming with the gateway, will update shortly."),
            },
            "TERMINAL_netbanking_redirect": {
                "title": "This looks like a netbanking redirect/timeout issue at the gateway level.",
                "body": ("The drop is spread across banks rather than concentrated on a few — that pattern "
                          "usually points to the redirect-and-return flow between the gateway and banks' "
                          "portals timing out or failing generically, rather than any one bank's issue."),
                "pull_steps": [
                    "Pull the redirect-success vs. redirect-timeout split from the gateway's netbanking logs",
                    "Check whether the return-URL/callback handling changed recently on our side",
                    "Ask the gateway for their netbanking redirect uptime for the same window",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is an infra/integration issue, not "
                                  "retention or experiment-shaped."),
                "reply_draft": ("Early read: netbanking failures are spread across banks rather than "
                                  "concentrated on a few, which points to a redirect/timeout issue at the "
                                  "gateway. Pulling the redirect logs now, will confirm shortly."),
            },

            "TERMINAL_wallet_outage": {
                "title": "This looks like a single wallet provider's outage, not a broad wallet-payments "
                          "issue.",
                "body": ("The drop is concentrated on one specific wallet provider rather than all wallets "
                          "— that's most consistent with an outage or API issue on that provider's side."),
                "pull_steps": [
                    "Pull wallet success rate filtered to that provider, compare to other wallets in the "
                    "same window",
                    "Check that provider's status page or developer channel for a known incident",
                    "Reach out to the gateway account manager to confirm if it's provider-side",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not retention or "
                                  "experiment-shaped."),
                "reply_draft": ("Early read: wallet failures are concentrated on one specific provider, "
                                  "which points to an issue on their side rather than ours. Confirming with "
                                  "the gateway, will update shortly."),
            },
            "TERMINAL_wallet_integration": {
                "title": "This looks like a wallet integration/API issue at the gateway, affecting all "
                          "wallet providers.",
                "body": ("The drop hits every wallet provider, not just one — that points to something in "
                          "the shared wallet-payments integration at the gateway level rather than any "
                          "single provider's outage."),
                "pull_steps": [
                    "Pull the gateway's wallet-payments API error codes across the affected window",
                    "Check for a recent gateway SDK/API version bump touching the wallet-payment path",
                    "Escalate to the gateway with sample failed transaction IDs across multiple wallet "
                    "providers",
                ],
                "handoff": None,
                "handoff_line": ("Not a suite handoff case — this is a vendor/infra issue, not retention or "
                                  "experiment-shaped."),
                "reply_draft": ("Early read: the drop hits every wallet provider, which points to a shared "
                                  "integration issue at the gateway rather than one provider's outage. "
                                  "Escalating with failed transaction samples now, will update shortly."),
            },
        },
    },

    # ── The other 9 trees: same live/branching mechanic, but the node graph
    # mirrors decision_tree.py's real checks directly (in their real order,
    # honoring every "terminal"/"redirect_tree" flag) rather than inventing
    # extra branch richness the way payment_success's pilot did — most
    # checks here are still real multi-way or yes/no forks, just not
    # hand-expanded beyond what the canonical tree already defines. A
    # "redirect_tree" branch ends the graph in a distinct redirect card
    # (see fr_live_step.html) linking to that other tree's own live start,
    # rather than stitching two trees' transcripts into one path — simpler,
    # and still faithful to what the real tree says should happen next.
    # A "CAP" terminal is reached if all 5 real checks come back clean —
    # decision_tree.py's own hit-cap fallback (default_handoff, if any).

    "page_views": {
        "vp_question": "Why are page views down this week?",
        "root": "tracking",
        "nodes": {
            "tracking": {
                "check_label": "Tracking",
                "question": "Any deploy, tag change, or GA4/GTM update in the last 7 days?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No changes"}],
                "next": {"yes": "TERMINAL_pv_tracking", "no": "concentration"},
            },
            "concentration": {
                "check_label": "Concentration",
                "question": "Is the drop uniform across devices, or concentrated on one — mobile or desktop?",
                "options": [{"key": "mobile", "label": "Mobile specifically"}, {"key": "desktop", "label": "Desktop specifically"}, {"key": "uniform", "label": "Uniform across devices"}],
                "next": {"mobile": "channel", "desktop": "channel", "uniform": "channel"},
            },
            "channel": {
                "check_label": "Channel",
                "question": "Within that, which channel dropped — organic, paid, direct, or referral?",
                "options": [{"key": "organic", "label": "Organic"}, {"key": "paid", "label": "Paid"}, {"key": "direct", "label": "Direct"}, {"key": "referral", "label": "Referral"}],
                "next": {"organic": "comparison_window", "paid": "comparison_window", "direct": "comparison_window", "referral": "comparison_window"},
            },
            "comparison_window": {
                "check_label": "Comparison window",
                "question": "Is this down vs. the same day last week AND last month, or just one of those?",
                "options": [{"key": "only_last_week", "label": "Only vs. last week"}, {"key": "both", "label": "Down vs. both windows"}],
                "next": {"only_last_week": "TERMINAL_pv_window_noise", "both": "compliance"},
            },
            "compliance": {
                "check_label": "Local/compliance",
                "question": "Any recent consent-banner, cookie policy, or DPDP-related change?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No changes"}],
                "next": {"yes": "TERMINAL_pv_compliance", "no": "TERMINAL_pv_cap"},
            },
        },
        "terminals": {
            "TERMINAL_pv_tracking": {
                "title": "This looks like a tracking break, not a real traffic drop.",
                "body": "A deploy, tag change, or GA4/GTM update in the last 7 days is the most common cause of a page-views drop that isn't real — a bad tag fire, a broken config, or a misfired event can undercount real traffic.",
                "pull_steps": ["Pull the exact deploy/tag-change timestamp and compare it to when the drop started", "Check GA4 DebugView or Tag Assistant on the affected pages to confirm events are firing"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a tracking/technical issue, not a genuine traffic problem.",
                "reply_draft": "Early read: a recent tracking/tag change is the likely cause, not a real drop in visitors. Confirming in GA4 DebugView now, will have a clean answer shortly.",
            },
            "TERMINAL_pv_window_noise": {
                "title": "This looks like day-of-week noise, not a real trend.",
                "body": "The drop only shows up against last week, not against the same day last month — that's far more consistent with normal day-to-day variance than an actual decline.",
                "pull_steps": ["Compare the same day-of-week across the last 4-6 weeks, not just last week", "Check whether last week was itself unusually high, making this week look worse by comparison"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this reads as noise, not a genuine pattern.",
                "reply_draft": "Early read: this only looks down vs. last week specifically, more consistent with normal noise than a real trend. Pulling a longer comparison window to confirm, will follow up shortly.",
            },
            "TERMINAL_pv_compliance": {
                "title": "This looks like a consent/compliance change suppressing real sessions, not an actual drop.",
                "body": "A recent consent-banner, cookie policy, or DPDP-related change can silently suppress GA4 sessions for users who haven't consented yet — the traffic is still happening, GA4 just isn't counting all of it.",
                "pull_steps": ["Check GA4's consent-mode reporting for the unconsented/modeled traffic share", "Compare total sessions (including modeled) vs. observed sessions since the change"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a measurement/compliance artifact, not a genuine decline.",
                "reply_draft": "Early read: a recent consent/compliance change may be undercounting real traffic rather than traffic actually dropping. Checking GA4's consent-mode data now, will confirm shortly.",
            },
            "TERMINAL_pv_cap": {
                "title": "No single check found a clear cause — worth a second, finer-grained pass.",
                "body": "Tracking, device/channel concentration, comparison window, and compliance all came back clean. That doesn't rule out a real drop — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Re-run the device/channel breakdown at a finer grain (e.g. mobile app vs. mobile web specifically)", "Check for a channel-specific issue not covered above (a paused campaign, a broken referral partner)"],
                "handoff": None, "handoff_line": "No suite handoff — nothing here pointed at a retention or experiment-shaped cause specifically.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so it may be a genuine shift. Digging into channel-level detail now, will follow up soon.",
            },
        },
    },

    "engagement": {
        "vp_question": "Why is time on site down this month?",
        "root": "bot_spam",
        "nodes": {
            "bot_spam": {
                "check_label": "Bot/spam filter",
                "question": "Any spike in sessions with 0-second duration or single-page bounces from unfamiliar geographies?",
                "options": [{"key": "yes", "label": "Yes, that pattern is there"}, {"key": "no", "label": "No, doesn't look like bot traffic"}],
                "next": {"yes": "TERMINAL_eng_bot_spam", "no": "content_change"},
            },
            "content_change": {
                "check_label": "Content change",
                "question": "Was a page redesigned, a hero banner changed, or content removed in the affected period?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No changes"}],
                "next": {"yes": "page_concentration", "no": "page_concentration"},
            },
            "page_concentration": {
                "check_label": "Page-level concentration",
                "question": "Is the drop sitewide, or concentrated on specific page types — PDP, blog, homepage?",
                "options": [{"key": "concentrated", "label": "Specific page types"}, {"key": "sitewide", "label": "Sitewide"}],
                "next": {"concentrated": "new_user_mix", "sitewide": "new_user_mix"},
            },
            "new_user_mix": {
                "check_label": "New user mix",
                "question": "Has the new-vs-returning visitor ratio shifted toward more first-time visitors?",
                "options": [{"key": "yes", "label": "Yes, more first-timers"}, {"key": "no", "label": "No, mix unchanged"}],
                "next": {"yes": "site_speed", "no": "site_speed"},
            },
            "site_speed": {
                "check_label": "Site speed",
                "question": "Any recent increase in page load time or Core Web Vitals scores?",
                "options": [{"key": "yes", "label": "Yes, load times are up"}, {"key": "no", "label": "No, load time unchanged"}],
                "next": {"yes": "REDIRECT:performance", "no": "TERMINAL_eng_cap"},
            },
        },
        "terminals": {
            "TERMINAL_eng_bot_spam": {
                "title": "This looks like bot/spam traffic dragging down average engagement, not a real content problem.",
                "body": "A spike in near-zero-duration sessions or single-page bounces from unfamiliar geographies inflates session count while dragging every averaged engagement metric down — nothing about real visitor behavior has actually changed.",
                "pull_steps": ["Pull the geography/user-agent breakdown for the spike and confirm it matches known bot patterns", "Re-run the engagement numbers with that traffic segment excluded"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a data-quality issue, not a genuine engagement problem.",
                "reply_draft": "Early read: a spike in bot/spam-like sessions is likely dragging the average down, not a real engagement decline. Filtering it out to confirm, will follow up shortly.",
            },
            "TERMINAL_eng_cap": {
                "title": "No single check found a clear cause — this may be genuine acquisition-mix dilution.",
                "body": "Bot traffic, content changes, page concentration, and site speed all came back clean, but a shift toward more first-time visitors is still on the table — new visitors naturally engage less deeply than returning ones, which can pull the average down with nothing actually declining in quality.",
                "pull_steps": ["Segment engagement (time on site, pages/session) by new vs. returning visitors separately", "Confirm any recent campaign launch date/spend against the timing of the drop"],
                "handoff": None, "handoff_line": "No suite handoff — this reads as a mix-shift question, not retention or experiment-shaped.",
                "reply_draft": "Early read: nothing obvious broke, so this may be dilution from a shift toward more first-time visitors. Segmenting by new vs. returning to confirm, will follow up shortly.",
            },
        },
    },

    "conversion": {
        "vp_question": "Why did our conversion rate drop this week?",
        "root": "funnel_stage",
        "nodes": {
            "funnel_stage": {
                "check_label": "Funnel stage isolation",
                "question": "Which specific step dropped — PDP view→Add to Cart, Cart→Checkout start, or Checkout→Purchase?",
                "options": [{"key": "pdp_to_cart", "label": "PDP → Add to Cart"}, {"key": "cart_to_checkout", "label": "Cart → Checkout start"}, {"key": "checkout_to_purchase", "label": "Checkout → Purchase"}],
                "next": {"pdp_to_cart": "payment_errors", "cart_to_checkout": "payment_errors", "checkout_to_purchase": "payment_errors"},
            },
            "payment_errors": {
                "check_label": "Payment/checkout errors",
                "question": "Any spike in checkout errors, failed payment attempts, or gateway timeouts?",
                "options": [{"key": "yes", "label": "Yes, errors are up"}, {"key": "no", "label": "No, error rates look normal"}],
                "next": {"yes": "REDIRECT:payment_success", "no": "price_inventory"},
            },
            "price_inventory": {
                "check_label": "Price/inventory change",
                "question": "Any price increase, out-of-stock spike, or promo code expiration in the window?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No changes"}],
                "next": {"yes": "ab_test", "no": "ab_test"},
            },
            "ab_test": {
                "check_label": "A/B test contamination",
                "question": "Is there an active or recently-ended experiment touching this funnel?",
                "options": [{"key": "yes", "label": "Yes, one's running"}, {"key": "no", "label": "No experiment here"}],
                "next": {"yes": "TERMINAL_conv_ab_test", "no": "device_browser"},
            },
            "device_browser": {
                "check_label": "Device/browser specific",
                "question": "Is it concentrated on one browser or device, especially an older OS version?",
                "options": [{"key": "yes", "label": "Yes, one browser/device"}, {"key": "no", "label": "No, not device-specific"}],
                "next": {"yes": "TERMINAL_conv_device_browser", "no": "TERMINAL_conv_cap"},
            },
        },
        "terminals": {
            "TERMINAL_conv_ab_test": {
                "title": "This is likely a live A/B test dragging the blended average down, not a real conversion problem.",
                "body": "The \"drop\" may actually be a losing variant, or a test that hasn't been reverted yet, rather than a genuine conversion decline — the Experiment Designer decision rule should have caught this if one was running.",
                "pull_steps": ["Pull conversion rate split by variant (control vs. treatment) instead of the blended average", "Check the Experiment Designer decision rule for this test — see if a kill/extend threshold was already tripped"],
                "handoff": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py", "soft": False, "key": "experiment_designer"},
                "handoff_line": "Worth routing through Experiment Designer — the \"drop\" may just be a losing variant or a test that hasn't been reverted yet.",
                "reply_draft": "Early signal: we have an experiment live right now, so this is probably a losing variant dragging the blended rate down, not a real conversion issue. Pulling the per-variant split to confirm, will have a clean read shortly.",
            },
            "TERMINAL_conv_device_browser": {
                "title": "This looks like a checkout rendering bug on one browser/device, not a real preference change.",
                "body": "Concentration on a specific browser or device — especially an older OS version — points to a checkout UI rendering bug on that environment rather than a genuine shift in what customers want.",
                "pull_steps": ["Reproduce checkout on that specific browser/device/OS combination", "Check recent frontend deploys for anything touching checkout-page compatibility"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a frontend/compatibility bug, not retention or experiment-shaped.",
                "reply_draft": "Early read: the drop is concentrated on one browser/device, which points to a checkout rendering bug there rather than a real conversion decline. Reproducing it now, will confirm shortly.",
            },
            "TERMINAL_conv_cap": {
                "title": "No single check found a clear cause — worth a second, finer-grained pass.",
                "body": "Funnel stage, payment errors, price/inventory, A/B tests, and device concentration all came back clean. That doesn't rule out a real drop — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Re-run the funnel breakdown by traffic source to check for a source-specific issue", "Check for a subtler UX change (copy, layout, button placement) in the affected step"],
                "handoff": None, "handoff_line": "No suite handoff — nothing here pointed at a retention or experiment-shaped cause specifically.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so it may be a genuine shift. Digging into source-level detail now, will follow up soon.",
            },
        },
    },

    "revenue": {
        "vp_question": "Why is revenue down this week?",
        "root": "volume_vs_value",
        "nodes": {
            "volume_vs_value": {
                "check_label": "Volume vs. value",
                "question": "Did order count drop, or did AOV drop while order count held steady?",
                "options": [{"key": "count_dropped", "label": "Order count dropped"}, {"key": "aov_dropped", "label": "AOV dropped, count steady"}],
                "next": {"count_dropped": "refunds", "aov_dropped": "REDIRECT:aov"},
            },
            "refunds": {
                "check_label": "Refunds/cancellations",
                "question": "Any spike in refund or cancellation rate in the same window?",
                "options": [{"key": "yes", "label": "Yes, refunds are up"}, {"key": "no", "label": "No, refunds are steady"}],
                "next": {"yes": "TERMINAL_rev_refunds", "no": "category_concentration"},
            },
            "category_concentration": {
                "check_label": "Category/SKU concentration",
                "question": "Is the drop sitewide or concentrated in specific categories?",
                "options": [{"key": "concentrated", "label": "Specific categories"}, {"key": "sitewide", "label": "Sitewide"}],
                "next": {"concentrated": "seasonality", "sitewide": "seasonality"},
            },
            "seasonality": {
                "check_label": "Seasonality/calendar",
                "question": "Any holiday, payday cycle, or known seasonal dip this maps to?",
                "options": [{"key": "yes", "label": "Yes, a known seasonal pattern"}, {"key": "no", "label": "No seasonal pattern"}],
                "next": {"yes": "TERMINAL_rev_seasonality", "no": "reporting"},
            },
            "reporting": {
                "check_label": "Currency/reporting",
                "question": "Any change in how revenue is being attributed or reported — gross vs. net, timezone cutoff?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No change"}],
                "next": {"yes": "TERMINAL_rev_reporting", "no": "TERMINAL_rev_cap"},
            },
        },
        "terminals": {
            "TERMINAL_rev_refunds": {
                "title": "This looks like a refund/cancellation spike eating net revenue, not a gross demand problem.",
                "body": "Gross revenue may look fine but net revenue is being eaten after the fact by a spike in refunds or cancellations — the demand-side numbers can look healthy while the number that matters (net) is actually down.",
                "pull_steps": ["Pull refund/cancellation rate by category and reason code for the affected window", "Compare gross vs. net revenue trend lines side by side to confirm the gap"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is an ops/quality issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: a refund/cancellation spike looks like the real driver, not a gross demand decline. Pulling the reason-code breakdown now, will confirm shortly.",
            },
            "TERMINAL_rev_seasonality": {
                "title": "This looks like a known seasonal dip, not a structural revenue problem.",
                "body": "The drop is concentrated in specific categories with a documented seasonal pattern — worth comparing to the same period last year before treating this as a real decline.",
                "pull_steps": ["Pull the affected category's revenue for the same period last year to confirm the pattern repeats", "Check whether other categories are flat or growing in the same window"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this reads as calendar-driven, not a retention or acquisition problem.",
                "reply_draft": "Early read: this matches a seasonal dip we've seen before in this category. Confirming against last year's numbers, will confirm by EOD.",
            },
            "TERMINAL_rev_reporting": {
                "title": "This may be a reporting artifact, not an actual revenue change.",
                "body": "A change in how revenue is attributed or reported — gross vs. net, a timezone cutoff shift — can make real revenue look like it moved when the underlying business didn't change at all.",
                "pull_steps": ["Reconcile the reporting change against the raw transaction log for the same window", "Recompute the metric using the old reporting definition to isolate the artifact"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a reporting/measurement issue, not a genuine revenue change.",
                "reply_draft": "Early read: a recent reporting change may be making this look like a decline when it isn't. Reconciling against the raw transaction log now, will confirm shortly.",
            },
            "TERMINAL_rev_cap": {
                "title": "No single check found a clear cause — worth a second, finer-grained pass.",
                "body": "Volume/value split, refunds, category concentration, seasonality, and reporting all came back clean. That doesn't rule out a real drop — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Re-run the breakdown by acquisition channel to check for a channel-specific issue", "Check for a pricing or catalog change not covered above"],
                "handoff": None, "handoff_line": "No suite handoff — nothing here pointed at a retention or experiment-shaped cause specifically.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so it may be a genuine shift. Digging into channel-level detail now, will follow up soon.",
            },
        },
    },

    "repeat_rate": {
        "vp_question": "Why is our repeat purchase rate down?",
        "root": "cohort_vs_blended",
        "nodes": {
            "cohort_vs_blended": {
                "check_label": "Cohort vs. blended",
                "question": "Is this the blended repeat rate across all customers, or a specific cohort's repeat rate?",
                "options": [{"key": "blended", "label": "Blended, across everyone"}, {"key": "cohort_specific", "label": "One specific cohort"}],
                "next": {"blended": "discount_dependency", "cohort_specific": "discount_dependency"},
            },
            "discount_dependency": {
                "check_label": "Discount dependency",
                "question": "Was a first-order discount reduced or removed recently?",
                "options": [{"key": "yes", "label": "Yes, discount was cut"}, {"key": "no", "label": "No discount change"}],
                "next": {"yes": "crm_disruption", "no": "crm_disruption"},
            },
            "crm_disruption": {
                "check_label": "CRM/lifecycle disruption",
                "question": "Was a WhatsApp/email/push campaign paused, or did a CRM tool change or break?",
                "options": [{"key": "yes", "label": "Yes, something broke/paused"}, {"key": "no", "label": "No disruption"}],
                "next": {"yes": "time_window", "no": "time_window"},
            },
            "time_window": {
                "check_label": "Time window",
                "question": "Is the measurement window shorter than your typical repeat-purchase gap?",
                "options": [{"key": "yes", "label": "Yes, window's too short"}, {"key": "no", "label": "No, window is long enough"}],
                "next": {"yes": "TERMINAL_rr_time_window", "no": "competitive_event"},
            },
            "competitive_event": {
                "check_label": "Competitive event",
                "question": "Any known competitor promo, price war, or new entrant in the market during this period?",
                "options": [{"key": "yes", "label": "Yes, there's a competitive event"}, {"key": "no", "label": "No competitive event"}],
                "next": {"yes": "TERMINAL_rr_competitive", "no": "TERMINAL_rr_cap"},
            },
        },
        "terminals": {
            "TERMINAL_rr_time_window": {
                "title": "This looks like a measurement-window issue, not an actual decline in repeat behavior.",
                "body": "You may be measuring too early — customers due to repeat haven't hit their typical window yet, so the rate isn't down, the clock is just being checked too soon.",
                "pull_steps": ["Recompute repeat rate using a wider window matching your real typical repeat gap", "Pull the actual days-to-second-order distribution for the last 2-3 cohorts to confirm the real gap"],
                "handoff": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py", "soft": True, "key": "funnel_diagnostics"},
                "handoff_line": "Worth a Funnel Diagnostics pass once the window is corrected — cohort-level data will confirm whether this is genuinely a timing artifact.",
                "reply_draft": "Early read: we may be measuring repeat rate too early relative to our real repeat gap. Recomputing with a wider window now, will confirm shortly.",
            },
            "TERMINAL_rr_competitive": {
                "title": "This may be temporary share-shift from a competitive event, not structural churn.",
                "body": "A known competitor promo, price war, or new entrant can pull customers away temporarily without reflecting any real change in loyalty to your own product.",
                "pull_steps": ["Track whether affected customers return once the competitive event ends", "Compare repeat rate for cohorts acquired before vs. during the competitive event"],
                "handoff": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py", "soft": True, "key": "funnel_diagnostics"},
                "handoff_line": "Worth a Funnel Diagnostics pass — cohort-level data will show whether this recovers once the competitive event passes.",
                "reply_draft": "Early read: a known competitive event may be pulling customers away temporarily, not a real loyalty decline. Tracking whether they return, will follow up shortly.",
            },
            "TERMINAL_rr_cap": {
                "title": "No single check found a clear cause — worth a cohort-level pass.",
                "body": "Cohort mix, discount changes, CRM disruption, measurement window, and competitive events all came back clean. That doesn't rule out a real decline — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Run the full cohort data through Funnel Diagnostics to separate genuine decline from blended dilution", "Check for a product or catalog change affecting repeat purchase specifically"],
                "handoff": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py", "soft": True, "key": "funnel_diagnostics"},
                "handoff_line": "Worth a Funnel Diagnostics pass — cohort-level data will show whether this is genuine or just noise.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly. Running the cohort data through Funnel Diagnostics now, will follow up shortly.",
            },
        },
    },

    "aov": {
        "vp_question": "Why is our average order value trending down?",
        "root": "mix_shift",
        "nodes": {
            "mix_shift": {
                "check_label": "Mix shift",
                "question": "Has the product/category mix of orders shifted toward lower-priced items?",
                "options": [{"key": "yes", "label": "Yes, mix has shifted"}, {"key": "no", "label": "No, mix unchanged"}],
                "next": {"yes": "discount_depth", "no": "discount_depth"},
            },
            "discount_depth": {
                "check_label": "Discount depth",
                "question": "Has discount percentage or coupon usage increased?",
                "options": [{"key": "yes", "label": "Yes, discount usage is up"}, {"key": "no", "label": "No, discount depth flat"}],
                "next": {"yes": "TERMINAL_aov_discount_depth", "no": "bundle_upsell"},
            },
            "bundle_upsell": {
                "check_label": "Bundle/upsell performance",
                "question": "Has a bundle, \"frequently bought together,\" or upsell module been removed or broken?",
                "options": [{"key": "yes", "label": "Yes, it changed/broke"}, {"key": "no", "label": "No, still live and working"}],
                "next": {"yes": "TERMINAL_aov_bundle_upsell", "no": "new_customer_mix"},
            },
            "new_customer_mix": {
                "check_label": "New customer mix",
                "question": "Are new customers — who typically order smaller, exploratory first orders — a larger share of orders this period?",
                "options": [{"key": "yes", "label": "Yes, new customers are up"}, {"key": "no", "label": "No, share unchanged"}],
                "next": {"yes": "payment_method", "no": "payment_method"},
            },
            "payment_method": {
                "check_label": "Payment method shift",
                "question": "Has there been a shift toward COD or a payment method associated with smaller average baskets?",
                "options": [{"key": "yes", "label": "Yes, a shift happened"}, {"key": "no", "label": "No shift"}],
                "next": {"yes": "TERMINAL_aov_payment_method", "no": "TERMINAL_aov_cap"},
            },
        },
        "terminals": {
            "TERMINAL_aov_discount_depth": {
                "title": "This looks like deeper discounting eating net AOV, not fewer big-ticket orders.",
                "body": "Gross AOV may be flat, but net (post-discount) AOV is what's actually dropping if discount percentage or coupon usage has increased — the order sizes haven't shrunk, the take-home per order has.",
                "pull_steps": ["Compare gross vs. net AOV trend lines side by side to confirm the gap", "Check which coupon codes or discount tiers saw the biggest usage increase"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a pricing/promo issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: increased discount usage looks like the real driver, not a drop in order size. Comparing gross vs. net AOV now, will confirm shortly.",
            },
            "TERMINAL_aov_bundle_upsell": {
                "title": "This looks like a broken bundle/upsell module, not a demand or pricing issue.",
                "body": "If a bundle, \"frequently bought together,\" or upsell module was removed or broke, customers simply aren't being offered the higher-basket path anymore — a fixable UI/merchandising issue, not a real preference shift.",
                "pull_steps": ["Check whether the module is still rendering correctly on PDP/cart", "Compare attach rate for that module before vs. after the change"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a merchandising/UI issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: a bundle/upsell module change looks like the real driver here. Checking whether it's still rendering correctly, will confirm shortly.",
            },
            "TERMINAL_aov_payment_method": {
                "title": "This looks like a payment-mix shift correlating with smaller baskets, not a real spending decline.",
                "body": "Some payment methods (like COD) correlate with smaller average basket sizes — a shift toward one of those can pull blended AOV down even if no individual customer is buying less per method.",
                "pull_steps": ["Split AOV by payment method for this period vs. the prior one", "Check whether the payment-mix shift correlates with a specific campaign or checkout change"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this reads as a payment-mix artifact, not a genuine spending decline.",
                "reply_draft": "Early read: a shift toward a lower-basket payment method looks like the real driver, not a genuine spending decline. Splitting AOV by method now, will confirm shortly.",
            },
            "TERMINAL_aov_cap": {
                "title": "No single check found a clear cause — worth checking new-customer dilution specifically.",
                "body": "Mix shift, discount depth, bundle/upsell, and payment method all came back clean, but a rising new-customer share is still on the table — new customers typically place smaller, exploratory first orders, which can pull blended AOV down with no per-customer decline underneath.",
                "pull_steps": ["Split AOV by new vs. returning customers for this period", "Compare per-cohort AOV — new customers this period vs. their own historical first-order AOV"],
                "handoff": {"label": "Funnel Diagnostics", "page": "pages/1_Funnel_Diagnostics.py", "soft": True, "key": "funnel_diagnostics"},
                "handoff_line": "Worth checking with Funnel Diagnostics — cohort-level data would confirm this is dilution, not decline.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so this may be new-customer dilution. Splitting AOV by cohort now, will follow up soon.",
            },
        },
    },

    "cart_abandon": {
        "vp_question": "Why is cart abandonment up this week?",
        "root": "checkout_friction",
        "nodes": {
            "checkout_friction": {
                "check_label": "Checkout friction",
                "question": "Any new field added to checkout — extra verification, mandatory account creation?",
                "options": [{"key": "yes", "label": "Yes, something was added"}, {"key": "no", "label": "No new friction"}],
                "next": {"yes": "TERMINAL_ca_checkout_friction", "no": "payment_options"},
            },
            "payment_options": {
                "check_label": "Payment options",
                "question": "Has a popular payment method — UPI, a specific wallet — had an outage or been removed?",
                "options": [{"key": "yes", "label": "Yes, a method is down/removed"}, {"key": "no", "label": "No disruption"}],
                "next": {"yes": "TERMINAL_ca_payment_options", "no": "shipping_surprise"},
            },
            "shipping_surprise": {
                "check_label": "Shipping cost/timeline surprise",
                "question": "Was shipping cost or delivery estimate changed, or made visible later in the flow than before?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No change"}],
                "next": {"yes": "TERMINAL_ca_shipping_surprise", "no": "device_browser"},
            },
            "device_browser": {
                "check_label": "Device/browser specific",
                "question": "Is it concentrated on mobile web specifically, vs. app or desktop?",
                "options": [{"key": "yes", "label": "Yes, mobile web specifically"}, {"key": "no", "label": "No, not mobile-web-specific"}],
                "next": {"yes": "retargeting", "no": "retargeting"},
            },
            "retargeting": {
                "check_label": "Retargeting/reminder disruption",
                "question": "Has an abandoned-cart email/WhatsApp reminder flow been paused or broken?",
                "options": [{"key": "yes", "label": "Yes, that flow broke/paused"}, {"key": "no", "label": "No disruption"}],
                "next": {"yes": "TERMINAL_ca_retargeting", "no": "TERMINAL_ca_cap"},
            },
        },
        "terminals": {
            "TERMINAL_ca_checkout_friction": {
                "title": "This looks like added checkout friction, the most common and most fixable cause of abandonment.",
                "body": "A mandatory verification step or new required field that wasn't there before is a strong candidate for the increase, especially if the timing lines up with when abandonment started rising.",
                "pull_steps": ["Pull abandonment rate specifically at the new field/step in the funnel breakdown", "Compare completion time and drop-off before vs. after it was added"],
                "handoff": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py", "soft": True, "key": "experiment_designer"},
                "handoff_line": "Worth routing the rollback or a lighter version through Experiment Designer to validate before removing it outright.",
                "reply_draft": "Early signal: a new checkout step lines up with the abandonment increase. Pulling step-level funnel data to confirm, will have a clean answer shortly.",
            },
            "TERMINAL_ca_payment_options": {
                "title": "This looks like a payment-method outage or removal, not a checkout UX problem.",
                "body": "If a popular payment method had an outage or was removed, customers who specifically wanted that option are abandoning rather than switching — a vendor/availability issue, not a UX one.",
                "pull_steps": ["Check payment gateway status/uptime for the affected method in this window", "Confirm whether the method was intentionally removed or is a live outage"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a vendor/availability issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: a payment method outage or removal looks like the real driver here. Checking gateway status now, will confirm shortly.",
            },
            "TERMINAL_ca_shipping_surprise": {
                "title": "This looks like a shipping cost/timeline surprise, a top abandonment driver.",
                "body": "Surprise costs or delivery estimates disclosed later in the flow than before are one of the most common abandonment drivers — customers commit, hit an unexpected number, and leave.",
                "pull_steps": ["Check where in the flow shipping info is currently disclosed vs. before", "Compare abandonment rate at the exact step where the surprise now appears"],
                "handoff": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py", "soft": True, "key": "experiment_designer"},
                "handoff_line": "Worth routing the fix (disclosing shipping earlier) through Experiment Designer to validate the recovery.",
                "reply_draft": "Early signal: a shipping cost/timeline change lines up with the abandonment increase. Pulling step-level data to confirm, will have a clean answer shortly.",
            },
            "TERMINAL_ca_retargeting": {
                "title": "This looks like a broken recovery flow, not a real increase in initial abandonment.",
                "body": "If an abandoned-cart reminder flow has been paused or broken, fewer abandoned carts are being recovered afterward — that can look like \"abandonment increasing\" even if the initial abandon rate itself is stable.",
                "pull_steps": ["Confirm the reminder flow's send/delivery status in the CRM tool", "Compare recovery rate before vs. after the suspected disruption"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a CRM/ops issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: a broken reminder flow looks like the real driver, not a genuine rise in abandonment. Confirming the flow's status now, will follow up shortly.",
            },
            "TERMINAL_ca_cap": {
                "title": "No single check found a clear cause — worth a second, finer-grained pass.",
                "body": "Checkout friction, payment options, shipping disclosure, device concentration, and retargeting all came back clean. That doesn't rule out a real increase — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Re-run the abandonment breakdown by traffic source or campaign", "Check for a subtler UX change (copy, button placement) in the checkout flow"],
                "handoff": None, "handoff_line": "No suite handoff — nothing here pointed at a retention or experiment-shaped cause specifically.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so it may be a genuine shift. Digging into source-level detail now, will follow up soon.",
            },
        },
    },

    "search_conv": {
        "vp_question": "Why is on-site search conversion down?",
        "root": "zero_result",
        "nodes": {
            "zero_result": {
                "check_label": "Zero-result rate",
                "question": "Has the percentage of searches returning zero results increased?",
                "options": [{"key": "yes", "label": "Yes, zero-result rate is up"}, {"key": "no", "label": "No, it's steady"}],
                "next": {"yes": "TERMINAL_sc_zero_result", "no": "ranking_change"},
            },
            "ranking_change": {
                "check_label": "Ranking/relevance change",
                "question": "Was the search ranking algorithm, synonym list, or personalization logic changed recently?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No change"}],
                "next": {"yes": "TERMINAL_sc_ranking_change", "no": "query_pattern"},
            },
            "query_pattern": {
                "check_label": "Query pattern shift",
                "question": "Has the mix of query types changed — more brand-name searches vs. category searches?",
                "options": [{"key": "yes", "label": "Yes, mix has shifted"}, {"key": "no", "label": "No, mix unchanged"}],
                "next": {"yes": "autocomplete", "no": "autocomplete"},
            },
            "autocomplete": {
                "check_label": "Autocomplete/typo tolerance",
                "question": "Any recent change to autocomplete suggestions or fuzzy-match/typo-tolerance settings?",
                "options": [{"key": "yes", "label": "Yes, something changed"}, {"key": "no", "label": "No change"}],
                "next": {"yes": "TERMINAL_sc_autocomplete", "no": "inventory_top_results"},
            },
            "inventory_top_results": {
                "check_label": "Inventory at top results",
                "question": "Are the top-ranked results for common queries out of stock?",
                "options": [{"key": "yes", "label": "Yes, top results are OOS"}, {"key": "no", "label": "No, top results in stock"}],
                "next": {"yes": "TERMINAL_sc_inventory", "no": "TERMINAL_sc_cap"},
            },
        },
        "terminals": {
            "TERMINAL_sc_zero_result": {
                "title": "This looks like a catalog/inventory sync issue, not a search relevance problem.",
                "body": "A rising zero-result rate is most often a catalog/inventory sync issue, or a new query pattern not mapped to any SKU — not a change in how well search understands what people want.",
                "pull_steps": ["Pull the top zero-result queries and check if they map to recently out-of-stock or delisted SKUs", "Check catalog sync job logs for failures or delays in the affected window"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this reads as a catalog/sync issue, not a retention or experiment question.",
                "reply_draft": "Early read: zero-result rate has spiked, which usually points to a catalog sync issue rather than a relevance problem. Checking sync logs now, will confirm shortly.",
            },
            "TERMINAL_sc_ranking_change": {
                "title": "This looks like a ranking/relevance regression from a recent change, not a catalog issue.",
                "body": "A recent change to the ranking algorithm, synonym list, or personalization logic may have actually regressed relevance for common queries, even if it was intended as an improvement.",
                "pull_steps": ["Compare top results for high-traffic queries before vs. after the change", "Check conversion rate specifically for queries most affected by the change"],
                "handoff": {"label": "Experiment Designer", "page": "pages/3_Experiment_Designer.py", "soft": True, "key": "experiment_designer"},
                "handoff_line": "Worth routing a rollback or a controlled re-test through Experiment Designer before committing either way.",
                "reply_draft": "Early read: a recent ranking/relevance change may have regressed results for common queries. Comparing before/after now, will confirm shortly.",
            },
            "TERMINAL_sc_autocomplete": {
                "title": "This looks like reduced typo tolerance silently increasing zero-result rate.",
                "body": "A recent change to autocomplete suggestions or fuzzy-match/typo-tolerance settings can silently increase zero-result rate for common misspellings, even without the raw zero-result metric itself flagging it first.",
                "pull_steps": ["Test a sample of common misspellings/typos manually in live search", "Compare autocomplete suggestion quality before vs. after the change"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this reads as a search-config issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: a recent autocomplete/typo-tolerance change looks like the real driver. Testing common misspellings now, will confirm shortly.",
            },
            "TERMINAL_sc_inventory": {
                "title": "This looks like an inventory problem wearing a search-relevance costume.",
                "body": "Zero-result rate, ranking logic, query mix, and autocomplete are all unchanged — but the top-ranked results for several common queries are currently out of stock. Search is technically doing its job; it's just pointing shoppers at products they can't buy.",
                "pull_steps": ["Pull the top highest-traffic queries and check in-stock status of their top-ranked results", "Loop in inventory/catalog to confirm restock timing for the affected top SKUs"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this reads as an inventory/catalog issue, not a relevance or retention problem.",
                "reply_draft": "Early read: search relevance itself looks fine — the issue is top-ranked results for common queries are out of stock. Pulling the affected SKU list now, will confirm shortly.",
            },
            "TERMINAL_sc_cap": {
                "title": "No single check found a clear cause — worth a second, finer-grained pass.",
                "body": "Zero-result rate, ranking changes, query mix, autocomplete, and top-result inventory all came back clean. That doesn't rule out a real drop — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Re-run the analysis segmented by device or app version", "Check for a subtler UI change to the search results page itself"],
                "handoff": None, "handoff_line": "No suite handoff — nothing here pointed at a retention or experiment-shaped cause specifically.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so it may be a genuine shift. Digging into device-level detail now, will follow up soon.",
            },
        },
    },

    "performance": {
        "vp_question": "Why did our site suddenly get slower?",
        "root": "deploy_correlation",
        "nodes": {
            "deploy_correlation": {
                "check_label": "Recent deploy correlation",
                "question": "Did the slowdown start right after a deploy, a third-party script addition, or a CDN change?",
                "options": [{"key": "yes", "label": "Yes, right after a deploy"}, {"key": "no", "label": "No, not deploy-correlated"}],
                "next": {"yes": "TERMINAL_perf_deploy", "no": "third_party_script"},
            },
            "third_party_script": {
                "check_label": "Third-party script audit",
                "question": "Any new tracking pixel, chat widget, or ad script added recently?",
                "options": [{"key": "yes", "label": "Yes, a new script was added"}, {"key": "no", "label": "No new script"}],
                "next": {"yes": "TERMINAL_perf_third_party", "no": "geography_cdn"},
            },
            "geography_cdn": {
                "check_label": "Geography/CDN concentration",
                "question": "Is the slowdown global, or concentrated in specific regions?",
                "options": [{"key": "concentrated", "label": "Specific regions"}, {"key": "global", "label": "Global"}],
                "next": {"concentrated": "TERMINAL_perf_geography", "global": "image_asset"},
            },
            "image_asset": {
                "check_label": "Image/asset size",
                "question": "Were new images, banners, or video assets added without compression?",
                "options": [{"key": "yes", "label": "Yes, uncompressed assets"}, {"key": "no", "label": "No new heavy assets"}],
                "next": {"yes": "TERMINAL_perf_image_asset", "no": "device_connection"},
            },
            "device_connection": {
                "check_label": "Device/connection type",
                "question": "Is it concentrated on mobile/slower connections, or uniform across all users?",
                "options": [{"key": "concentrated_mobile", "label": "Mobile/slow connections"}, {"key": "uniform", "label": "Uniform across all users"}],
                "next": {"concentrated_mobile": "TERMINAL_perf_device_connection", "uniform": "TERMINAL_perf_cap"},
            },
        },
        "terminals": {
            "TERMINAL_perf_deploy": {
                "title": "This is almost certainly deploy-correlated.",
                "body": "Performance regressions that start right after a deploy are deploy-correlated far more often than not — check what shipped in that window before looking anywhere else.",
                "pull_steps": ["Pull the deploy diff and check for anything touching page load, scripts, or the asset pipeline", "Compare Core Web Vitals before vs. after the exact deploy timestamp"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a deploy/infra issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: the slowdown lines up almost exactly with a recent deploy. Pulling the deploy diff now, will confirm the specific change shortly.",
            },
            "TERMINAL_perf_third_party": {
                "title": "This looks like a new third-party script causing a silent performance regression.",
                "body": "Third-party scripts — tracking pixels, chat widgets, ad tags — are a top cause of silent performance regressions; they often load render-blocking resources that don't show up in an obvious code review.",
                "pull_steps": ["Check the network waterfall for new blocking requests from the added script", "Test load time with the new script temporarily disabled"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a frontend/vendor-script issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: a newly added third-party script looks like the likely cause. Checking the network waterfall now, will confirm shortly.",
            },
            "TERMINAL_perf_geography": {
                "title": "This looks like a CDN edge-node or regional infrastructure issue, not an application problem.",
                "body": "Slowdown concentrated in specific regions rather than global points to a CDN edge-node or regional infrastructure issue, not a code-level performance regression.",
                "pull_steps": ["Check CDN edge-node status/health for the affected regions", "Compare response times from that region's edge vs. the nearest healthy one"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a vendor/infra issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: the slowdown is concentrated in specific regions, which points to a CDN/regional infra issue. Checking edge-node status now, will confirm shortly.",
            },
            "TERMINAL_perf_image_asset": {
                "title": "This looks like new uncompressed assets, a straightforward and fixable cause.",
                "body": "New images, banners, or video assets added without compression are one of the most common and easiest-to-fix causes of a sudden slowdown.",
                "pull_steps": ["Check asset sizes on the affected pages specifically", "Re-compress and re-deploy the offending assets, then re-measure"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a straightforward asset-optimization fix, not retention or experiment-shaped.",
                "reply_draft": "Early read: newly added uncompressed assets look like the likely cause. Checking asset sizes on the affected pages now, will confirm shortly.",
            },
            "TERMINAL_perf_device_connection": {
                "title": "This looks like a render-blocking resource or unoptimized mobile bundle, not a backend issue.",
                "body": "Concentration on mobile or slower connections, with nothing else explaining the slowdown, points to a render-blocking resource or an unoptimized mobile-specific bundle rather than anything backend-side.",
                "pull_steps": ["Run a mobile-specific Lighthouse/PageSpeed audit on the affected pages", "Check for a recent mobile-bundle size increase or a newly render-blocking script"],
                "handoff": None, "handoff_line": "Not a suite handoff case — this is a frontend/mobile-performance issue, not retention or experiment-shaped.",
                "reply_draft": "Early read: the slowdown is concentrated on mobile/slower connections, which points to a frontend issue there. Running a mobile audit now, will confirm shortly.",
            },
            "TERMINAL_perf_cap": {
                "title": "No single check found a clear cause — worth a deeper infra-level pass.",
                "body": "Deploy correlation, third-party scripts, geography/CDN, asset size, and device concentration all came back clean. That doesn't rule out a real slowdown — it just means the standard checks didn't catch it at this grain.",
                "pull_steps": ["Pull backend response-time percentiles (p50/p95/p99) to rule out server-side latency", "Check database/query performance for the affected window"],
                "handoff": None, "handoff_line": "No suite handoff — nothing here pointed at a retention or experiment-shaped cause specifically.",
                "reply_draft": "Early read: none of the usual quick checks explain this cleanly, so it may be a backend-side issue. Pulling server response-time data now, will follow up soon.",
            },
        },
    },
}
