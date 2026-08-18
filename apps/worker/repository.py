from __future__ import annotations

from collections import deque
from typing import Protocol

from apps.worker.models import AlertRecord, AlertStatus, AnomalyDecision, LogEvent


class InvestigationRepository(Protocol):
    def event_seen(self, event_id: str) -> bool: ...
    def save_event(self, event: LogEvent, decision: AnomalyDecision) -> None: ...
    def save_alert(self, alert: AlertRecord) -> None: ...
    def update_alert(self, alert_id: str, status: AlertStatus) -> AlertRecord | None: ...
    def alerts(self) -> list[AlertRecord]: ...
    def events(self) -> list[dict]: ...


class InMemoryInvestigationRepository:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._events: deque[dict] = deque(maxlen=250)
        self._alerts: dict[str, AlertRecord] = {}

    def event_seen(self, event_id: str) -> bool:
        return event_id in self._seen

    def save_event(self, event: LogEvent, decision: AnomalyDecision) -> None:
        self._seen.add(event.event_id)
        self._events.appendleft({"event": event, "decision": decision})

    def save_alert(self, alert: AlertRecord) -> None:
        self._alerts[alert.alert_id] = alert

    def update_alert(self, alert_id: str, status: AlertStatus) -> AlertRecord | None:
        alert = self._alerts.get(alert_id)
        if alert is None:
            return None
        updated = alert.model_copy(update={"status": status})
        self._alerts[alert_id] = updated
        return updated

    def alerts(self) -> list[AlertRecord]:
        return sorted(self._alerts.values(), key=lambda item: item.created_at, reverse=True)

    def events(self) -> list[dict]:
        return list(self._events)
