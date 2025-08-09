import requests
from .config import TEAMS_WEBHOOK_URL

def send_teams_message(title: str, message: str):
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": title,
        "themeColor": "0076D7",
        "title": title,
        "text": message
    }
    r = requests.post(TEAMS_WEBHOOK_URL, json=payload)
    r.raise_for_status()
