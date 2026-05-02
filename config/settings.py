import os
from dotenv import load_dotenv

load_dotenv()

url = "https://google.serper.dev/search"
model = "gemini-3-flash-preview"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
SERPER_API_KEY = os.getenv("SERPER_API_KEY") or ""