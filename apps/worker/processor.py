from __future__ import annotations

from prometheus_client import Counter, Histogram

from apps.worker.anomaly import AdaptiveAnomalyDetector
from apps.worker.models import AlertRecord, LogEvent
from apps.worker.repository import InvestigationRepository

PROCESSED_LOGS = Counter("logsentinel_logs_processed_total", "Log events evaluated", ["service"])
ANOMALIES = Counter("logsentinel_anomalies_total", "Anomalies detected", ["service", "severity"])
PROCESSING_LATENCY = Histogram("logsentinel_processing_seconds", "Log processing latency")


class LogProcessor:
    def __init__(self, repository: InvestigationRepository, detector: AdaptiveAnomalyDetector):
        self.repository = repository
        self.detector = detector

    @PROCESSING_LATENCY.time()
    def process(self, event: LogEvent) -> dict:
        if self.repository.event_seen(event.event_id):
            return {"accepted": False, "duplicate": True, "event_id": event.event_id}

        decision = self.detector.score(event)
        self.repository.save_event(event, decision)
        PROCESSED_LOGS.labels(service=event.service).inc()
        alert = None
        if decision.is_anomaly:
            severity = "critical" if decision.anomaly_score >= 0.85 else "high"
            alert = AlertRecord(
                event_id=event.event_id,
                service=event.service,
                severity=severity,
                anomaly_score=decision.anomaly_score,
                summary=f"{event.service}: anomalous {event.level.value} log event",
                reasons=decision.reasons,
            )
            self.repository.save_alert(alert)
            ANOMALIES.labels(service=event.service, severity=severity).inc()
        return {
            "accepted": True,
            "duplicate": False,
            "event": event,
            "decision": decision,
            "alert": alert,
        }
