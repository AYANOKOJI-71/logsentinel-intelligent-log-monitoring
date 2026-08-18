# LogSentinel demonstration guide

The reviewer can begin in deterministic local mode, which requires neither Kafka nor OpenSearch. The objective is to demonstrate signal triage rather than imitate production traffic.

| Step | Action | What to narrate |
|---|---|---|
| 1 | Open the React workspace. | “This is an analyst-facing investigation queue, not a passive log viewer.” |
| 2 | Select **Run incident scenario**. | “The system receives a known-safe incident sequence and builds a checkout-service baseline.” |
| 3 | Open the critical alert. | “The explanation lists latency deviation, unusual error rate, unseen error signature, and burst correlation.” |
| 4 | Change the lifecycle to **Investigating**. | “An analyst owns the alert state; the detector does not automatically alter production systems.” |
| 5 | View the event stream and metric cards. | “The score is connected to source logs and operational counters.” |

The full Docker lab adds Kafka, OpenSearch, Prometheus, and Grafana. In that path, use the built-in producer module to publish the same deterministic scenario to `application.logs.v1`; the worker reads the raw topic and emits high-scoring decisions to `application.anomalies.v1`.
