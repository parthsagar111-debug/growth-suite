"""
First Response — the AI interpretation layer.

Everything decision-shaped lives in decision_tree.py as data. This
module's job is deliberately narrow, per the brief's non-negotiable
architecture principle (deterministic logic first, AI interpretation
second): given the current tree/check and the PM's free-text answer,

  1. classify the answer into one of that check's pre-defined branch
     keys — strict mode: if it doesn't cleanly map, say so instead of
     guessing, so the caller can ask for clarification within the
     existing tree rather than inventing a new path;
  2. judge (a genuine model call, not a hardcoded rule) whether enough
     signal has accumulated to stop before the 5-question cap; and
  3. once stopped, phrase the hypothesis / "what to pull" / draft reply
     in natural language — but strictly grounded in the branch outcome
     text and handoff facts already resolved deterministically in
     decision_tree.py. The model is never the one deciding WHICH
     handoff applies; it only explains a decision Python already made.

Pinned to groq==1.5.0 specifically — an earlier 0.11.0 pin broke in
production with `Client.__init__() got an unexpected keyword argument
'proxies'` once a newer httpx dropped that argument.

Ported verbatim from the Streamlit app's lib/ai_diagnostic.py — zero
framework dependency. Not called by any route yet in this project;
every First Response category currently uses the scripted walkthrough
in sample_scenario.py instead (same reliability tradeoff as the
Streamlit build). Kept here so a live diagnostic chat mode can be
wired in later without re-porting this file.
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

_client = None
_client_tried = False


def is_configured() -> bool:
    return bool(GROQ_API_KEY)


def _get_client():
    """Lazy, guarded client construction — mirrors lib/data.py's _supabase()
    pattern: never let missing config or a bad import crash the page."""
    global _client, _client_tried
    if _client_tried:
        return _client
    _client_tried = True
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        _client = Groq(api_key=GROQ_API_KEY)
    except Exception:
        _client = None
    return _client


def _call_json(system_prompt: str, user_prompt: str) -> dict | None:
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None


_CLASSIFY_SYSTEM = """You are the branch-classification layer for "First Response," a PM diagnostic \
tool. You are NOT diagnosing anything yourself — a fixed decision tree already defines every valid \
branch. Your only job this turn:

1. Read the check's question and its pre-defined branch options (given as a JSON object mapping \
branch-key to a short description of what that branch means).
2. Read the PM's free-text answer.
3. Decide which single branch-key the answer cleanly maps to.
4. Decide, given the running history of already-resolved checks in this session, whether enough \
signal now exists to stop asking further questions and move to a diagnosis.

Strict mode rules:
- If the answer doesn't cleanly map to any of the given branch-keys, set "branch" to null and \
"confidence" to "unclear" — do NOT guess, do NOT invent a new branch that isn't in the list.
- Only set "stop" to true if the accumulated pattern (this answer plus prior ones) reasonably \
matches a genuine resolution — e.g. a "boring cause" check confirmed, or the pattern matches the \
tree's documented common false alarm, or isolation is already tight enough that further questions \
in this tree would be redundant. Never stop just because you're bored of asking questions.
- Never claim a "confirmed" cause anywhere, including in "stop_reason" — hypothesis language only.

