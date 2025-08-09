import requests
from .config import GRAFANA_URL, GRAFANA_API_KEY

def post_annotation(dashboard_id: int, panel_id: int, text: str):
    url = f"{GRAFANA_URL}/api/annotations"
    headers = {"Authorization": f"Bearer {GRAFANA_API_KEY}"}
    payload = {
        "dashboardId": dashboard_id,
        "panelId": panel_id,
        "time": int(__import__("time").time() * 1000),
        "text": text
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
