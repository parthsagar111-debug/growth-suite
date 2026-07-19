import streamlit as st
from lib import style, data, decision_tree as dt, ai_diagnostic as ai, sample_scenario

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("First Response")
st.markdown(
    '<p class="subtitle">Someone senior just asked why a metric is down. Get a branching diagnostic '
    'that tells you exactly what to investigate, in what order — before you touch the rest of the '
    'suite.</p>',
    unsafe_allow_html=True,
)

# ── Session state ────────────────────────────────────────────────────────
# fr_history entries: {"tree_id", "check_label", "question", "answer",
# "branch_note", "branch_data"}. fr_active_tree can differ from
# fr_category after a cross-tree redirect (e.g. Engagement -> Performance)
# — the total question count keeps counting across that switch, it never
# resets, since the 5-question cap is a session-wide safety limit, not a
# per-tree one.
_DEFAULTS = {
    "fr_phase": "intake", "fr_vp_question": "", "fr_category": None, "fr_active_tree": None,
    "fr_check_idx": 0, "fr_total_asked": 0, "fr_history": [], "fr_clarify": None,
    "fr_result": None, "fr_is_demo": False,
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


def _reset():
    for key, default in _DEFAULTS.items():
        st.session_state[key] = default


def _start_category(tree_id: str):
    st.session_state.fr_category = tree_id
    st.session_state.fr_active_tree = tree_id
    st.session_state.fr_check_idx = 0
    st.session_state.fr_total_asked = 0
    st.session_state.fr_history = []
    st.session_state.fr_clarify = None
    st.session_state.fr_result = None
    st.session_state.fr_is_demo = False
    st.session_state.fr_phase = "chat"


def _start_demo():
    st.session_state.fr_category = sample_scenario.CATEGORY
    st.session_state.fr_active_tree = sample_scenario.CATEGORY
    st.session_state.fr_vp_question = sample_scenario.VP_QUESTION
    st.session_state.fr_history = [
        {"tree_id": sample_scenario.CATEGORY, "check_label": t["check_label"], "question": t["question"],
         "answer": t["answer"], "branch_note": t["branch_note"], "branch_data": {}}
        for t in sample_scenario.TRANSCRIPT
    ]
    st.session_state.fr_total_asked = len(sample_scenario.TRANSCRIPT)
    st.session_state.fr_clarify = None
    st.session_state.fr_is_demo = True
    st.session_state.fr_result = dict(sample_scenario.DIAGNOSIS)
    st.session_state.fr_phase = "diagnosis"


# ── Phase 0: intake ──────────────────────────────────────────────────────
if st.session_state.fr_phase == "intake":
    with st.container(border=True):
        st.markdown('<div class="gs-agent-label">What\'s the question you need to answer?</div>',
                    unsafe_allow_html=True)
        st.caption("Paste it exactly as it landed — Slack ping, email, hallway ask, whatever prompted this.")
        st.session_state.fr_vp_question = st.text_input(
            "VP question", value=st.session_state.fr_vp_question,
            placeholder="Why are page views down this week?", label_visibility="collapsed",
        )

    if not ai.is_configured():
        st.info(
            "Live diagnostic chat needs `GROQ_API_KEY` configured — it isn't right now, so picking a "
            "category below won't work yet. The demo below still runs (it's fully pre-scripted, no AI "
            "call needed).",
            icon="ℹ️",
        )

    st.markdown("### Pick the metric category")
    categories = dt.category_list()
    for row_start in (0, 5):
        row_cols = st.columns(5)
        for col, (tid, name, icon, tag) in zip(row_cols, categories[row_start:row_start + 5]):
            with col:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:20px;'>{icon}</div>", unsafe_allow_html=True)
                    st.markdown(f"**{name}**")
                    st.caption(tag)
                    if st.button("Select", key=f"fr_cat_{tid}", use_container_width=True,
                                 disabled=not ai.is_configured()):
                        _start_category(tid)
                        st.rerun()

    st.divider()
    st.caption("Or see a full worked example first:")
    if st.button("▶ Try the demo — \"Page Views, mobile-direct drop\"", use_container_width=False):
        _start_demo()
        st.rerun()

# ── Phase 1 + 2: chat trace, then diagnosis ──────────────────────────────
else:
    tree = dt.get_tree(st.session_state.fr_active_tree)
    resolved = st.session_state.fr_result is not None

    if st.session_state.fr_vp_question:
        st.caption(f"“{st.session_state.fr_vp_question}”")

    # The demo replays a frozen mid-session frame (see the pending-question
    # note further down), so its header/dots should read "stopped at
    # question 4" per the mockup rather than the generic 3-answered count.
    stopped_at = (sample_scenario.STOPPED_AT_QUESTION if st.session_state.fr_is_demo
                  else st.session_state.fr_total_asked)
    header_sub = (f"stopped at question {stopped_at} · hypothesis, not confirmed"
                  if resolved else f"question {st.session_state.fr_total_asked + 1} of max {dt.MAX_QUESTIONS}")
    st.markdown(f"##### {'Diagnosis' if resolved else 'Diagnostic questions'} — {tree['name']} tree")
    st.caption(header_sub)

    # Depth dots — filled = answered, current = being asked (or, for the
    # demo, the one pending question frozen mid-ask), muted = not reached.
    show_current_dot = (not resolved) or (st.session_state.fr_is_demo and resolved)
    current_dot_idx = st.session_state.fr_total_asked if show_current_dot else None
    dots = []
    for i in range(dt.MAX_QUESTIONS):
        if i < st.session_state.fr_total_asked:
            color = "#6366f1"   # filled — accent, matches Growth Suite's primary
        elif i == current_dot_idx:
            color = "#d97706"   # current/pending — amber, same "not yet confirmed" meaning as the hyp badge
        else:
            color = "#e2e8f0"   # muted — matches the shared border token
        dots.append(f'<span style="width:9px;height:9px;border-radius:50%;background:{color};'
                     'display:inline-block;margin-right:5px;"></span>')
    st.markdown("".join(dots), unsafe_allow_html=True)

    with st.container(border=True):
        for h in st.session_state.fr_history:
            with st.chat_message("assistant"):
                st.caption(h["check_label"])
                st.write(h["question"])
                if h["branch_note"]:
                    st.caption(f"↳ {h['branch_note']}")
            with st.chat_message("user"):
                st.write(h["answer"])

        # Demo-only: replicate the mockup's exact frozen frame — a 4th
        # question shown as asked but never answered, because the
        # accumulated pattern already matched the tree's documented false
        # alarm before an answer was needed. Live mode never leaves a
        # question dangling like this — it always stops right after a
        # confirmed answer, which is the more consistent real behavior.
        if st.session_state.fr_is_demo and resolved:
            with st.chat_message("assistant"):
                st.caption(sample_scenario.PENDING_QUESTION["check_label"] + " — current")
                st.write(sample_scenario.PENDING_QUESTION["question"])

        if not resolved:
            if st.session_state.fr_clarify:
                with st.chat_message("assistant"):
                    st.caption(tree["checks"][st.session_state.fr_check_idx]["label"])
                    st.write(st.session_state.fr_clarify)
            else:
                current_check = tree["checks"][st.session_state.fr_check_idx]
                with st.chat_message("assistant"):
                    st.caption(current_check["label"])
                    st.write(current_check["question"])

    if not resolved:
        answer = st.chat_input("Your answer…")
        if answer:
            current_check = tree["checks"][st.session_state.fr_check_idx]
            judged = ai.classify_and_judge(
                st.session_state.fr_active_tree, current_check, answer,
                [{"check_label": h["check_label"], "answer": h["answer"], "branch_note": h["branch_note"]}
                 for h in st.session_state.fr_history],
            )
            if judged["unavailable"]:
                st.error("Couldn't reach the AI classification layer — check `GROQ_API_KEY` and try again.")
            elif judged["confidence"] != "clear" or judged["branch"] is None:
                options = ", ".join(current_check["branches"].keys())
                st.session_state.fr_clarify = (
                    f"That didn't clearly map to one of the options for this check — could you answer in "
                    f"terms of one of: {options}?"
                )
                st.rerun()
            else:
                branch_key = judged["branch"]
                branch_data = current_check["branches"][branch_key]
                st.session_state.fr_history.append({
                    "tree_id": st.session_state.fr_active_tree, "check_label": current_check["label"],
                    "question": current_check["question"], "answer": answer,
                    "branch_note": branch_data["note"], "branch_data": branch_data,
                })
                st.session_state.fr_total_asked += 1
                st.session_state.fr_clarify = None

                redirect = branch_data.get("redirect_tree")
                if redirect:
                    st.session_state.fr_active_tree = redirect
                    st.session_state.fr_check_idx = 0
                else:
                    st.session_state.fr_check_idx += 1

                hit_cap = st.session_state.fr_total_asked >= dt.MAX_QUESTIONS
                exhausted = st.session_state.fr_check_idx >= len(dt.get_tree(st.session_state.fr_active_tree)["checks"])
                should_stop = judged["stop"] or hit_cap or exhausted

                if should_stop:
                    active_tree = dt.get_tree(st.session_state.fr_active_tree)
                    transcript = [
                        {"check_label": h["check_label"], "question": h["question"], "answer": h["answer"],
                         "outcome": (h["branch_data"] or {}).get("outcome")}
                        for h in st.session_state.fr_history
                    ]
                    steps_in_active_tree = [h for h in st.session_state.fr_history
                                             if h["tree_id"] == st.session_state.fr_active_tree]
                    handoff = dt.resolve_handoff(st.session_state.fr_active_tree, steps_in_active_tree, hit_cap)
                    result = ai.draft_diagnosis(
                        active_tree["name"], transcript, active_tree.get("common_false_alarm"),
                        active_tree.get("grounding_note"), handoff,
                    )
                    if result is None:
                        # Groq unreachable mid-session — fall back to a plain,
                        # un-phrased rendering built straight from tree data
                        # rather than crash or lose the session's progress.
                        outcomes = [t["outcome"] for t in transcript if t["outcome"]]
                        result = {
                            "title": "Hypothesis unavailable — AI phrasing layer unreachable.",
                            "body": " ".join(outcomes) or "No specific outcome pattern matched; "
                                    "review the answers above directly.",
                            "pull_steps": ["Review each answered check above and verify it directly against "
                                           "your own dashboards."],
                            "handoff_line": (f"Consider {handoff['label']} as a next step."
                                              if handoff else "No suite handoff suggested for this pattern."),
                            "reply_draft": "Still looking into this — will confirm with the underlying data "
                                           "shortly.",
                        }
                    result["handoff"] = handoff
                    st.session_state.fr_result = result
                st.rerun()

    else:
        result = st.session_state.fr_result
        handoff = result.get("handoff")

        st.markdown("### Diagnosis")
        with st.container(border=True):
            style.badge("Hypothesis — verify before reporting up", "amber")
            st.markdown(f"**{result['title']}**")
            st.markdown(result["body"])

        with st.container(border=True):
            st.markdown("**What to actually pull**")
            for i, step in enumerate(result["pull_steps"], start=1):
                st.markdown(f"{i}. {step}")

        with st.container(border=True):
            if handoff:
                style.badge("Suite handoff" + (" (worth checking)" if handoff.get("soft") else ""), "teal")
                st.markdown(result["handoff_line"])
                if st.button(f"Go to {handoff['label']} →", type="primary"):
                    st.switch_page(handoff["page"])
            else:
                style.badge("Not a handoff case — yet", "muted")
                st.markdown(result["handoff_line"])

        with st.container(border=True):
            st.markdown("**Draft reply (buying time)**")
            st.code(result["reply_draft"], language=None)

        if st.button("Start a new diagnosis"):
            _reset()
            st.rerun()
