from fastapi.testclient import TestClient

from apps.api.main import app, processor, repository
from apps.worker.models import LogEvent, LogLevel

client = TestClient(app)


def reset_state() -> None:
    repository._seen.clear()
    repository._events.clear()
    repository._alerts.clear()
    processor.detector._baselines.clear()


def test_seed_detects_synthetic_incident() -> None:
    reset_state()
    response = client.post("/api/demo/seed")
    assert response.status_code == 200
    overview = client.get("/api/overview").json()
    assert overview["events_processed"] == 8
    assert overview["anomalies_detected"] >= 1
    assert overview["open_alerts"] >= 1


def test_duplicate_event_is_idempotent() -> None:
    reset_state()
    event = LogEvent(
        event_id="same-event",
        service="api",
        level=LogLevel.INFO,
        message="ok",
        latency_ms=10,
    )
    first = client.post("/api/logs", json=event.model_dump(mode="json"))
    second = client.post("/api/logs", json=event.model_dump(mode="json"))
    assert first.json()["accepted"] is True
    assert second.json()["duplicate"] is True


def test_alert_can_move_to_investigating() -> None:
    reset_state()
    client.post("/api/demo/seed")
    alert = client.get("/api/alerts").json()[0]
    changed = client.patch(f"/api/alerts/{alert['alert_id']}", json={"status": "investigating"})
    assert changed.status_code == 200
    assert changed.json()["status"] == "investigating"


def test_metrics_expose_processor_counters() -> None:
    reset_state()
    client.post("/api/demo/seed")
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "logsentinel_logs_processed_total" in metrics.text
