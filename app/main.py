from fastapi import FastAPI, Request
from .llm_client import analyze_alert
from .grafana_client import post_annotation
from .teams_client import send_teams_message

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    alert_text = data.get("message", "No message")
    dashboard_id = data.get("dashboardId", 1)
    panel_id = data.get("panelId", 1)

    # Send to LLM
    analysis = analyze_alert(alert_text)

    # Send annotation to Grafana
    post_annotation(dashboard_id, panel_id, analysis)

    # Send to Teams
    send_teams_message("Grafana Alert Analysis", analysis)

    return {"status": "ok", "analysis": analysis}
