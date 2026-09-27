import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { postJson } from "../api";
import { BeaconPanel } from "../components/BeaconPanel";
import { ComplianceBanner } from "../components/ComplianceBanner";
import { IncidentPanel } from "../components/IncidentPanel";
import { MineMap } from "../components/MineMap";
import { ReplayBar } from "../components/ReplayBar";
import { TelemetryPanel } from "../components/TelemetryPanel";
import { Card, MetricCard, Pill, SectionHeading } from "../components/ui";
import { SCENARIOS } from "../types";
import type { IncidentView } from "../types";
import { useAlertSiren } from "../useAlertSiren";
import { useSimulation } from "../useSimulation";

const CONNECTION_COPY: Record<string, { text: string; dot: string; textClass: string }> = {
  live: { text: "● LIVE SYSTEM ACTIVE", dot: "bg-emerald-500", textClass: "text-emerald-700" },
  connecting: { text: "● CONNECTING…", dot: "bg-slate-400", textClass: "text-slate-500" },
  reconnecting: { text: "● RECONNECTING…", dot: "bg-amber-500", textClass: "text-amber-700" },
  disconnected: { text: "● DISCONNECTED — showing last snapshot", dot: "bg-red-500", textClass: "text-red-700" },
};

export function ControlRoom() {
  const { snapshot, map, connection, commandError, runCommand } = useSimulation();
  const [selectedId, setSelectedId] = useState("D01");
  const [replayIncident, setReplayIncident] = useState<IncidentView | null>(null);
  const live = connection === "live";
  const disconnected = connection === "disconnected" || connection === "reconnecting";
  const vehicle = useMemo(
    () => snapshot?.vehicles.find((item) => item.vehicle_id === selectedId) ?? snapshot?.vehicles[0] ?? null,
    [snapshot, selectedId],
  );

  const blindCurveSegmentIds = useMemo(() => {
    const ids = new Set<string>();
    snapshot?.road_segments.forEach((segment) => {
      if (segment.is_blind_curve) ids.add(segment.segment_id);
    });
    return ids;
  }, [snapshot]);

  const anyVehicleApproachingBlindCurve = useMemo(
    () => (snapshot?.vehicles ?? []).some((item) => blindCurveSegmentIds.has(item.current_road_segment_id)),
    [snapshot, blindCurveSegmentIds],
  );
  const anyVehicleBraking = useMemo(
    () => (snapshot?.vehicles ?? []).some((item) => item.safety.simulated_brake_active),
    [snapshot],
  );
  const siren = useAlertSiren({ blindCurveApproach: anyVehicleApproachingBlindCurve, brakeActive: anyVehicleBraking });

  const safetyScore = useMemo(() => {
    if (!snapshot) return null;
    const warning = snapshot.kpis.severity_counts.WARNING ?? 0;
    const critical = snapshot.kpis.severity_counts.CRITICAL ?? 0;
    const penalty = snapshot.kpis.active_incident_count * 4 + warning * 3 + critical * 10 + snapshot.kpis.simulated_braking_count * 5;
    return Math.max(0, Math.min(100, 100 - penalty));
  }, [snapshot]);

  const connectionCopy = CONNECTION_COPY[connection] ?? CONNECTION_COPY.connecting;

  return (
    <div className="min-h-screen bg-white">
      <ComplianceBanner />
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-slate-900">Third Eye: Safe Mining Operations Dashboard</h1>
            <p className="text-sm text-slate-500">Fog-Shield digital twin · software-only simulation</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`flex items-center gap-1.5 rounded-full bg-slate-50 px-3 py-1.5 text-sm font-bold ${connectionCopy.textClass}`}>
              {connectionCopy.text}
            </span>
            <button
              className="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              onClick={siren.toggle}
            >
              {siren.enabled ? "🔔 Alerts on" : "🔕 Enable audio alerts"}
            </button>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-600">
              Demo scenarios
              <select
                className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm font-semibold text-slate-900"
                disabled={disconnected}
                value={snapshot?.scenario ?? "NORMAL"}
                onChange={(event) => void runCommand(() => postJson("/api/simulation/scenario", { scenario: event.target.value }))}
              >
                {SCENARIOS.map((item) => (
                  <option key={item} value={item}>
                    {item.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex gap-1.5">
              <button
                className="rounded-full bg-signal-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-signal-700 disabled:opacity-40"
                disabled={disconnected}
                onClick={() => void runCommand(() => postJson("/api/simulation/start"))}
              >
                Start
              </button>
              <button
                className="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                disabled={disconnected}
                onClick={() => void runCommand(() => postJson("/api/simulation/pause"))}
              >
                Pause
              </button>
              <button
                className="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                disabled={disconnected}
                onClick={() => void runCommand(() => postJson("/api/simulation/reset"))}
              >
                Reset
              </button>
            </div>
          </div>
        </div>
        {commandError ? <p className="mt-2 text-sm font-semibold text-red-600">Command failed: {commandError}</p> : null}
      </header>

      <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-4">
        <div className="flex flex-col gap-4 lg:col-span-1">
          <div className="grid grid-cols-2 gap-3">
            <MetricCard label="Trucks online" value={snapshot?.kpis.fleet_size ?? "—"} />
            <MetricCard label="Active warnings" value={snapshot?.kpis.active_incident_count ?? "—"} />
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
            <div className="text-xs font-semibold text-emerald-700">Shift safety score</div>
            <div className="tabular mt-1 text-4xl font-extrabold text-emerald-600">
              {safetyScore !== null ? `${safetyScore.toFixed(1)}%` : "—"}
            </div>
            <div className="mt-1 text-xs text-emerald-700/70">
              Live rollup from active incidents &amp; simulated braking events — not a backend field.
            </div>
          </div>

          <Card>
            <SectionHeading>Activity feed</SectionHeading>
            {(snapshot?.incidents_recent.length ?? 0) === 0 ? (
              <p className="text-sm text-slate-400">No safety events yet this shift.</p>
            ) : (
              <ul className="flex flex-col gap-3">
                {[...(snapshot?.incidents_recent ?? [])]
                  .sort((a, b) => b.timestamp_seconds - a.timestamp_seconds)
                  .slice(0, 6)
                  .map((incident) => (
                    <li key={incident.incident_id} className="text-sm">
                      <span className="tabular font-semibold text-slate-900">t={incident.timestamp_seconds.toFixed(0)}s</span>{" "}
                      <span className="text-slate-600">
                        {incident.vehicle_id} — {incident.message}
                      </span>
                    </li>
                  ))}
              </ul>
            )}
          </Card>
        </div>

        <div className="flex flex-col gap-3 lg:col-span-3">
          <SectionHeading
            action={
              vehicle ? (
                <Link className="text-sm font-semibold text-signal-600 hover:text-signal-700" to={`/hud/${vehicle.vehicle_id}`}>
                  Open driver HUD →
                </Link>
              ) : null
            }
          >
            Live haul road safety map
          </SectionHeading>
          <div className="flex flex-wrap gap-2">
            {(snapshot?.vehicles ?? []).map((item) => (
              <button
                key={item.vehicle_id}
                onClick={() => setSelectedId(item.vehicle_id)}
                className={`rounded-full px-3 py-1 text-xs font-bold ring-1 ${
                  item.vehicle_id === selectedId
                    ? "bg-signal-600 text-white ring-signal-600"
                    : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {item.vehicle_id}
              </button>
            ))}
          </div>
          <div className="h-[480px]">
            <MineMap
              map={map}
              vehicles={snapshot?.vehicles ?? []}
              beacons={snapshot?.beacons ?? []}
              selectedId={selectedId}
              onSelect={setSelectedId}
              live={live}
            />
          </div>
        </div>
      </div>

      {disconnected ? (
        <div className="mx-6 mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm font-semibold text-red-700">
          Backend disconnected. Last snapshot is frozen — no local telemetry is generated while offline.
        </div>
      ) : null}

      <div className="flex flex-col gap-6 px-6 pb-6">
        <TelemetryPanel vehicle={vehicle} />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <IncidentPanel incidents={snapshot?.incidents_recent ?? []} disabled={disconnected} onCommand={runCommand} />
          <BeaconPanel beacons={snapshot?.beacons ?? []} disabled={disconnected} onCommand={runCommand} />
        </div>
      </div>

      <footer className="border-t border-slate-200 bg-slate-50 px-6 py-4">
        <ReplayBar incidents={snapshot?.incidents_recent ?? []} onSelectIncident={setReplayIncident} />
        {replayIncident ? (
          <div className="mt-3 rounded-lg border border-slate-200 bg-white p-3">
            <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-slate-500">
              <Pill tone="neutral">{replayIncident.hazard_type.replace(/_/g, " ")}</Pill>
              <span>Stored telemetry context at t={replayIncident.timestamp_seconds.toFixed(1)}s</span>
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
              {replayIncident.telemetry_context.map(([name, value]) => (
                <div key={name} className="rounded-md border border-slate-100 px-2 py-1">
                  <div className="truncate text-[10px] font-medium capitalize text-slate-400">{name.replace(/_/g, " ")}</div>
                  <div className="tabular text-xs font-bold text-slate-800">{String(value)}</div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </footer>
    </div>
  );
}
