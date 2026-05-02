from langchain_google_genai import GoogleGenerativeAI
from config.settings import get_gemini, model

def get_llm():
    key = get_gemini()
    if not key:
        raise ValueError("Gemini API key not set.")
    return GoogleGenerativeAI(model=model, temperature=0.3, google_api_key=key)