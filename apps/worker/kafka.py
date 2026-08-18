from __future__ import annotations

import json
import os

from apps.worker.models import LogEvent
from apps.worker.processor import LogProcessor


def run_kafka_consumer(processor: LogProcessor) -> None:
    """Run only in container mode; local deterministic mode never needs a broker."""
    try:
        from confluent_kafka import Consumer, Producer
    except ImportError as exc:  # pragma: no cover - dependency is container-only
        raise RuntimeError("Install logsentinel[streaming] to run the Kafka consumer") from exc

    consumer = Consumer(
        {
            "bootstrap.servers": os.getenv("LOGWATCH_KAFKA_BOOTSTRAP", "kafka:9092"),
            "group.id": "logsentinel-detector-v1",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([os.getenv("LOGWATCH_LOG_TOPIC", "application.logs.v1")])
    producer = Producer({"bootstrap.servers": os.getenv("LOGWATCH_KAFKA_BOOTSTRAP", "kafka:9092")})
    anomaly_topic = os.getenv("LOGWATCH_ANOMALY_TOPIC", "application.anomalies.v1")
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                continue
            event = LogEvent.model_validate(json.loads(message.value()))
            result = processor.process(event)
            if result["accepted"] and result["decision"].is_anomaly:
                producer.produce(
                    anomaly_topic,
                    key=event.service,
                    value=json.dumps(
                        {
                            "event": event.model_dump(mode="json"),
                            "decision": result["decision"].model_dump(mode="json"),
                            "alert": result["alert"].model_dump(mode="json"),
                        }
                    ),
                )
                producer.flush(2)
            consumer.commit(message=message, asynchronous=False)
    finally:
        consumer.close()
