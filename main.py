import os, re, json, datetime
import streamlit as st

# ─────────────────────────────────────────────
# 🔬 DEBUG PANEL — shows on every run
# ─────────────────────────────────────────────
def _dbg_header():
    with st.expander("🔬 **DEBUG PANEL** — Environment & Import Check", expanded=False):
        st.markdown("#### 🐍 Python & Runtime")
        import sys, platform
        st.code(
            f"Python     : {sys.version}\n"
            f"Platform   : {platform.platform()}\n"
            f"CWD        : {os.getcwd()}\n"
            f"__file__   : {os.path.abspath(__file__)}\n"
            f"PYTHONPATH : {os.environ.get('PYTHONPATH', '(not set)')}"
        )

        st.markdown("#### 📦 Critical Imports")
        _import_checks = [
            ("config.settings", ["model", "get_gemini", "get_serper"]),
            ("utils.build_pdf", ["build_pdf"]),
            ("agents.planner",  ["planner_task"]),
            ("agents.researcher", ["web_search"]),
            ("agents.aggregator", ["aggregate_results"]),
            ("agents.reporter",   ["report_task"]),
            ("agents.summarizer", ["summarize_task"]),
            ("database.read",     ["search_related_summaries"]),
            ("database.write",    ["write_summary"]),
            ("tabs.chat",  ["render"]),
            ("tabs.swot",  ["render"]),
            ("tabs.history", ["render"]),
        ]
        rows = []
        all_ok = True
        for mod, attrs in _import_checks:
            try:
                m = __import__(mod, fromlist=attrs)
                missing = [a for a in attrs if not hasattr(m, a)]
                if missing:
                    rows.append(f"⚠️  {mod:<35} imported BUT missing: {missing}")
                    all_ok = False
                else:
                    rows.append(f"✅  {mod:<35} OK  ({', '.join(attrs)})")
            except Exception as e:
                rows.append(f"❌  {mod:<35} FAILED → {e}")
                all_ok = False
        st.code("\n".join(rows))
        if not all_ok:
            st.error("🚨 One or more imports failed — analysis WILL break. Fix the ❌ lines above first.")

        st.markdown("#### 🗂️ File-system spot check")
        expected_paths = [
            "config/settings.py",
            "utils/build_pdf.py",
            "agents/planner.py",
            "agents/researcher.py",
            "agents/aggregator.py",
            "agents/reporter.py",
            "agents/summarizer.py",
            "database/read.py",
            "database/write.py",
            "tabs/chat.py",
            "tabs/swot.py",
            "tabs/history.py",
        ]
        fs_rows = []
        for p in expected_paths:
            exists = os.path.isfile(p)
            fs_rows.append(("✅" if exists else "❌") + f"  {p}")
        st.code("\n".join(fs_rows))

        st.markdown("#### 🌍 Env vars set in environment (names only)")
        sensitive = {"GOOGLE_API_KEY", "SERPER_API_KEY"}
        env_rows = []
        for k, v in sorted(os.environ.items()):
            if k in sensitive:
                env_rows.append(f"  {k} = {'[SET — ' + str(len(v)) + ' chars]' if v else '[EMPTY]'}")
            elif "key" in k.lower() or "secret" in k.lower() or "token" in k.lower():
                env_rows.append(f"  {k} = [REDACTED]")
            else:
                env_rows.append(f"  {k} = {v[:80]}")
        st.code("\n".join(env_rows) or "(none)")


def _dbg_step(label: str, *, error: Exception = None, detail: str = None):
    """Call at every major pipeline step."""
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if error:
        st.error(f"💥 **[{ts}] FAILED at: {label}**\n\n```\n{type(error).__name__}: {error}\n```")
        import traceback
        st.code(traceback.format_exc(), language="python")
    else:
        st.success(f"✅ **[{ts}]** {label}" + (f"  —  {detail}" if detail else ""))


# ─────────────────────────────────────────────
# App bootstrap
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Business Analyzer", page_icon="🚀", layout="centered")

# Show debug panel right under the page config, before anything else can crash
_dbg_header()

# ── safe import of config (may fail on cloud) ──────────────────────────────
try:
    from config.settings import model, get_gemini, get_serper
    _config_ok = True
