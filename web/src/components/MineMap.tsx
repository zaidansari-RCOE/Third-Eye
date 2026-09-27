import { useMemo, useState } from "react";
import type { MapDocument, VehicleView, BeaconView } from "../types";

// Traffic-light semantics are real content: they mirror the backend's
// safety_zone field exactly. Never repurpose these three colors for chrome.
const ZONE_COLOR: Record<string, string> = {
  green: "#10b981",
  yellow: "#f59e0b",
  red: "#ef4444",
};

const ZONE_LABEL: Record<string, string> = {
  green: "Normal operation",
  yellow: "Advisory",
  red: "Emergency brake",
};

type Props = {
  map: MapDocument | null;
  vehicles: VehicleView[];
  beacons: BeaconView[];
  selectedId: string | null;
  onSelect: (vehicleId: string) => void;
  live: boolean;
};

function WifiTowerIcon({ color }: { color: string }) {
  return (
    <g>
      <circle r="3" fill={color} />
      <path d="M -8 -6 A 11 11 0 0 1 8 -6" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" />
      <path d="M -4.5 -1.5 A 6 6 0 0 1 4.5 -1.5" fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" />
    </g>
  );
}

export function MineMap({ map, vehicles, beacons, selectedId, onSelect, live }: Props) {
  const [hoveredBeacon, setHoveredBeacon] = useState<string | null>(null);

  const nearBeaconIds = useMemo(() => {
    const ids = new Set<string>();
    vehicles.forEach((vehicle) => {
      const active = vehicle.telemetry.active_beacon_id;
      if (typeof active === "string" && active) ids.add(active);
    });
    return ids;
  }, [vehicles]);

  if (!map) {
    return (
      <div className="flex h-full min-h-[420px] items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-400">
        Waiting for backend map…
      </div>
    );
  }

  const points = [
    ...map.mine_area.boundary,
    ...map.benches.flatMap((item) => item.boundary),
    ...map.safe_zones.flatMap((item) => item.boundary),
    ...map.road_segments.flatMap((item) => [item.start, item.end]),
  ];
  const xs = points.map((item) => item.x_m);
  const ys = points.map((item) => item.y_m);
  const minX = Math.min(...xs) - 40;
  const maxX = Math.max(...xs) + 40;
  const minY = Math.min(...ys) - 40;
  const maxY = Math.max(...ys) + 40;
  const width = maxX - minX;
  const height = maxY - minY;
  const ty = (y: number) => minY + maxY - y;

  const poly = (boundary: { x_m: number; y_m: number }[]) =>
    boundary.map((item) => `${item.x_m},${ty(item.y_m)}`).join(" ");

  return (
    <div className="relative h-full min-h-[420px] overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
      <svg viewBox={`${minX} ${minY} ${width} ${height}`} className="h-full w-full" role="img" aria-label="Live haul road safety map">
        <polygon points={poly(map.mine_area.boundary)} fill="#f8fafc" stroke="#cbd5e1" strokeWidth="3" strokeDasharray="2 6" />
        {map.benches.map((bench) => (
          <polygon key={bench.bench_id} points={poly(bench.boundary)} fill="#f1f5f9" stroke="#e2e8f0" strokeWidth="1.5" />
        ))}
        {map.safe_zones.map((zone) => (
          <polygon key={zone.zone_id} points={poly(zone.boundary)} fill="#ecfdf5" stroke="#6ee7b7" strokeWidth="2" />
        ))}
        {map.road_segments.map((road) => (
          <line
            key={road.segment_id}
            x1={road.start.x_m}
            y1={ty(road.start.y_m)}
            x2={road.end.x_m}
            y2={ty(road.end.y_m)}
            stroke={road.is_blind_curve ? "#f59e0b" : "#94a3b8"}
            strokeWidth={road.is_blind_curve ? 7 : 5}
            strokeLinecap="round"
          />
        ))}
        {map.cliff_boundaries.map((cliff) => (
          <line
            key={cliff.boundary_id}
            x1={cliff.start.x_m}
            y1={ty(cliff.start.y_m)}
            x2={cliff.end.x_m}
            y2={ty(cliff.end.y_m)}
            stroke="#f87171"
            strokeWidth="4"
            strokeDasharray="10 7"
            strokeLinecap="round"
          />
        ))}
        {map.intersections.map((item) => (
          <circle
            key={item.intersection_id}
            cx={item.coordinate.x_m}
            cy={ty(item.coordinate.y_m)}
            r={item.is_blind_curve ? 8 : 5}
            fill={item.is_blind_curve ? "#f59e0b" : "#ffffff"}
            stroke="#94a3b8"
            strokeWidth="1.5"
          />
        ))}

        {beacons.map((beacon) => {
          const showTip = hoveredBeacon === beacon.beacon_id || nearBeaconIds.has(beacon.beacon_id);
          const plainMessage = beacon.hazard_broadcast_active
            ? beacon.hazard_message ?? "Caution advised near this beacon"
            : `Speed limit ${beacon.speed_limit_kph} kph near here`;
          return (
            <g
              key={beacon.beacon_id}
              transform={`translate(${beacon.position.x_m} ${ty(beacon.position.y_m)})`}
              onMouseEnter={() => setHoveredBeacon(beacon.beacon_id)}
              onMouseLeave={() => setHoveredBeacon((current) => (current === beacon.beacon_id ? null : current))}
              style={{ cursor: "default" }}
            >
              <WifiTowerIcon color={beacon.hazard_broadcast_active ? "#ef4444" : "#2563eb"} />
              <foreignObject x={-46} y={7} width={92} height={20} style={{ overflow: "visible" }}>
                <div className="pointer-events-none flex justify-center">
                  <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold text-slate-500 shadow-sm ring-1 ring-slate-200">
                    {beacon.beacon_id}
                  </span>
                </div>
              </foreignObject>
              {showTip ? (
                <foreignObject x={-120} y={-72} width={240} height={64} style={{ overflow: "visible" }}>
                  <div className="pointer-events-none rounded-lg bg-white px-3 py-2 text-center text-xs font-medium leading-snug text-slate-700 shadow-lg ring-1 ring-slate-200">
                    {plainMessage}
                  </div>
                </foreignObject>
              ) : null}
            </g>
          );
        })}

        {vehicles.map((vehicle) => {
          const color = ZONE_COLOR[vehicle.safety.safety_zone] ?? "#94a3b8";
          const selected = vehicle.vehicle_id === selectedId;
          return (
            <g
              key={vehicle.vehicle_id}
              style={{ cursor: "pointer" }}
              onClick={() => onSelect(vehicle.vehicle_id)}
              opacity={live ? 1 : 0.6}
            >
              <g transform={`translate(${vehicle.position.x_m} ${ty(vehicle.position.y_m)}) rotate(${-vehicle.heading_degrees})`}>
                {vehicle.safety.simulated_brake_active ? (
                  <circle r="18" fill="none" stroke={color} strokeWidth="2" className="animate-pulse-dot" />
                ) : null}
                <rect x={-13} y={-8} width={22} height={16} rx={4} fill={color} stroke="#ffffff" strokeWidth={selected ? 2.5 : 1.5} />
                <rect x={7} y={-6} width={8} height={12} rx={3} fill={color} stroke="#ffffff" strokeWidth={selected ? 2.5 : 1.5} />
              </g>
              <foreignObject
                x={vehicle.position.x_m - 70}
                y={ty(vehicle.position.y_m) - 46}
                width={140}
                height={26}
                style={{ overflow: "visible" }}
              >
                <div className="pointer-events-none flex justify-center">
                  <span
                    className="whitespace-nowrap rounded-full bg-white px-2.5 py-1 text-[11px] font-bold shadow-md ring-1 ring-slate-200"
                    style={{ color }}
                  >
                    {vehicle.vehicle_id} · {vehicle.velocity_kph.toFixed(0)} kph
                  </span>
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>

      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap gap-2">
        {(["green", "yellow", "red"] as const).map((zone) => (
          <span
            key={zone}
            className="flex items-center gap-1.5 rounded-full bg-white/95 px-2.5 py-1 text-[11px] font-semibold text-slate-600 shadow-sm ring-1 ring-slate-200"
          >
            <span className="h-2 w-2 rounded-full" style={{ background: ZONE_COLOR[zone] }} />
            {ZONE_LABEL[zone]}
          </span>
        ))}
      </div>
    </div>
  );
}
