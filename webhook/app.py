import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment variables (set via .env locally, GitHub Actions in CI, K8s secrets in prod)
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://grafana:3000")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")

if not GRAFANA_API_KEY or not TEAMS_WEBHOOK_URL:
    # In non-production flows you may want to allow missing values for testing
    raise ValueError("Missing required environment variables: GRAFANA_API_KEY and/or TEAMS_WEBHOOK_URL")

def analyze_with_ollama(prompt_text: str) -> str:
    """
    Example payload for Ollama-like API. Adjust model & payload to your Ollama installation.
    If Ollama is local CLI-only, replace with subprocess call to `ollama run ...`.
    """
    try:
        payload = {
            "model": "gemma-3b",    # change as needed
            "prompt": prompt_text,
            "stream": False
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # adapt extraction depending on your Ollama API response shape
        return data.get("response") or data.get("text") or json.dumps(data)
    except Exception as e:
        app.logger.exception("Ollama analysis failed")
        return f"Error analyzing alert: {e}"

def create_grafana_annotation(start_time_ms: int, end_time_ms: int | None, text: str, tags=None):
    headers = {"Authorization": f"{GRAFANA_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "text": text,
        "time": start_time_ms,
        "tags": tags or ["alert-analysis"]
    }
    if end_time_ms:
        payload["timeEnd"] = end_time_ms

    r = requests.post(f"{GRAFANA_URL}/api/annotations", json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def send_to_teams(text: str):
    payload = {"text": text}
    r = requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=10)
    r.raise_for_status()
    return r.text

def iso_to_ms(ts: str) -> int:
    # Expecting ISO timestamp like "2025-08-09T07:00:00Z"
    from datetime import datetime, timezone
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ts)
        return int(dt.timestamp() * 1000)
    except Exception:
        return int.__call__(0)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Invalid payload"}), 400

    # Grafana Alertmanager-ish payload handling
    alert = (payload.get("alerts") or [None])[0] or payload
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    status = alert.get("status", payload.get("status", "firing"))
    startsAt = alert.get("startsAt", payload.get("startsAt"))
    endsAt = alert.get("endsAt", None)

    start_ms = iso_to_ms(startsAt) if startsAt else None
    end_ms = iso_to_ms(endsAt) if endsAt else None

    summary = annotations.get("summary") or labels.get("alertname") or "Grafana Alert"
    body_text = f"Status: {status}\nLabels: {json.dumps(labels)}\nAnnotations: {json.dumps(annotations)}\nFull payload:\n{json.dumps(payload, indent=2)}"

    # Analyze with Ollama
    try:
        analysis = analyze_with_ollama(body_text)
    except Exception as e:
        analysis = f"Error calling analysis: {e}"

    # Post annotation to Grafana (non-blocking best-effort)
    try:
        ann_text = f"Alert: {summary}\n\nAnalysis:\n{analysis}"
        if start_ms:
            create_grafana_annotation(start_ms, end_ms, ann_text, tags=["alert-analysis", status])
    except Exception:
        app.logger.exception("Failed to post Grafana annotation")

    # Send to Teams
    try:
        teams_text = f"**{summary}**\n\nStatus: {status}\n\nAnalysis:\n{analysis}"
        send_to_teams(teams_text)
    except Exception:
        app.logger.exception("Failed to send to Teams")

    return jsonify({"status": "processed", "analysis": analysis}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))

