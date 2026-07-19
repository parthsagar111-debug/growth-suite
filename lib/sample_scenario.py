"""
First Response — the "Try the demo" canned walkthrough.

Matches the Page Views / mobile-direct-drop example from
first_response_mockup.html exactly: three answered checks (tracking,
concentration, channel), stopped before a fourth answer was needed,
diagnosed as a tracking/deep-link issue rather than a real traffic
drop. No Groq call — this is a static replay so the demo works even
without GROQ_API_KEY configured, and always renders identically.

Per direct correction: the mockup's "Not a Retention Autopsy case —
yet" is rewritten to "Not a Funnel Diagnostics case — yet" (Retention
Autopsy doesn't exist in this build; Funnel Diagnostics is the real
page that plays that role).
"""

CATEGORY = "page_views"

VP_QUESTION = "Why are page views down this week?"

TRANSCRIPT = [
    {
        "check_label": "Tracking",
        "question": "Any deploy, tag change, or GA4/GTM update in the last 7 days?",
        "answer": "No deploys that I know of.",
        "branch_note": "tracking ruled out, now isolating where it's happening",
    },
    {
        "check_label": "Concentration",
        "question": "Is the drop uniform across devices, or concentrated on one — mobile or desktop?",
        "answer": "Mostly mobile, desktop looks normal.",
        "branch_note": "device isolated to mobile, narrowing to acquisition source",
    },
    {
        "check_label": "Channel",
        "question": "Within that, which channel dropped — organic, paid, direct, or referral?",
        "answer": "Direct mostly, organic looks okay.",
        "branch_note": "narrowed to direct",
    },
]

# The 4th check was asked but the session stopped before it needed an
# answer — the accumulated pattern (mobile + direct, everything else
# flat) already matched this tree's documented common false alarm.
STOPPED_AT_QUESTION = 4
PENDING_QUESTION = {
    "check_label": "Comparison window",
    "question": "Is this down vs. the same day last week AND last month, or just one of those?",
}

DIAGNOSIS = {
    "title": "This looks like a mobile app deep-link or tracking issue, not a real traffic drop.",
    "body": ("Mobile-direct-specific drops, with desktop and organic both normal, almost never indicate a "
             "genuine demand decline — direct traffic doesn't behave that way on its own. The pattern "
             "matches a broken deep link, an app tracking SDK issue, or a silent GA4 consent-mode change "
             "more than an actual user drop-off."),
    "pull_steps": [
        "GA4 → Reports → Tech → Overview → filter device = mobile, channel = direct, last 14 days",
        "Check app deep-link redirect logs (or Branch/AppsFlyer dashboard if you use one) for failed "
        "opens in the same window",
        "Ask engineering: any GTM container publish or consent-mode change in the last 7 days, even a "
        "minor one",
    ],
    "handoff": None,
    "handoff_line": ("Not a Funnel Diagnostics case — yet. This reads as a tracking/technical issue, not "
                      "a genuine engagement problem. If GA4 confirms the numbers are real (not a tracking "
                      "artifact), bring the corrected data back here to check if it's a retention pattern."),
    "reply_draft": ("Looking into it — early signal points to mobile-direct traffic specifically, which "
                     "usually means a tracking or deep-link issue rather than a real drop. Confirming with "
                     "GA4 and eng, will have a clean answer by EOD."),
}
