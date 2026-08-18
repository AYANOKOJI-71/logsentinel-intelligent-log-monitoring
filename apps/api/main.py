from __future__ import annotations

from collections import Counter
from os import getenv

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from apps.worker.anomaly import AdaptiveAnomalyDetector
from apps.worker.models import AlertStatus, LogEvent
from apps.worker.opensearch import OpenSearchInvestigationRepository
from apps.worker.processor import LogProcessor
from apps.worker.repository import InMemoryInvestigationRepository
from apps.worker.scenarios import deterministic_log_scenario


def build_repository():
    if getenv("LOGWATCH_STORAGE_MODE", "memory") == "opensearch":
        return OpenSearchInvestigationRepository()
    return InMemoryInvestigationRepository()


repository = build_repository()
processor = LogProcessor(repository, AdaptiveAnomalyDetector())
app = FastAPI(title="LogSentinel API", version="1.0.0")


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "deterministic-local"}


@app.post("/api/logs")
def ingest_log(event: LogEvent) -> dict:
    return processor.process(event)


@app.get("/api/logs")
def list_logs() -> list[dict]:
    return [
        {
            "event": item["event"].model_dump(mode="json"),
            "decision": item["decision"].model_dump(mode="json"),
        }
        for item in repository.events()
    ]


@app.post("/api/demo/seed")
def seed_demo() -> dict:
    results = [processor.process(event) for event in deterministic_log_scenario()]
    return {
        "processed": len(results),
        "new": sum(item["accepted"] for item in results),
        "results": results,
    }


@app.get("/api/overview")
def overview() -> dict:
    events = repository.events()
    alerts = repository.alerts()
    services = Counter(item["event"].service for item in events)
    anomalies = [item for item in events if item["decision"].is_anomaly]
    return {
        "events_processed": len(events),
        "anomalies_detected": len(anomalies),
        "open_alerts": sum(alert.status != AlertStatus.RESOLVED for alert in alerts),
        "services": [{"name": name, "events": count} for name, count in services.most_common()],
        "recent_events": events[:12],
        "alerts": alerts,
    }


@app.get("/api/alerts")
def list_alerts() -> list:
    return repository.alerts()


@app.patch("/api/alerts/{alert_id}")
def update_alert(alert_id: str, change: AlertStatusUpdate) -> dict:
    alert = repository.update_alert(alert_id, change.status)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert.model_dump(mode="json")


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