except Exception as _cfg_err:
    st.error(
        f"🚨 **config.settings import failed** — nothing will work until this is fixed.\n\n"
        f"`{type(_cfg_err).__name__}: {_cfg_err}`"
    )
    _config_ok = False
    model, get_gemini, get_serper = "unknown", lambda: "", lambda: ""

try:
    from utils.build_pdf import build_pdf
    _pdf_ok = True
except Exception as _pdf_err:
    st.warning(f"⚠️ **utils.build_pdf import failed** — PDF download will be unavailable.\n\n`{_pdf_err}`")
    _pdf_ok = False
    build_pdf = None


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
    os.environ["GOOGLE_API_KEY"] = st.session_state.get("gemini_key", "")
    st.caption("[Get free key →](https://aistudio.google.com/app/apikey)")

    serper_key = st.text_input(
        "Serper API Key",
        type="password",
        placeholder="your-serper-key",
        value=st.session_state.get("serper_key", get_serper()),
    )
    st.session_state["serper_key"] = serper_key
    os.environ["SERPER_API_KEY"] = st.session_state.get("serper_key", "")
    st.caption("[Get free key →](https://serper.dev/)")

    keys_ready = bool(gemini_key and serper_key)

    # ── key sanity check ────────────────────────────────────────────────────
    if gemini_key:
        if not gemini_key.startswith("AIza"):
            st.warning("⚠️ Gemini key looks wrong — should start with `AIza`")
        elif len(gemini_key) < 30:
            st.warning("⚠️ Gemini key looks too short — double-check it")
        else:
            st.markdown("✅ Gemini key format OK")
    if serper_key and len(serper_key) < 10:
        st.warning("⚠️ Serper key looks suspiciously short")

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

