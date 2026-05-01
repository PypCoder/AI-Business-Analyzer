from langchain_google_genai import GoogleGenerativeAI
from config.settings import GEMINI_API_KEY, model

# ------------------------------
# Gemini LLM
# ------------------------------
if not GEMINI_API_KEY:
    ll=None
    raise ValueError("GEMINI_API_KEY is not set. Please set it in Streamlit Secrets or as an environment variable.")
else:
    llm = GoogleGenerativeAI(model=model, temperature=0.3, google_api_key=GEMINI_API_KEY)