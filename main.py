import os, re, json, datetime
import streamlit as st
from config.settings import model, get_gemini, get_serper, set_gemini, set_serper
from utils.build_pdf import build_pdf


st.set_page_config(page_title="AI Business Analyzer", page_icon="🚀", layout="centered")

for k, v in [("report", None), ("is_running", False), ("last_goal", ""), ("chart_data", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

with st.sidebar:
    st.title("Configuration")
    st.subheader("API Keys")
    gemini_key = st.text_input(
        "Gemini API Key", 
        type="password", 
        placeholder="AIza...",
        value=st.session_state.get("gemini_key", get_gemini()),
        )
    st.session_state["gemini_key"] = gemini_key
    set_gemini(gemini_key)
    st.caption("[Get free key →](https://aistudio.google.com/app/apikey)")
    serper_key = st.text_input(
        "Serper API Key", 
        type="password", 
        placeholder="your-serper-key",
        value=st.session_state.get("serper_key", get_serper()),
        )
    st.session_state["serper_key"] = serper_key
    set_serper(serper_key)
    st.caption("[Get free key →](https://serper.dev/)")

    keys_ready = bool(gemini_key and serper_key)
    st.markdown("✅ Keys configured" if keys_ready else "⚠️ Both keys required")

    st.divider()
    st.subheader("Settings")
    report_depth = st.selectbox("Report Depth", ["Standard", "Detailed", "Executive Summary"])
    max_queries  = st.slider("Max Search Queries", 1, 10, 5)
    use_memory   = st.toggle("Use Memory", value=True)

st.title("🚀 AI Business Analyzer")
st.caption("Multi-agent strategic research · Gemini · Serper · Memory")
st.divider()

TAB_NAMES = ["📄 Report", "💬 Chat", "🧩 SWOT Board", "🕒 History"]
tabs = st.tabs(TAB_NAMES)
TAB_REPORT, TAB_CHAT, TAB_SWOT, TAB_HISTORY = tabs
# To add a new tab: append to TAB_NAMES, unpack one more variable above, render inside it below.

def run_agent(goal: str) -> dict | None:
    from agents.planner    import planner_task
    from agents.researcher import web_search
    from agents.aggregator import aggregate_results
    from agents.reporter   import report_task
    from agents.summarizer import summarize_task
    from database.read     import search_related_summaries
    from database.write    import write_summary

    prev = search_related_summaries(goal) if use_memory else []
    memory = "\n\n".join(prev) if prev else ""

    queries = [q.strip() for q in planner_task(goal).split("\n") if q.strip()][:max_queries]
    results = [web_search(q) for q in queries]
    if not results:
        return None

    aggregated = aggregate_results(results)
    if not aggregated:
        return None

    raw_report = report_task(goal=goal, research_data=aggregated, past_insights=memory)

    # Split chart data out of report text
    chart_data = None
    chart_match = re.search(r"<chart>(.*?)</chart>", raw_report, re.DOTALL)
    if chart_match:
        try:
            chart_data = json.loads(chart_match.group(1).strip())
        except Exception:
            pass
    clean_report = re.sub(r"<chart>.*?</chart>", "", raw_report, flags=re.DOTALL).strip()

    summary = summarize_task(clean_report)
    write_summary(original_text=clean_report, summary=summary, model_name=model)

    return {
        "queries":      queries,
        "aggregated":   aggregated,
        "report":       clean_report,
        "chart_data":   chart_data,
        "memory_used":  bool(prev),
        "timestamp":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

with TAB_REPORT:
    goal = st.text_input(
        "Business goal",
        placeholder="e.g. Analyze competitive landscape of B2B SaaS invoicing tools in 2025",
    )
    if not keys_ready:
        st.warning("Enter your API keys in the sidebar.")

    col1, col2 = st.columns([3, 1])
    with col1:
        run_clicked = st.button(
            "Run Analysis", type="primary", use_container_width=True,
            disabled=not keys_ready or st.session_state.is_running,
        )
    with col2:
        clear_clicked = st.button("Clear", use_container_width=True)

    if clear_clicked:
        st.session_state.report = None
        st.session_state.chart_data = None
        st.session_state.last_goal = ""
        st.rerun()

    if run_clicked:
        if not goal.strip():
            st.error("Please enter a business goal.")
        else:
            st.session_state.is_running = True
            st.session_state.last_goal = goal
            with st.spinner("Running analysis..."):
                result = run_agent(goal)
                st.session_state.report = result
                st.session_state.chart_data = result.get("chart_data") if result else None
            st.session_state.is_running = False
            st.rerun()

    if st.session_state.report:
        r = st.session_state.report
        g = st.session_state.last_goal

        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Queries Run",  len(r["queries"]))
        c2.metric("Memory",       "On" if r["memory_used"] else "Off")
        c3.metric("Generated",    r["timestamp"])
        st.divider()

        with st.expander("Search Queries"):
            for i, q in enumerate(r["queries"], 1):
                st.write(f"{i}. {q}")

        # Chart
        cd = r.get("chart_data")
        if cd:
            st.subheader(cd.get("title", "Chart"))
            if cd["type"] == "pie":
                import pandas as pd
                df = pd.DataFrame({"label": cd["labels"], "value": cd["values"]}).set_index("label")
                st.bar_chart(df)          # Streamlit has no native pie; bar is clean
            else:
                import pandas as pd
                df = pd.DataFrame({"value": cd["values"]}, index=cd["labels"])
                st.bar_chart(df)

        st.subheader("Strategic Report")
        st.markdown(r["report"])
        st.divider()

        # Download PDF
        slug     = g[:40].strip().lower().replace(" ", "-")
        filename = f"business-analysis_{slug}_{r['timestamp'].replace(' ','_').replace(':','-')}.pdf"
        try:
            pdf_bytes = build_pdf(g, r, report_depth)
            st.download_button("⬇ Download Report (.pdf)", data=pdf_bytes,
                               file_name=filename, mime="application/pdf",
                               use_container_width=True)
        except Exception as e:
            st.error(f"PDF generation failed: {e}.")

with TAB_CHAT:
    if not st.session_state.report:
        st.info("Run an analysis first, then come back to chat about it.")
    else:
        from tabs import chat
        chat.render(st.session_state.report["report"])

with TAB_SWOT:
    if not st.session_state.report:
        st.info("Run an analysis first to generate the SWOT board.")
    elif not keys_ready:
        st.warning("API keys required.")
    else:
        from tabs import swot
        swot.render(st.session_state.report["report"])

with TAB_HISTORY:
    from tabs import history
    history.render()