from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class AlertStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class LogEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    service: str
    environment: str = "demo"
    level: LogLevel
    message: str
    latency_ms: float = Field(ge=0)
    trace_id: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class AnomalyDecision(BaseModel):
    event_id: str
    service: str
    anomaly_score: float = Field(ge=0, le=1)
    is_anomaly: bool
    reasons: list[str]
    baseline_samples: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AlertRecord(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str
    service: str
    severity: str
    status: AlertStatus = AlertStatus.OPEN
    anomaly_score: float
    summary: str
    reasons: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