# ─────────────────────────────────────────────
# TAB: REPORT
# ─────────────────────────────────────────────
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

            progress = st.container()
            with progress:
                status = st.status("Running analysis...", expanded=True)
                with status:
                    result = None
                    try:
                        # ── Step 1: imports ────────────────────────────────────────
                        st.write("📦 Importing agent modules...")
                        try:
                            from agents.planner import planner_task
                            from agents.researcher import web_search
                            from agents.aggregator import aggregate_results
                            from agents.reporter import report_task
                            from agents.summarizer import summarize_task
                            from database.read import search_related_summaries
                            from database.write import write_summary
                            _dbg_step("All agent modules imported")
                        except Exception as e:
                            _dbg_step("Agent module import", error=e)
                            raise

                        # ── Step 2: memory ─────────────────────────────────────────
                        st.write("🧠 Loading memory...")
                        try:
                            prev = search_related_summaries(goal) if use_memory else []
                            memory = "\n\n".join(prev) if prev else ""
                            _dbg_step("Memory loaded", detail=f"{len(prev)} previous summaries found")
                        except Exception as e:
                            _dbg_step("Memory load (search_related_summaries)", error=e)
                            raise

                        # ── Step 3: planner ────────────────────────────────────────
                        st.write("🧠 Planning search queries...")
                        try:
                            raw_queries = planner_task(goal)
                            queries = [q.strip() for q in raw_queries.split("\n") if q.strip()][:max_queries]
                            _dbg_step("Planner done", detail=f"{len(queries)} queries: {queries}")
                            if not queries:
                                st.warning("⚠️ Planner returned 0 queries — raw output was empty or unparseable.")
                        except Exception as e:
                            _dbg_step("planner_task()", error=e)
                            raise

                        # ── Step 4: web search ─────────────────────────────────────
                        st.write(f"🔍 Running {len(queries)} web searches...")
                        results = []
                        for i, q in enumerate(queries):
                            try:
                                r = web_search(q)
                                results.append(r)
                                _dbg_step(f"Search {i+1}/{len(queries)}", detail=f"`{q}` → {len(str(r))} chars returned")
                            except Exception as e:
                                _dbg_step(f"web_search() for query #{i+1}: `{q}`", error=e)
                                raise

                        # ── Step 5: aggregation ────────────────────────────────────
                        st.write("📊 Aggregating results...")
                        try:
                            aggregated = aggregate_results(results)
                            _dbg_step("Aggregation done", detail=f"{len(str(aggregated))} chars")
                        except Exception as e:
                            _dbg_step("aggregate_results()", error=e)
                            raise

                        # ── Step 6: report generation ──────────────────────────────
                        st.write("✍️ Generating report...")
                        try:
                            raw_report = report_task(goal=goal, research_data=aggregated, past_insights=memory)
                            _dbg_step("report_task() done", detail=f"{len(raw_report)} chars")
                            if not raw_report or len(raw_report) < 50:
                                st.warning(f"⚠️ Report looks suspiciously short ({len(raw_report)} chars). Raw output:\n\n```\n{raw_report}\n```")
                        except Exception as e:
                            _dbg_step("report_task()", error=e)
                            raise

                        # ── Step 7: chart parsing ──────────────────────────────────
                        chart_data = None
                        try:
                            chart_match = re.search(r"<chart>(.*?)</chart>", raw_report, re.DOTALL)
                            if chart_match:
                                chart_data = json.loads(chart_match.group(1).strip())
                                _dbg_step("Chart JSON parsed", detail=str(chart_data)[:200])
                            else:
                                _dbg_step("Chart block", detail="No <chart> tag found in report (this is OK)")
                        except Exception as e:
                            _dbg_step("Chart JSON parse", error=e)
                            # non-fatal — continue without chart
                            st.warning("⚠️ Chart data found but couldn't be parsed — continuing without chart.")
                        clean_report = re.sub(r"<chart>.*?</chart>", "", raw_report, flags=re.DOTALL).strip()

                        # ── Step 8: summarize & save ───────────────────────────────
                        st.write("💾 Saving to memory...")
                        try:
                            summary = summarize_task(clean_report)
                            _dbg_step("summarize_task() done", detail=f"{len(summary)} chars")
                        except Exception as e:
                            _dbg_step("summarize_task()", error=e)
                            raise

                        try:
                            write_summary(original_text=clean_report, summary=summary, model_name=model)
                            _dbg_step("write_summary() done")
                        except Exception as e:
                            _dbg_step("write_summary()", error=e)
                            raise

                        result = {
                            "queries": queries,
                            "aggregated": aggregated,
                            "report": clean_report,
                            "chart_data": chart_data,
                            "memory_used": bool(prev),
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        }
                        status.update(label="✅ Analysis complete", state="complete")

                    except Exception as e:
                        status.update(label="❌ Analysis failed", state="error")
                        # The individual _dbg_step already printed the traceback;
                        # this is the final catch-all summary.
                        st.error(
                            f"**Pipeline stopped with:** `{type(e).__name__}: {e}`\n\n"
                            "Scroll up in this panel to see exactly which step failed and the full traceback."
                        )

            st.session_state.report = result
            st.session_state.chart_data = result.get("chart_data") if result else None
            st.session_state.is_running = False

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

        cd = r.get("chart_data")
        if cd:
            st.subheader(cd.get("title", "Chart"))
            try:
                import pandas as pd
                if cd["type"] == "pie":
                    df = pd.DataFrame({"label": cd["labels"], "value": cd["values"]}).set_index("label")
                    st.bar_chart(df)
                else:
                    df = pd.DataFrame({"value": cd["values"]}, index=cd["labels"])
                    st.bar_chart(df)
            except Exception as e:
                st.warning(f"⚠️ Chart render failed: `{e}`")

        st.subheader("Strategic Report")
        st.markdown(r["report"])
        st.divider()

        slug     = g[:40].strip().lower().replace(" ", "-")
        filename = f"business-analysis_{slug}_{r['timestamp'].replace(' ','_').replace(':','-')}.pdf"
        if _pdf_ok and build_pdf:
            try:
                pdf_bytes = build_pdf(g, r, report_depth)
                st.download_button("⬇ Download Report (.pdf)", data=pdf_bytes,
                                   file_name=filename, mime="application/pdf",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"PDF generation failed: `{type(e).__name__}: {e}`")
        else:
            st.info("PDF download unavailable — `utils.build_pdf` failed to import (see debug panel above).")

# ─────────────────────────────────────────────
# TAB: CHAT
# ─────────────────────────────────────────────
with TAB_CHAT:
    if not st.session_state.report:
        st.info("Run an analysis first, then come back to chat about it.")
    else:
        try:
            from tabs import chat
            chat.render(st.session_state.report["report"])
        except Exception as e:
            import traceback
            st.error(f"💥 **tabs.chat crashed**\n\n`{type(e).__name__}: {e}`")
            st.code(traceback.format_exc(), language="python")

