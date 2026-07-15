import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Results & learnings")
st.markdown('<p class="subtitle">Grade a shipped experiment against the decision rule it committed to, and keep a running log of what was learned.</p>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### Grade an outcome")
    st.caption("This step is deliberately not AI — the verdict is computed by comparing your actual "
               "numbers against the thresholds already agreed to in Experiment Designer.")
    c1, c2, c3 = st.columns(3)
    with c1:
        lift = st.number_input("Actual M2 lift (pp)", value=3.4, step=0.1)
    with c2:
        optout = st.number_input("Opt-out delta (pp)", value=0.3, step=0.1)
    with c3:
        support = st.number_input("Support ticket delta", value=0, step=1)
    grade = st.button("Grade this experiment →", type="primary")

if grade:
    if optout >= 1.5:
        verdict, color = "KILL", "coral"
    elif lift >= 3.0:
        verdict, color = "SHIP", "teal"
    else:
        verdict, color = "EXTEND", "amber"
    st.session_state["latest_verdict"] = (verdict, color, lift, optout)

if "latest_verdict" in st.session_state:
    verdict, color, lift, optout = st.session_state["latest_verdict"]
    with st.container(border=True):
        style.badge(verdict, color)
        st.markdown(f"Graded deterministically: lift {lift}pp, opt-out delta {optout}pp against the "
                     "committed decision rule — no model involved in this call.")
        style.agent_card("Takeaway writer", "The code-free at-risk nudge cleared the bar with opt-out "
                          "well within tolerance — confirms the M2 cliff was retention-driven, not purely "
                          "price-driven. Worth extending the same no-discount pattern to the lapsed-stage message.")

st.markdown("### Full analysis dashboard")
result = data.call_workflow("results_learnings", {"brand_id": st.session_state.get("brand_id")})
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(charts.win_rate_over_time(result["history"]), use_container_width=True)
    st.plotly_chart(charts.cumulative_impact(result["cumulative_impact_pp"]), use_container_width=True)
with c2:
    st.plotly_chart(charts.verdict_distribution(result["verdict_distribution"]), use_container_width=True)
    st.plotly_chart(charts.theme_cluster(result["themes"]), use_container_width=True)

style.agent_card("Pattern recognition", result["narrative"]["pattern_recognition"])

col_a, col_b = st.columns([3, 1])
with col_b:
    style.export_pdf_button(result.get("pdf_url"))

st.markdown("### Learnings log")
for h in result["history"]:
    with st.container(border=True):
        color = {"SHIP": "teal", "KILL": "coral", "EXTEND": "amber"}.get(h["verdict"], "accent")
        style.badge(h["verdict"], color)
        st.caption(f"{h['date']} · {h['brand']} · lift {h['lift_pp']}pp")
