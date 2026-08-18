from __future__ import annotations

import json
import os

from apps.worker.scenarios import deterministic_log_scenario


def publish_demo() -> int:
    """Publish the safe synthetic scenario to Kafka's raw-log topic for lab demos."""
    try:
        from confluent_kafka import Producer
    except ImportError as exc:  # pragma: no cover - Compose runtime responsibility
        raise RuntimeError("Install logsentinel[streaming] to publish through Kafka") from exc

    bootstrap = os.getenv("LOGWATCH_KAFKA_BOOTSTRAP", "localhost:9092")
    producer = Producer({"bootstrap.servers": bootstrap})
    topic = os.getenv("LOGWATCH_LOG_TOPIC", "application.logs.v1")
    events = deterministic_log_scenario()
    for event in events:
        producer.produce(topic, key=event.service, value=json.dumps(event.model_dump(mode="json")))
    producer.flush(10)
    return len(events)


if __name__ == "__main__":
    print(f"Published {publish_demo()} synthetic log events.")