# ─────────────────────────────────────────────
# TAB: SWOT
# ─────────────────────────────────────────────
with TAB_SWOT:
    if not st.session_state.report:
        st.info("Run an analysis first to generate the SWOT board.")
    elif not keys_ready:
        st.warning("API keys required.")
    else:
        try:
            from tabs import swot
            swot.render(st.session_state.report["report"])
        except Exception as e:
            import traceback
            st.error(f"💥 **tabs.swot crashed**\n\n`{type(e).__name__}: {e}`")
            st.code(traceback.format_exc(), language="python")

# ─────────────────────────────────────────────
# TAB: HISTORY
# ─────────────────────────────────────────────
with TAB_HISTORY:
    try:
        from tabs import history
        history.render()
    except Exception as e:
        import traceback
        st.error(f"💥 **tabs.history crashed**\n\n`{type(e).__name__}: {e}`")
        st.code(traceback.format_exc(), language="python")

# import os, re, json, datetime
# import streamlit as st
# from config.settings import model, get_gemini, get_serper
# from utils.build_pdf import build_pdf


# st.set_page_config(page_title="AI Business Analyzer", page_icon="🚀", layout="centered")

# for k, v in [("report", None), ("is_running", False), ("last_goal", ""), ("chart_data", None)]:
#     if k not in st.session_state:
#         st.session_state[k] = v

# with st.sidebar:
#     st.title("Configuration")
#     st.subheader("API Keys")
#     gemini_key = st.text_input(
#         "Gemini API Key", 
#         type="password", 
#         placeholder="AIza...",
#         value=st.session_state.get("gemini_key", get_gemini()),
#         )
#     st.session_state["gemini_key"] = gemini_key
#     os.environ["GOOGLE_API_KEY"] = st.session_state.get("gemini_key", "")
#     st.caption("[Get free key →](https://aistudio.google.com/app/apikey)")
#     serper_key = st.text_input(
#         "Serper API Key", 
#         type="password", 
#         placeholder="your-serper-key",
#         value=st.session_state.get("serper_key", get_serper()),
#         )
#     st.session_state["serper_key"] = serper_key
#     os.environ["SERPER_API_KEY"] = st.session_state.get("serper_key", "")
#     st.caption("[Get free key →](https://serper.dev/)")

#     keys_ready = bool(gemini_key and serper_key)
#     st.markdown("✅ Keys configured" if keys_ready else "⚠️ Both keys required")

#     st.divider()
#     st.subheader("Settings")
#     report_depth = st.selectbox("Report Depth", ["Standard", "Detailed", "Executive Summary"])
#     max_queries  = st.slider("Max Search Queries", 1, 10, 5)
#     use_memory   = st.toggle("Use Memory", value=True)

# st.title("🚀 AI Business Analyzer")
# st.caption("Multi-agent strategic research · Gemini · Serper · Memory")
# st.divider()

# TAB_NAMES = ["📄 Report", "💬 Chat", "🧩 SWOT Board", "🕒 History"]
# tabs = st.tabs(TAB_NAMES)
# TAB_REPORT, TAB_CHAT, TAB_SWOT, TAB_HISTORY = tabs

# with TAB_REPORT:
#     goal = st.text_input(
#         "Business goal",
#         placeholder="e.g. Analyze competitive landscape of B2B SaaS invoicing tools in 2025",
#     )
#     if not keys_ready:
#         st.warning("Enter your API keys in the sidebar.")

#     col1, col2 = st.columns([3, 1])
#     with col1:
#         run_clicked = st.button(
#             "Run Analysis", type="primary", use_container_width=True,
#             disabled=not keys_ready or st.session_state.is_running,
#         )
#     with col2:
#         clear_clicked = st.button("Clear", use_container_width=True)

#     if clear_clicked:
#         st.session_state.report = None
#         st.session_state.chart_data = None
#         st.session_state.last_goal = ""
#         st.rerun()

#     if run_clicked:
#         if not goal.strip():
#             st.error("Please enter a business goal.")
#         else:
#             st.session_state.is_running = True
#             st.session_state.last_goal = goal

