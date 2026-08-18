# LogSentinel security notes

LogSentinel is intentionally packaged as a portfolio lab. The default local mode stores its short-lived investigation state only in memory, and the supplied scenario contains fictional telemetry. No real operational logs, identity data, secrets, or payment information belong in the repository or the demo flow.

| Boundary | Lab control | Production follow-up |
|---|---|---|
| Log content | Synthetic messages only; explicit data-boundary documentation | Redact tokens, headers, identifiers, and sensitive payloads before event publication. |
| Ingestion | Stable event IDs prevent duplicate detector processing | Add authenticated producers, schema validation, quotas, and encrypted Kafka listeners. |
| Investigation state | Local in-memory fallback or local OpenSearch lab | Enforce least privilege, retention controls, backups, encryption, and network segmentation. |
| Alert actions | Human lifecycle changes only | Add audited authorization and integration-specific approvals. |
| Dashboards | Local Grafana development credentials | Use secret-managed strong credentials and SSO. |

The OpenSearch security plugin is disabled in `compose.yaml` solely to lower setup friction for a single-machine evaluation. That configuration must never be exposed outside an isolated local environment.
