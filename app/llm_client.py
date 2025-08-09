import requests
from .config import OLLAMA_URL, OLLAMA_MODEL

def analyze_alert(alert_text: str) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": f"Analyze this Grafana alert:\n{alert_text}"}
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
    response.raise_for_status()
    return response.json().get("response", "").strip()
