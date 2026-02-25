from agents.planner import planner_task
from agents.researcher import web_search
from agents.aggregator import aggregate_results
from agents.reporter import report_task
from agents.summarizer import summarize_task
from database.read import search_related_summaries
from database.write import write_summary
from config.settings import model, GEMINI_API_KEY, SERPER_API_KEY

import streamlit as st


# =====================================================
# Page Config
# =====================================================
st.set_page_config(
    page_title="AI Business Analyzer",
    page_icon="🚀",
    layout="centered",
)

st.title("🚀 AI Business Analyzer")
st.caption("AI-powered strategic research engine with memory")


# =====================================================
# Sidebar — Configuration
# =====================================================
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("🔑 API Keys")

    gemini_key = st.text_input(
        "Gemini API Key",
        value=GEMINI_API_KEY or "",
        type="password",
        placeholder="AIza...",
        help="Get your key at https://ai.google.dev/"
    )

    serper_key = st.text_input(
        "Serper.dev API Key",
        value=SERPER_API_KEY or "",
        type="password",
        placeholder="your-serper-key",
        help="Get your key at https://serper.dev/"
    )

    keys_ready = bool(gemini_key and serper_key)

    if keys_ready:
        st.success("✅ API keys set")
    else:
        st.warning("⚠️ Both API keys are required to run analysis.")

    st.divider()

    st.subheader("🛠️ Settings")

    report_depth = st.selectbox(
        "Report Depth",
        options=["Standard", "Detailed", "Executive Summary"],
        help="Controls how comprehensive the generated report will be."
    )

    max_queries = st.slider(
        "Max Search Queries",
        min_value=1,
        max_value=10,
        value=5,
        help="Number of search queries the researcher will run."
    )

    use_memory = st.toggle("🧠 Use Memory", value=True, help="Include past related analyses in the report context.")

    st.divider()
    st.caption("AI Business Analyzer · Built with Streamlit & Gemini")


# =====================================================
# Session State Control
# =====================================================
if "report" not in st.session_state:
    st.session_state.report = None

if "is_running" not in st.session_state:
    st.session_state.is_running = False


# =====================================================
# Agent Execution
# =====================================================
def run_agent(goal):

    # 🔎 Memory Retrieval
    previous_summaries = search_related_summaries(goal) if use_memory else []
    context_memory = "\n\n".join(previous_summaries) if previous_summaries else ""

    # Planner
    queries = planner_task(goal).split("\n")
    queries = queries[:max_queries]  # Respect sidebar setting
    search_results = []
    aggregated = None

    # Web Search
    for q in queries:
        if q.strip():
            search_results.append(web_search(q.strip()))

    # Aggregation
    if search_results:
        aggregated = aggregate_results(search_results)

    # Report Generation
    if aggregated:
        report = report_task(goal=goal, research_data=aggregated, past_insights=context_memory)

        # Store summary
        summary = summarize_task(report)
        write_summary(
            original_text=report,
            summary=summary,
            model_name=model
        )

        return {
            "queries": queries,
            "aggregated": aggregated,
            "report": report,
            "memory_used": bool(previous_summaries)
        }

    return None


# =====================================================
# UI Layout
# =====================================================
with st.container():
    goal = st.text_input("🎯 Enter your business goal")

    col1, col2 = st.columns([1, 1])

    with col1:
        run_button = st.button(
            "Run Analysis",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.is_running or not keys_ready
        )

    with col2:
        clear_button = st.button(
            "Clear",
            use_container_width=True
        )

# Clear results
if clear_button:
    st.session_state.report = None
    st.rerun()


# =====================================================
# Controlled Execution
# =====================================================
if run_button and goal and not st.session_state.is_running:
    st.session_state.is_running = True

    with st.spinner("Running AI analysis..."):
        if not gemini_key or not serper_key:
            st.error("⚠️ API keys are missing. Configure them in Streamlit Secrets or enter them in the sidebar.")
            st.stop()  # Prevent further execution
        result = run_agent(goal)
        st.session_state.report = result

    st.session_state.is_running = False
    st.rerun()


# =====================================================
# Display Results
# =====================================================
if st.session_state.report:

    result = st.session_state.report

    st.divider()

    if result["memory_used"]:
        st.success("🧠 Previous related insights were used.")

    with st.expander("🔍 Generated Search Queries", expanded=False):
        for q in result["queries"]:
            st.write("-", q)

    with st.expander("📊 Aggregated Results", expanded=False):
        st.write(result["aggregated"])

    st.divider()
    st.subheader("📄 Final Strategic Report")
    st.markdown(result["report"])