from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.worker.models import LogEvent, LogLevel


def deterministic_log_scenario() -> list[LogEvent]:
    """Synthetic incident path: baseline checkout logs then a correlated payment outage."""
    now = datetime.now(UTC)
    logs: list[LogEvent] = []
    for index, latency in enumerate([80, 91, 86, 88, 90]):
        logs.append(
            LogEvent(
                event_id=f"baseline-{index}",
                timestamp=now - timedelta(minutes=8 - index),
                service="checkout-api",
                level=LogLevel.INFO,
                message="checkout completed",
                latency_ms=latency,
                trace_id=f"trace-baseline-{index}",
            )
        )
    logs.extend(
        [
            LogEvent(
                event_id="payment-timeout-1",
                timestamp=now - timedelta(seconds=20),
                service="checkout-api",
                level=LogLevel.ERROR,
                message="payment gateway timeout",
                latency_ms=980,
                trace_id="trace-payment-1",
                attributes={"burst": "true", "dependency": "payments"},
            ),
            LogEvent(
                event_id="payment-timeout-2",
                timestamp=now - timedelta(seconds=12),
                service="checkout-api",
                level=LogLevel.ERROR,
                message="payment gateway timeout",
                latency_ms=1100,
                trace_id="trace-payment-2",
                attributes={"burst": "true", "dependency": "payments"},
            ),
            LogEvent(
                event_id="catalog-normal-1",
                timestamp=now - timedelta(seconds=5),
                service="catalog-api",
                level=LogLevel.INFO,
                message="catalog cache refresh",
                latency_ms=41,
                trace_id="trace-catalog-1",
            ),
        ]
    )
    return logs
