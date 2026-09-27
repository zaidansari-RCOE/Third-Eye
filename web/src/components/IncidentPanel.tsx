import { postJson } from "../api";
import type { IncidentView } from "../types";
import { Card, Pill, SectionHeading, SeverityPill } from "./ui";

type Props = {
  incidents: IncidentView[];
  disabled: boolean;
  onCommand: (action: () => Promise<unknown>) => Promise<void>;
};

export function IncidentPanel({ incidents, disabled, onCommand }: Props) {
  return (
    <Card>
      <SectionHeading>Incidents</SectionHeading>
      {incidents.length === 0 ? (
        <p className="text-sm text-slate-400">No incidents in memory. The fleet is operating normally.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {incidents.map((incident) => (
            <article key={incident.incident_id} className="rounded-lg border border-slate-200 p-3">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-sm font-bold text-slate-900">{incident.title}</span>
                <SeverityPill severity={incident.severity} />
              </div>
              <div className="text-xs text-slate-500">
                {incident.vehicle_id} · {incident.hazard_type.replace(/_/g, " ")} · {incident.status}
              </div>
              <p className="mt-1.5 text-sm text-slate-600">{incident.message}</p>
              <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span className="tabular">t={incident.timestamp_seconds.toFixed(1)}s</span>
                <span>rule: {incident.triggering_rule}</span>
                {incident.simulated_brake_active ? <Pill tone="red">Simulated brake</Pill> : null}
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                  disabled={disabled || incident.status !== "open"}
                  onClick={() => void onCommand(() => postJson(`/api/incidents/${incident.incident_id}/acknowledge`))}
                >
                  Acknowledge
                </button>
                <button
                  className="rounded-full bg-signal-600 px-3 py-1 text-xs font-semibold text-white hover:bg-signal-700 disabled:opacity-40"
                  disabled={disabled || incident.status === "resolved"}
                  onClick={() => void onCommand(() => postJson(`/api/incidents/${incident.incident_id}/resolve`))}
                >
                  Resolve
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}
