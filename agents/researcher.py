import requests
from config.settings import SERPER_API_KEY, url

def web_search(query: str):
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    results = []
    for item in data.get("organic", []):
        results.append(f"{item.get('title','')} - {item.get('link','')}")
    return results