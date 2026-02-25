from langchain_google_genai import GoogleGenerativeAI
from config.settings import GEMINI_API_KEY, model

# ------------------------------
# Gemini LLM
# ------------------------------

llm = GoogleGenerativeAI(model=model, temperature=0.3, api_key=GEMINI_API_KEY)