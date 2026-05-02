import streamlit as st

def render():
    from database.read import get_all_summaries

    st.caption("Past analyses stored in memory.")

    try:
        rows = get_all_summaries()
    except Exception as e:
        st.error(f"Could not load history: {e}")
        return

    if not rows:
        st.info("No analyses yet. Run one from the Report tab.")
        return

    for row in reversed(rows):
        label = f"{row.get('timestamp', 'Unknown date')} — {row.get('summary', '')[:60]}..."
        with st.expander(label):
            st.markdown(f"**Model:** `{row.get('model_name', '—')}`")
            st.divider()
            st.markdown(row.get("original_text", ""))