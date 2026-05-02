import os
from dotenv import load_dotenv

load_dotenv()

url = "https://google.serper.dev/search"
model = "gemini-3-flash-preview"

def get_gemini():
    return os.environ.get("GOOGLE_API_KEY", "")

def get_serper():
    return os.environ.get("SERPER_API_KEY", "")
