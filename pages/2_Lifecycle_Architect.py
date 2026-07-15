import streamlit as st
from lib import style, data, charts

style.inject()
if not data.is_live():
    st.markdown('<div class="gs-offline"><h2>This demo is currently offline</h2></div>', unsafe_allow_html=True)
    st.stop()
style.sidebar()

st.title("Lifecycle architect")
st.markdown('<p class="subtitle">Describe a brand to get a stage-by-stage WhatsApp journey, grounded in real diagnosis data when available.</p>', unsafe_allow_html=True)

imported = st.session_state.pop("imported_diagnosis", None)
if imported:
    style.flow_banner(f"Imported diagnosis: {imported['diagnosed_leak']}")

with st.container(border=True):
    st.markdown("### Brand input")
    c1, c2 = st.columns(2)
    with c1:
        category = st.selectbox("Category", ["D2C · Beauty & personal care", "D2C · Home", "D2C · Food & bev"])
    with c2:
        discount_stance = st.selectbox("Discount stance", ["Discount-light (earn loyalty)", "Discount-heavy"])
    import_box = st.text_area(
        "Import diagnosis (optional)",
        value=imported["diagnosed_leak"] if imported else "",
        placeholder="Paste a Funnel Diagnostics result here, or send it directly from that tool.",
    )
    run = st.button("Generate journey →", type="primary")

if run:
    with st.spinner("Computing trigger-day cadence, then writing + scoring copy with 6 AI agents…"):
        st.session_state["lifecycle_result"] = data.call_workflow(
            "lifecycle_architect",
            {"brand_id": st.session_state.get("brand_id"), "category": category,
             "discount_stance": discount_stance, "diagnosis": import_box},
        )

result = st.session_state.get("lifecycle_result")
if result:
    stages = result["stages"]

    st.markdown("### Full analysis dashboard")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.journey_timeline(stages), use_container_width=True)
        st.plotly_chart(charts.tone_curve(stages), use_container_width=True)
    with c2:
        st.plotly_chart(charts.engagement_funnel(result["engagement_funnel"]), use_container_width=True)
        st.plotly_chart(charts.cadence_benchmark(result["cadence_benchmark"]), use_container_width=True)

    style.agent_card("Narrative synthesis", f"**{result['narrative']['synthesis']}**")

    st.markdown("### Journey — stage by stage")
    for s in stages:
        with st.container(border=True):
            cc1, cc2 = st.columns([1, 5])
            with cc1:
                st.markdown(f"**Day {s['day']}**")
                st.caption(s["channel"])
            with cc2:
                st.markdown(f"**{s['name']}**")
                st.markdown(f'<div class="gs-stage-msg">{s["message"]}</div>', unsafe_allow_html=True)
                st.caption(f"Why here: {s['rationale']}")
                warmth, urgency = s["tone_score"]["warmth"], s["tone_score"]["urgency"]
                st.caption(f"Tone — warmth {warmth:.2f} · urgency {urgency:.2f}")
                with st.expander("AI copy variants"):
                    for v in s["variants"]:
                        st.markdown(f"- {v}")

    col_a, col_b = st.columns([3, 1])
    with col_a:
        style.flow_banner("Turn the at-risk stage into a testable hypothesis before rolling it out broadly.")
        if st.button("Send to Experiment Designer →"):
            st.session_state["imported_hypothesis"] = (
                f"Sending the day-{stages[2]['day']} \"{stages[2]['name']}\" WhatsApp nudge "
                f"(no discount) will lift M2 repeat-purchase rate."
            )
            st.switch_page("pages/3_Experiment_Designer.py")
    with col_b:
        style.export_pdf_button(result.get("pdf_url"))
else:
    style.empty_state("Fill in the brand input above and generate a journey to see the full dashboard.")
