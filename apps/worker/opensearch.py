from __future__ import annotations

from datetime import UTC, datetime
from os import getenv

from apps.worker.models import AlertRecord, AlertStatus, AnomalyDecision, LogEvent


class OpenSearchInvestigationRepository:
    """OpenSearch-backed repository used only when LOGWATCH_STORAGE_MODE=opensearch.

    The in-memory repository remains the default for a deterministic, zero-service demo.
    """

    def __init__(self) -> None:
        try:
            from opensearchpy import OpenSearch
        except ImportError as exc:  # pragma: no cover - exercised in the Compose image
            raise RuntimeError("Install logsentinel[search] for OpenSearch mode") from exc

        endpoint = getenv("LOGWATCH_OPENSEARCH_URL", "http://opensearch:9200")
        self.client = OpenSearch(hosts=[endpoint])
        self.logs_index = "logsentinel-logs-v1"
        self.alerts_index = "logsentinel-alerts-v1"
        self._ensure_indices()

    def _ensure_indices(self) -> None:
        mappings = {
            "properties": {
                "event_id": {"type": "keyword"},
                "service": {"type": "keyword"},
                "timestamp": {"type": "date"},
                "is_anomaly": {"type": "boolean"},
                "anomaly_score": {"type": "float"},
            }
        }
        for index in (self.logs_index, self.alerts_index):
            if not self.client.indices.exists(index=index):
                self.client.indices.create(index=index, body={"mappings": mappings})

    def event_seen(self, event_id: str) -> bool:
        return self.client.exists(index=self.logs_index, id=event_id)

    def save_event(self, event: LogEvent, decision: AnomalyDecision) -> None:
        self.client.index(
            index=self.logs_index,
            id=event.event_id,
            body={
                "event_id": event.event_id,
                "service": event.service,
                "timestamp": event.timestamp.isoformat(),
                "is_anomaly": decision.is_anomaly,
                "anomaly_score": decision.anomaly_score,
                "event": event.model_dump(mode="json"),
                "decision": decision.model_dump(mode="json"),
            },
            refresh="wait_for",
        )

    def save_alert(self, alert: AlertRecord) -> None:
        self.client.index(
            index=self.alerts_index,
            id=alert.alert_id,
            body=alert.model_dump(mode="json"),
            refresh="wait_for",
        )

    def update_alert(self, alert_id: str, status: AlertStatus) -> AlertRecord | None:
        if not self.client.exists(index=self.alerts_index, id=alert_id):
            return None
        self.client.update(
            index=self.alerts_index,
            id=alert_id,
            body={"doc": {"status": status.value, "updated_at": datetime.now(UTC).isoformat()}},
            refresh="wait_for",
        )
        refreshed = self.client.get(index=self.alerts_index, id=alert_id)
        return AlertRecord.model_validate(refreshed["_source"])

    def alerts(self) -> list[AlertRecord]:
        result = self.client.search(
            index=self.alerts_index,
            body={
                "size": 100,
                "sort": [{"created_at": {"order": "desc"}}],
                "query": {"match_all": {}},
            },
        )
        return [AlertRecord.model_validate(item["_source"]) for item in result["hits"]["hits"]]

    def events(self) -> list[dict]:
        result = self.client.search(
            index=self.logs_index,
            body={
                "size": 250,
                "sort": [{"timestamp": {"order": "desc"}}],
                "query": {"match_all": {}},
            },
        )
        return [
            {
                "event": LogEvent.model_validate(item["_source"]["event"]),
                "decision": AnomalyDecision.model_validate(item["_source"]["decision"]),
            }
            for item in result["hits"]["hits"]
        ]
