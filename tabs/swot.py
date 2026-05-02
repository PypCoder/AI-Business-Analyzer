import streamlit as st
import json, os, re
from langchain_core.prompts import ChatPromptTemplate
from core.llm import llm

swot_prompt = ChatPromptTemplate.from_template(
"""Extract a SWOT analysis from the report below.
Return ONLY valid JSON, no markdown, no explanation:
{{"strengths":["..."],"weaknesses":["..."],"opportunities":["..."],"threats":["..."]}}

Report:
{report}"""
)

llm = swot_prompt | llm
def _parse_swot(report: str) -> dict:

    raw = llm.invoke({
        "report": report,
    })
    clean = re.sub(r"```json|```", "", raw).strip()
    return json.loads(clean)


def render(report: str):
    st.caption("Auto-generated SWOT from the report.")

    if "swot_data" not in st.session_state:
        st.session_state.swot_data = None

    if st.button("Generate SWOT", type="primary"):
        with st.spinner("Extracting SWOT..."):
            try:
                st.session_state.swot_data = _parse_swot(report)
            except Exception as e:
                st.error(f"Failed to parse SWOT: {e}")
                return

    data = st.session_state.swot_data
    if not data:
        return

    CELLS = [
        ("strengths",     "💪 Strengths",     "#0a2a1a", "#166534", "#4ade80"),
        ("weaknesses",    "⚠️ Weaknesses",    "#2a1a0a", "#92400e", "#fbbf24"),
        ("opportunities", "🚀 Opportunities", "#0a1a2a", "#1e3a5f", "#60a5fa"),
        ("threats",       "🔴 Threats",       "#2a0a0a", "#7f1d1d", "#f87171"),
    ]

    top_left, top_right = st.columns(2)
    bot_left, bot_right = st.columns(2)
    containers = [top_left, top_right, bot_left, bot_right]

    for (key, label, bg, border, text_color), col in zip(CELLS, containers):
        items = data.get(key, [])
        with col:
            st.markdown(
                f"""<div style="background:{bg};border:1px solid {border};border-radius:6px;padding:1rem;min-height:160px">
                <div style="color:{text_color};font-weight:700;margin-bottom:0.5rem">{label}</div>
                {"".join(f'<div style="color:#c8d6e5;font-size:0.82rem;margin-bottom:0.4rem">• {i}</div>' for i in items)}
                </div>""",
                unsafe_allow_html=True,
            )