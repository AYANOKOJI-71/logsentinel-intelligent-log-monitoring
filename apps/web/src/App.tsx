import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "./api";
import { percent, stamp } from "./format";
import type { Alert, AlertStatus, Overview } from "./types";

const emptyOverview: Overview = {
  events_processed: 0,
  anomalies_detected: 0,
  open_alerts: 0,
  services: [],
  recent_events: [],
  alerts: [],
};

function statusLabel(status: AlertStatus): string {
  return status === "open" ? "Open" : status === "investigating" ? "Investigating" : "Resolved";
}

export default function App() {
  const [overview, setOverview] = useState<Overview>(emptyOverview);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const next = await api.overview();
      setOverview(next);
      setSelectedAlert((current) => next.alerts.find((alert) => alert.alert_id === current?.alert_id) ?? current);
    } catch {
      setError("The API is unavailable. Start the local FastAPI service on port 4300.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const selected = selectedAlert ?? overview.alerts[0] ?? null;
  const maxEvents = useMemo(() => Math.max(...overview.services.map((item) => item.events), 1), [overview.services]);

  const runIncident = async () => {
    setSeeding(true);
    try {
      await api.seedDemo();
      await refresh();
    } finally {
      setSeeding(false);
    }
  };

  const changeStatus = async (alert: Alert, status: AlertStatus) => {
    try {
      await api.updateAlert(alert.alert_id, status);
      await refresh();
    } catch {
      setError("Could not update the alert state. Try refreshing the workspace.");
    }
  };

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">LS</span><span>LogSentinel</span></div>
        <p className="workspace-label">OBSERVABILITY LAB</p>
        <nav aria-label="Workspace sections">
          <a className="nav-link active" href="#overview">Overview</a>
          <a className="nav-link" href="#stream">Log stream</a>
          <a className="nav-link" href="#incidents">Incidents <span>{overview.open_alerts}</span></a>
          <a className="nav-link" href="#baseline">Baselines</a>
        </nav>
        <div className="sidebar-foot"><span className="pulse" /> Local deterministic mode<br />No production data</div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div><p className="eyebrow">LIVE ANALYST WORKSPACE</p><h1>Incident command center</h1></div>
          <div className="top-actions"><span className="mode-chip">Synthetic telemetry only</span><button onClick={() => void runIncident()} disabled={seeding}>{seeding ? "Running scenario…" : "Run incident scenario"}</button></div>
        </header>

        {error && <div className="error-banner">{error}<button onClick={() => void refresh()}>Retry</button></div>}

        <section id="overview" className="metrics-grid" aria-label="Operations metrics">
          <Metric label="Logs processed" value={overview.events_processed.toLocaleString()} note="Current investigation window" tone="blue" />
          <Metric label="Anomalies found" value={overview.anomalies_detected.toLocaleString()} note="Explainable detector decisions" tone="orange" />
          <Metric label="Active alerts" value={overview.open_alerts.toLocaleString()} note="Open or investigating" tone="red" />
          <Metric label="Monitored services" value={overview.services.length.toLocaleString()} note="Adaptive service baselines" tone="mint" />
        </section>

        <section className="content-grid">
          <article id="incidents" className="panel alerts-panel">
            <div className="panel-title"><div><p className="eyebrow">TRIAGE QUEUE</p><h2>Incident alerts</h2></div><span>{overview.alerts.length} total</span></div>
            <div className="alert-list">
              {loading && <p className="empty">Loading investigation state…</p>}
              {!loading && overview.alerts.length === 0 && <p className="empty">Run the incident scenario to create a safe, synthetic payment-outage alert.</p>}
              {overview.alerts.map((alert) => (
                <button key={alert.alert_id} className={`alert-row ${selected?.alert_id === alert.alert_id ? "selected" : ""}`} onClick={() => setSelectedAlert(alert)}>
                  <span className={`severity-dot ${alert.severity}`} />
                  <span className="alert-main"><strong>{alert.summary}</strong><small>{alert.service} · {stamp(alert.created_at)}</small></span>
                  <span className={`status ${alert.status}`}>{statusLabel(alert.status)}</span>
                </button>
              ))}
            </div>
          </article>

          <article className="panel investigation-panel">
            <div className="panel-title"><div><p className="eyebrow">INVESTIGATION</p><h2>{selected ? "Anomaly explanation" : "Select an alert"}</h2></div>{selected && <span className="score">{percent(selected.anomaly_score)} confidence</span>}</div>
            {selected ? <>
              <div className="investigation-summary"><span className={`severity-pill ${selected.severity}`}>{selected.severity}</span><h3>{selected.summary}</h3><p>The detector raised this alert from a service-specific streaming baseline. Evidence is retained so an operator can assess the signal before changing systems.</p></div>
              <div className="explanation"><p className="explanation-title">Why this event was flagged</p>{selected.reasons.map((reason) => <p key={reason} className="reason"><span>↳</span>{reason}</p>)}</div>
              <div className="lifecycle"><span>Lifecycle</span>{(["open", "investigating", "resolved"] as AlertStatus[]).map((status) => <button key={status} className={selected.status === status ? "current" : ""} onClick={() => void changeStatus(selected, status)}>{statusLabel(status)}</button>)}</div>
            </> : <p className="empty">The detail pane will show the evidence and lifecycle controls for an alert.</p>}
          </article>
        </section>

        <section className="bottom-grid">
          <article id="stream" className="panel stream-panel">
            <div className="panel-title"><div><p className="eyebrow">EVENT STREAM</p><h2>Recent normalized logs</h2></div><button className="quiet" onClick={() => void refresh()}>Refresh</button></div>
            <div className="table-wrap"><table><thead><tr><th>Time</th><th>Service</th><th>Level</th><th>Message</th><th>Latency</th><th>Score</th></tr></thead><tbody>{overview.recent_events.map(({ event, decision }) => <tr key={event.event_id}><td>{stamp(event.timestamp)}</td><td>{event.service}</td><td><span className={`level ${event.level}`}>{event.level}</span></td><td>{event.message}</td><td>{Math.round(event.latency_ms)} ms</td><td><span className={decision.is_anomaly ? "score hot" : "score"}>{percent(decision.anomaly_score)}</span></td></tr>)}</tbody></table></div>
          </article>
          <article id="baseline" className="panel service-panel"><div className="panel-title"><div><p className="eyebrow">BASELINE COVERAGE</p><h2>Service activity</h2></div></div><div className="service-bars">{overview.services.map((service) => <div key={service.name}><div className="service-name"><span>{service.name}</span><strong>{service.events}</strong></div><div className="bar-track"><span style={{ width: `${(service.events / maxEvents) * 100}%` }} /></div></div>)}{overview.services.length === 0 && <p className="empty">No baseline has been established yet.</p>}</div></article>
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value, note, tone }: { label: string; value: string; note: string; tone: string }) {
  return <article className={`metric ${tone}`}><p>{label}</p><strong>{value}</strong><span>{note}</span></article>;
}
