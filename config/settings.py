import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = st.secrets.get("SERPER_API_KEY") or os.getenv("SERPER_API_KEY")
url = "https://google.serper.dev/search"
model = "gemini-2.5-flash"