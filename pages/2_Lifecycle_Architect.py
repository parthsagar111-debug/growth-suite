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

# ── Horizontal control strip ────────────────────────────────────────────
# Card look comes from a real st.container(border=True), not a blanket
# CSS rule on every columns() row (that used to also card chart pairs,
# button rows, etc. — see the note on stHorizontalBlock in style.py).
with st.container(border=True):
    sc1, sc2, sc3 = st.columns([1.3, 1, 1])
    with sc1:
        brand_id = style.brand_selector(label="Scope Memory Context")
    with sc2:
        category = st.selectbox("Category", ["D2C · Beauty & personal care", "D2C · Home", "D2C · Food & bev"])
    with sc3:
        discount_stance = st.selectbox("Discount stance", ["Discount-light (earn loyalty)", "Discount-heavy"])
    import_box = st.text_area(
        "Import diagnosis (optional)",
        value=imported["diagnosed_leak"] if imported else "",
        placeholder="Paste a Funnel Diagnostics result here, or send it directly from that tool.",
    )
    run = st.button("Generate journey →", type="primary", disabled=brand_id is None,
                     help="Select a brand first." if brand_id is None else None)

if run:
    with st.spinner("Computing trigger-day cadence, then writing + scoring copy with 6 AI agents…"):
        result_value = data.call_workflow(
            "lifecycle_architect",
            {"brand_id": brand_id, "category": category,
             "discount_stance": discount_stance, "diagnosis": import_box},
        )
    style.remember_result("lifecycle_result", result_value, brand_id)

style.stale_guard("lifecycle_result", brand_id)
result = st.session_state.get("lifecycle_result")
if result:
    stages = result["stages"]
    funnel = result["engagement_funnel"]
    avg_warmth = sum(s["tone_score"]["warmth"] for s in stages) / len(stages)
    convert_rate = (funnel[-1]["value"] / funnel[0]["value"] * 100) if funnel and funnel[0]["value"] else 0

    st.markdown("### Executive scorecard")
    style.kpi_row([
        {"label": "Journey stages", "value": str(len(stages))},
        {"label": "Expected engagement → convert", "value": f"{convert_rate:.1f}%"},
        {"label": "Average warmth score", "value": f"{avg_warmth:.2f}"},
    ])

    st.markdown("### Full analysis dashboard")
    # Tone curve and cadence-vs-benchmark dropped — secondary context that
    # doesn't change what to do next; the stage-by-stage cards below already
    # show each stage's tone score and trigger day inline.
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.journey_timeline(stages), use_container_width=True)
    with c2:
        st.plotly_chart(charts.engagement_funnel(funnel), use_container_width=True)

    style.agent_card("Narrative synthesis", f"**{result['narrative']['synthesis']}**")

    st.markdown("### Journey — stage by stage")
    for s in stages:
        with st.container(border=True):
            cc1, cc2 = st.columns([1, 5])
            with cc1:
                st.markdown(f'<div class="gs-step-day">Day<br>{s["day"]}</div>', unsafe_allow_html=True)
                st.caption(s["channel"])
            with cc2:
                st.markdown(f"**{s['name']}**")
                st.markdown(f'<div class="gs-stage-msg">{s["message"]}</div>', unsafe_allow_html=True)
                st.caption(f"Why here: {s['rationale']}")
                warmth, urgency = s["tone_score"]["warmth"], s["tone_score"]["urgency"]
                st.caption(f"Tone — warmth {warmth:.2f} · urgency {urgency:.2f}")
                if s["variants"]:
                    with st.expander("AI copy variants"):
                        for v in s["variants"]:
                            st.code(v, language=None)
                else:
                    style.status_pill("✓ No variants generated", "muted")

    style.next_action(
        "Turn the at-risk stage into a testable hypothesis before rolling it out broadly.",
        button_label="Send to Experiment Designer →",
        button_page="pages/3_Experiment_Designer.py",
        button_state=("imported_hypothesis",
                       f"Sending the day-{stages[2]['day']} \"{stages[2]['name']}\" WhatsApp nudge "
                       f"(no discount) will lift M2 repeat-purchase rate."),
        pdf_url=result.get("pdf_url"),
    )
else:
    style.empty_state("Fill in the brand input above and generate a journey to see the full dashboard.")
