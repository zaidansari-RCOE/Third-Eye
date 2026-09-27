import { TELEMETRY_FIELDS } from "../types";
import type { VehicleView } from "../types";
import { Card, Pill, SectionHeading, SeverityPill } from "./ui";

function isDegraded(name: string, value: string | number | boolean): boolean {
  if (value === -1 || value === -1.0 || value === -999 || value === "UNAVAILABLE") return true;
  if (
    name.includes("cliff") ||
    name.includes("lidar") ||
    name.includes("fog") ||
    name.includes("voltage") ||
    name.includes("current") ||
    name.includes("temp")
  ) {
    if (typeof value === "number" && value < 0) return true;
  }
  return false;
}

function fieldLabel(field: string): string {
  return field.replace(/_/g, " ");
}

type Props = { vehicle: VehicleView | null };

export function TelemetryPanel({ vehicle }: Props) {
  if (!vehicle) {
    return (
      <Card>
        <SectionHeading>Vehicle telemetry</SectionHeading>
        <p className="text-sm text-slate-400">Select D01, D02, or D03 on the map to inspect its full sensor readout.</p>
      </Card>
    );
  }

  const { telemetry, validation, safety } = vehicle;

  return (
    <Card>
      <SectionHeading
        action={
          <div className="flex items-center gap-2">
            <SeverityPill severity={safety.severity} />
            {safety.simulated_brake_active ? <Pill tone="red">Simulated brake active</Pill> : null}
          </div>
        }
      >
        {vehicle.vehicle_id} telemetry
      </SectionHeading>

      <p className="text-sm text-slate-600">
        <span className="font-semibold text-slate-900">{safety.action.replace(/_/g, " ")}.</span> {safety.explanation}
      </p>
      <p className="mt-2 text-xs text-slate-400">
        Triggered rules: {safety.triggered_rules.join(", ") || "none"} · Orientation readings are simulated
        vehicle/environment orientation, not a physical IMU reading.
      </p>

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {TELEMETRY_FIELDS.map((field) => {
          const value = telemetry[field];
          const degraded = isDegraded(field, value);
          return (
            <div key={field} className="rounded-lg border border-slate-200 px-3 py-2">
              <div className="truncate text-[11px] font-medium capitalize text-slate-500">{fieldLabel(field)}</div>
              <div className={`tabular text-sm font-bold ${degraded ? "text-red-600" : "text-slate-900"}`}>{String(value)}</div>
            </div>
          );
        })}
      </div>

      <div className="mt-4">
        <div className="mb-2 text-xs font-semibold text-slate-500">Sensor validation</div>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(validation).map(([name, record]) => (
            <span
              key={name}
              className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ${
                record.accepted ? "bg-slate-50 text-slate-500 ring-slate-200" : "bg-red-50 text-red-600 ring-red-200"
              }`}
              title={record.accepted ? "accepted" : record.reason ?? "rejected"}
            >
              {name.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      </div>
    </Card>
  );
}
