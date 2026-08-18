export type AlertStatus = "open" | "investigating" | "resolved";

export interface Decision {
  anomaly_score: number;
  is_anomaly: boolean;
  reasons: string[];
  baseline_samples: number;
}

export interface LogEvent {
  event_id: string;
  timestamp: string;
  service: string;
  level: "debug" | "info" | "warn" | "error";
  message: string;
  latency_ms: number;
  trace_id?: string;
  attributes: Record<string, string>;
}

export interface Alert {
  alert_id: string;
  event_id: string;
  service: string;
  severity: "high" | "critical";
  status: AlertStatus;
  anomaly_score: number;
  summary: string;
  reasons: string[];
  created_at: string;
}

export interface Overview {
  events_processed: number;
  anomalies_detected: number;
  open_alerts: number;
  services: Array<{ name: string; events: number }>;
  recent_events: Array<{ event: LogEvent; decision: Decision }>;
  alerts: Alert[];
}