#             progress = st.container()
#             with progress:
#                 status = st.status("Running analysis...", expanded=True)
#                 with status:
#                     st.write("🧠 Planning search queries...")
#                     result = None
#                     try:
#                         from agents.planner import planner_task
#                         from agents.researcher import web_search
#                         from agents.aggregator import aggregate_results
#                         from agents.reporter import report_task
#                         from agents.summarizer import summarize_task
#                         from database.read import search_related_summaries
#                         from database.write import write_summary
#                         import os, re, json

#                         prev = search_related_summaries(goal) if use_memory else []
#                         memory = "\n\n".join(prev) if prev else ""

#                         queries = [q.strip() for q in planner_task(goal).split("\n") if q.strip()][:max_queries]

#                         st.write(f"🔍 Running {len(queries)} web searches...")
#                         results = [web_search(q) for q in queries]

#                         st.write("📊 Aggregating results...")
#                         aggregated = aggregate_results(results)

#                         st.write("✍️ Generating report...")
#                         raw_report = report_task(goal=goal, research_data=aggregated, past_insights=memory)

#                         chart_data = None
#                         chart_match = re.search(r"<chart>(.*?)</chart>", raw_report, re.DOTALL)
#                         if chart_match:
#                             try:
#                                 chart_data = json.loads(chart_match.group(1).strip())
#                             except Exception:
#                                 pass
#                         clean_report = re.sub(r"<chart>.*?</chart>", "", raw_report, flags=re.DOTALL).strip()

#                         st.write("💾 Saving to memory...")
#                         summary = summarize_task(clean_report)
#                         write_summary(original_text=clean_report, summary=summary, model_name=model)

#                         result = {
#                             "queries": queries,
#                             "aggregated": aggregated,
#                             "report": clean_report,
#                             "chart_data": chart_data,
#                             "memory_used": bool(prev),
#                             "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
#                         }
#                         status.update(label="✅ Analysis complete", state="complete")

#                     except Exception as e:
#                         status.update(label="❌ Analysis failed", state="error")
#                         st.error(str(e))

#             st.session_state.report = result
#             st.session_state.chart_data = result.get("chart_data") if result else None
#             st.session_state.is_running = False

#     if st.session_state.report:
#         r = st.session_state.report
#         g = st.session_state.last_goal

#         st.divider()
#         c1, c2, c3 = st.columns(3)
#         c1.metric("Queries Run",  len(r["queries"]))
#         c2.metric("Memory",       "On" if r["memory_used"] else "Off")
#         c3.metric("Generated",    r["timestamp"])
#         st.divider()

#         with st.expander("Search Queries"):
#             for i, q in enumerate(r["queries"], 1):
#                 st.write(f"{i}. {q}")

#         # Chart
#         cd = r.get("chart_data")
#         if cd:
#             st.subheader(cd.get("title", "Chart"))
#             if cd["type"] == "pie":
#                 import pandas as pd
#                 df = pd.DataFrame({"label": cd["labels"], "value": cd["values"]}).set_index("label")
#                 st.bar_chart(df)          # Streamlit has no native pie; bar is clean
#             else:
#                 import pandas as pd
#                 df = pd.DataFrame({"value": cd["values"]}, index=cd["labels"])
#                 st.bar_chart(df)

#         st.subheader("Strategic Report")
#         st.markdown(r["report"])
#         st.divider()

#         # Download PDF
#         slug     = g[:40].strip().lower().replace(" ", "-")
#         filename = f"business-analysis_{slug}_{r['timestamp'].replace(' ','_').replace(':','-')}.pdf"
#         try:
#             pdf_bytes = build_pdf(g, r, report_depth)
#             st.download_button("⬇ Download Report (.pdf)", data=pdf_bytes,
#                                file_name=filename, mime="application/pdf",
#                                use_container_width=True)
#         except Exception as e:
#             st.error(f"PDF generation failed: {e}.")

# with TAB_CHAT:
#     if not st.session_state.report:
#         st.info("Run an analysis first, then come back to chat about it.")
#     else:
#         from tabs import chat
#         chat.render(st.session_state.report["report"])

# with TAB_SWOT:
#     if not st.session_state.report:
#         st.info("Run an analysis first to generate the SWOT board.")
#     elif not keys_ready:
#         st.warning("API keys required.")
#     else:
#         from tabs import swot
#         swot.render(st.session_state.report["report"])

# with TAB_HISTORY:
#     from tabs import history
#     history.render()