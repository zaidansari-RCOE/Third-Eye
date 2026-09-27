import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { ComplianceBanner } from "../components/ComplianceBanner";
import { ThermalUpscalingCanvas } from "../components/ThermalUpscalingCanvas";
import { Card, MetricCard, Pill } from "../components/ui";
import { useAlertSiren } from "../useAlertSiren";
import { useSimulation } from "../useSimulation";

const ZONE_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  green: { bg: "bg-emerald-500", text: "text-white", label: "Normal operation" },
  yellow: { bg: "bg-amber-500", text: "text-white", label: "Approaching blind curve / advisory" },
  red: { bg: "bg-red-500", text: "text-white", label: "Emergency brake triggered" },
};

export function DriverHud() {
  const { vehicleId = "D01" } = useParams();
  const { snapshot, connection, commandError } = useSimulation();
  const vehicle = snapshot?.vehicles.find((item) => item.vehicle_id === vehicleId) ?? snapshot?.vehicles[0];
  const zone = vehicle?.safety.safety_zone ?? "green";
  const zoneStyle = ZONE_STYLE[zone] ?? ZONE_STYLE.green;
  const telemetry = vehicle?.telemetry;

  const isBlindCurve = useMemo(() => {
    if (!vehicle) return false;
    const segment = snapshot?.road_segments.find((item) => item.segment_id === vehicle.current_road_segment_id);
    return Boolean(segment?.is_blind_curve);
  }, [snapshot, vehicle]);

  const siren = useAlertSiren({
    blindCurveApproach: isBlindCurve,
    brakeActive: Boolean(vehicle?.safety.simulated_brake_active),
  });

  return (
    <div className="min-h-screen bg-white">
      <ComplianceBanner />
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-6 py-4">
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-slate-900">Driver HUD · {vehicle?.vehicle_id ?? vehicleId}</h1>
          <p className="text-sm text-slate-500">Origin: simulated digital twin</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-slate-50 px-3 py-1.5 text-sm font-bold text-slate-600">{connection.toUpperCase()}</span>
          <button
            className="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            onClick={siren.toggle}
          >
            {siren.enabled ? "🔔 Alerts on" : "🔕 Enable audio alerts"}
          </button>
          <Link className="rounded-full bg-signal-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-signal-700" to="/">
            Control room
          </Link>
        </div>
      </header>

      {commandError ? <p className="px-6 pt-3 text-sm font-semibold text-red-600">Command failed: {commandError}</p> : null}
      {connection !== "live" ? (
        <p className="px-6 pt-3 text-sm font-semibold text-red-600">Link degraded. Display is frozen on the last backend snapshot.</p>
      ) : null}

      <div className="p-6">
        <div className={`flex items-center justify-between rounded-xl px-5 py-4 ${zoneStyle.bg} ${zoneStyle.text}`}>
          <span className="text-lg font-extrabold uppercase tracking-tight">{zone}</span>
          <span className="text-sm font-semibold opacity-90">{zoneStyle.label}</span>
        </div>

        {vehicle?.safety.simulated_brake_active ? (
          <div className="mt-4 rounded-xl bg-red-600 px-5 py-4 text-center text-lg font-extrabold text-white animate-pulse-dot">
            SIMULATED BRAKE ACTIVE
          </div>
        ) : null}

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MetricCard label="Speed" value={telemetry ? `${Number(telemetry.vehicle_velocity_kph).toFixed(1)}` : "—"} sub="kph" />
          <MetricCard label="Advisory speed" value={telemetry ? `${Number(telemetry.curve_speed_limit_kph).toFixed(0)}` : "—"} sub="kph" />
          <MetricCard label="Forward LiDAR" value={telemetry ? String(telemetry.forward_lidar_cm) : "—"} sub="cm" />
          <MetricCard label="Fog density" value={telemetry ? String(telemetry.visual_fog_density_pct) : "—"} sub="%" />
          <MetricCard label="Human detection" value={telemetry ? String(telemetry.human_detection_conf) : "—"} sub="confidence" />
          <MetricCard
            label="Cliff distance L / R"
            value={telemetry ? `${telemetry.left_cliff_dist_cm} / ${telemetry.right_cliff_dist_cm}` : "—"}
            sub="cm"
          />
          <MetricCard label="Ground loss" value={telemetry ? String(telemetry.ground_loss_trigger) : "—"} />
          <MetricCard
            label="Beacon / RSSI"
            value={telemetry ? `${telemetry.active_beacon_id} · ${telemetry.beacon_rssi_dbm} dBm` : "—"}
          />
        </div>

        <div className="mt-4 flex items-center gap-2">
          {telemetry?.hazard_warning_flag ? <Pill tone="red">Hazard warning active</Pill> : <Pill tone="green">Hazard clear</Pill>}
        </div>

        <div className="mt-6">
          <ThermalUpscalingCanvas
            fogDensityPct={Number(telemetry?.visual_fog_density_pct ?? 0)}
            humanDetectionConf={Number(telemetry?.human_detection_conf ?? 0)}
            forwardLidarCm={Number(telemetry?.forward_lidar_cm ?? 1200)}
            thermalTempGradient={Number(telemetry?.thermal_temp_gradient ?? 0)}
          />
        </div>

        <Card className="mt-6">
          <h2 className="mb-2 text-base font-bold text-slate-900">Safety explanation</h2>
          <p className="text-sm text-slate-600">{vehicle?.safety.explanation ?? "Waiting for backend snapshot."}</p>
          <p className="mt-3 text-xs text-slate-400">
            SIMULATED VEHICLE/ENVIRONMENT ORIENTATION — NOT A PHYSICAL IMU READING. Braking pressure and brake status
            are not physical actuator readings.
          </p>
        </Card>
      </div>
    </div>
  );
}
