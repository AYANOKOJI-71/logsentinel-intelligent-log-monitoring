from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from math import sqrt

from apps.worker.models import AnomalyDecision, LogEvent, LogLevel


@dataclass
class ServiceBaseline:
    count: int = 0
    mean_latency: float = 0.0
    m2_latency: float = 0.0
    error_count: int = 0
    known_messages: set[str] = field(default_factory=set)

    def standard_deviation(self) -> float:
        if self.count < 2:
            return 0.0
        return sqrt(self.m2_latency / (self.count - 1))

    def observe(self, event: LogEvent) -> None:
        self.count += 1
        delta = event.latency_ms - self.mean_latency
        self.mean_latency += delta / self.count
        self.m2_latency += delta * (event.latency_ms - self.mean_latency)
        self.error_count += int(event.level == LogLevel.ERROR)
        self.known_messages.add(event.message.lower().strip())


class AdaptiveAnomalyDetector:
    """Explainable online baseline detector for streaming log events.

    It retains per-service running moments and error ratios. This model avoids opaque
    automatic remediation: every score is accompanied by human-readable evidence.
    """

    def __init__(self, min_baseline_samples: int = 3, anomaly_threshold: float = 0.67):
        self._baselines: dict[str, ServiceBaseline] = defaultdict(ServiceBaseline)
        self.min_baseline_samples = min_baseline_samples
        self.anomaly_threshold = anomaly_threshold

    def score(self, event: LogEvent) -> AnomalyDecision:
        baseline = self._baselines[event.service]
        reasons: list[str] = []
        score = 0.0
        message = event.message.lower().strip()

        if baseline.count >= self.min_baseline_samples:
            deviation = baseline.standard_deviation()
            if deviation > 0:
                z_score = abs(event.latency_ms - baseline.mean_latency) / deviation
                if z_score >= 3:
                    score += 0.55
                    reasons.append(f"latency is {z_score:.1f}σ from the {event.service} baseline")
                elif z_score >= 2:
                    score += 0.3
                    reasons.append(f"latency is {z_score:.1f}σ above the service baseline")

            historical_error_rate = baseline.error_count / baseline.count
            if event.level == LogLevel.ERROR and historical_error_rate < 0.25:
                score += 0.45
                reasons.append("error level is unusual for this service baseline")
            if event.level == LogLevel.ERROR and message not in baseline.known_messages:
                score += 0.2
                reasons.append("error signature has not appeared in the current baseline")
        elif event.level == LogLevel.ERROR:
            score += 0.5
            reasons.append("error observed while baseline is still warming")

        if event.attributes.get("burst") == "true":
            score += 0.2
            reasons.append("event is part of a correlated error burst")

        score = min(round(score, 3), 1.0)
        decision = AnomalyDecision(
            event_id=event.event_id,
            service=event.service,
            anomaly_score=score,
            is_anomaly=score >= self.anomaly_threshold,
            reasons=reasons or ["within the current adaptive baseline"],
            baseline_samples=baseline.count,
        )
        baseline.observe(event)
        return decision
