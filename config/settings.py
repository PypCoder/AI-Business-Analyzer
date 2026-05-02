import os
from dotenv import load_dotenv

load_dotenv()

url = "https://google.serper.dev/search"
model = "gemini-3-flash-preview"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
SERPER_API_KEY = os.getenv("SERPER_API_KEY") or ""

def get_gemini():
    return GEMINI_API_KEY

def get_serper():
    return SERPER_API_KEY

def set_gemini(key: str):
    global GEMINI_API_KEY
    GEMINI_API_KEY = key

def set_serper(key: str):
    global SERPER_API_KEY
    SERPER_API_KEY = key