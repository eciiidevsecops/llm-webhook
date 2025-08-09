import os

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://grafana.monitoring.svc.cluster.local:3000")
GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2")
