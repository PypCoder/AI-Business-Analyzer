import streamlit as st
from google import genai
from google.genai import types

client = genai.Client()

def convert_history(messages):
    gemini_history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
        )
    return gemini_history

def render(report: str):
    st.caption("Ask follow-up questions about the report.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for m in st.session_state.chat_messages:
        st.chat_message(m["role"]).write(m["content"])

    if prompt := st.chat_input("Ask anything about the report..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        system = f"You are a business analyst. Answer questions using ONLY the report below.\n\n---\n{report}\n---"

        with st.chat_message("assistant"):
            with st.spinner(""):
                resp = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    config=types.GenerateContentConfig(
                        system_instruction=system
                    ),
                    contents=convert_history(st.session_state.chat_messages),
                )
                reply = resp.text
                st.write(reply)

        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

    if st.session_state.chat_messages:
        if st.button("Clear chat", type="secondary"):
            st.session_state.chat_messages = []
            st.rerun()