from apps.worker.anomaly import AdaptiveAnomalyDetector
from apps.worker.kafka import run_kafka_consumer
from apps.worker.opensearch import OpenSearchInvestigationRepository
from apps.worker.processor import LogProcessor

if __name__ == "__main__":
    repository = OpenSearchInvestigationRepository()
    run_kafka_consumer(LogProcessor(repository, AdaptiveAnomalyDetector()))