Respond with ONLY a JSON object: {"branch": "<key>" or null, "confidence": "clear" or "unclear", \
"stop": true or false, "stop_reason": "<one short clause, or empty string if stop is false>"}"""


def classify_and_judge(tree_id: str, check: dict, answer_text: str, history: list) -> dict:
    """Returns {"branch": key|None, "confidence": "clear"|"unclear", "stop": bool,
    "stop_reason": str, "unavailable": bool}. `history` is the list of already-
    resolved steps this session: [{"question":.., "answer":.., "branch_note":..}, ...]
    (cross-tree — spans a redirect if one happened)."""
    branch_options = {k: v.get("note") or k for k, v in check["branches"].items()}
    payload = {
        "check_label": check["label"],
        "question": check["question"],
        "branch_options": branch_options,
        "pm_answer": answer_text,
        "history_so_far": [{"check": h["check_label"], "answer": h["answer"], "resolved_as": h["branch_note"]}
                            for h in history],
    }
    result = _call_json(_CLASSIFY_SYSTEM, json.dumps(payload))
    if result is None:
        return {"branch": None, "confidence": "unclear", "stop": False, "stop_reason": "",
                "unavailable": True}
    branch = result.get("branch")
    if branch not in check["branches"]:
        branch = None
    return {
        "branch": branch,
        "confidence": result.get("confidence", "unclear"),
        "stop": bool(result.get("stop")) if branch else False,
        "stop_reason": result.get("stop_reason", ""),
        "unavailable": False,
    }


_DIAGNOSIS_SYSTEM = """You are the write-up layer for "First Response," a PM diagnostic tool. A fixed \
decision tree already determined every fact below — you are only phrasing it clearly, not deciding \
anything new. You will be given:

- the category being diagnosed,
- the ordered transcript of checks asked and how each was resolved (question, answer, branch outcome \
text already written by the tree),
- the tree's "common false alarm" pattern and/or grounding note, if any,
- a deterministically-resolved handoff fact: either a specific suite tool this case should hand off \
to (with a short reason already implied by the transcript), or an explicit instruction that this case \
does NOT warrant a handoff right now.

Your job:
1. Write a one-sentence hypothesis title (plain language, no jargon dump) framed as a hypothesis, \
never a confirmed cause.
2. Write a 2-3 sentence hypothesis body synthesizing the resolved branch outcomes into one coherent \
story — pull directly from the outcome text you were given, don't invent new causal claims that \
aren't grounded in it.
3. Write 3 concrete "what to pull" steps — specific, practical, tool-aware (name real dashboards/\
reports a PM would actually check: GA4, Search Console, gateway dashboards, deployment logs, etc.) \
that would let someone verify or refute this hypothesis.
4. If a handoff is warranted per the given fact, write ONE short sentence explaining why in plain \
language. If a handoff is NOT warranted, write ONE short sentence explicitly saying so and why not \
(never silently omit this — say it plainly).
5. Draft a short "buying time" reply (1-2 sentences, first person, casual-professional) the PM could \
send back to whoever asked, that names the early signal honestly without overclaiming.

Always frame the hypothesis as "verify before reporting up" in spirit — never assert a confirmed root \
cause anywhere in your output.

Respond with ONLY a JSON object: {"title": "...", "body": "...", "pull_steps": ["...", "...", "..."], \
"handoff_line": "...", "reply_draft": "..."}"""


def draft_diagnosis(category_name: str, transcript: list, common_false_alarm: str | None,
                     grounding_note: str | None, handoff: dict | None) -> dict | None:
    """`transcript`: [{"check_label":.., "question":.., "answer":.., "outcome":..}, ...].
    `handoff`: dict from decision_tree.resolve_handoff(), or None.
    Returns None if Groq isn't configured/reachable — caller should fall back
    to a plain, unstyled rendering of the raw transcript rather than crash."""
    payload = {
        "category": category_name,
        "transcript": transcript,
        "common_false_alarm": common_false_alarm,
        "grounding_note": grounding_note,
        "handoff_fact": (
            f"This case DOES warrant a handoff to {handoff['label']}."
            + (" (soft/optional — mention it as worth verifying, not urgent.)" if handoff and handoff.get("soft") else "")
            if handoff else
            "This case does NOT warrant a handoff to Funnel Diagnostics right now (the suite's default "
            "next step for anything cohort/retention-shaped) — say so explicitly and briefly explain why "
            "(e.g. it reads as a tracking/technical/infra issue instead), and note what would need to be "
            "true for it to become relevant later."
        ),
    }
    result = _call_json(_DIAGNOSIS_SYSTEM, json.dumps(payload))
    return result
