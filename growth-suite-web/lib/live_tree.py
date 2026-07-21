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
}
