import { useState } from "react";
import { deletePath, postJson, putJson } from "../api";
import type { BeaconView } from "../types";
import { Card, Pill, SectionHeading } from "./ui";

type Props = {
  beacons: BeaconView[];
  disabled: boolean;
  onCommand: (action: () => Promise<unknown>) => Promise<void>;
};

export function BeaconPanel({ beacons, disabled, onCommand }: Props) {
  const [limits, setLimits] = useState<Record<string, string>>({});
  const [messages, setMessages] = useState<Record<string, string>>({});

  return (
    <Card>
      <SectionHeading>V2I beacons</SectionHeading>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {beacons.map((beacon) => (
          <article key={beacon.beacon_id} className="flex flex-col gap-2 rounded-lg border border-slate-200 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-900">{beacon.beacon_id}</span>
              <Pill tone={beacon.communication_state === "online" ? "green" : "red"}>{beacon.communication_state}</Pill>
            </div>
            <div className="text-xs text-slate-500">
              Road {beacon.associated_road_segment_id} · zone {beacon.associated_zone_id}
            </div>
            <div className="text-xs text-slate-500">
              Limit <span className="tabular font-semibold text-slate-700">{beacon.speed_limit_kph} kph</span>
            </div>
            <div className="text-xs text-slate-500">
              Hazard: {beacon.hazard_broadcast_active ? <span className="font-semibold text-red-600">{beacon.hazard_message ?? "active"}</span> : "none"}
            </div>

            <div className="mt-1 flex gap-2">
              <input
                className="w-20 rounded-md border border-slate-200 px-2 py-1 text-xs tabular"
                value={limits[beacon.beacon_id] ?? String(beacon.speed_limit_kph)}
                disabled={disabled}
                onChange={(event) => setLimits((current) => ({ ...current, [beacon.beacon_id]: event.target.value }))}
                aria-label={`${beacon.beacon_id} speed limit`}
              />
              <button
                className="rounded-md bg-signal-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-signal-700 disabled:opacity-40"
                disabled={disabled}
                onClick={() =>
                  void onCommand(() =>
                    putJson(`/api/v2i/beacons/${beacon.beacon_id}/speed-limit`, {
                      speed_limit_kph: Number(limits[beacon.beacon_id] ?? beacon.speed_limit_kph),
                    }),
                  )
                }
              >
                Set limit
              </button>
            </div>

            <div className="flex gap-2">
              <input
                className="flex-1 rounded-md border border-slate-200 px-2 py-1 text-xs"
                value={messages[beacon.beacon_id] ?? ""}
                disabled={disabled}
                placeholder="Hazard message"
                onChange={(event) => setMessages((current) => ({ ...current, [beacon.beacon_id]: event.target.value }))}
              />
              <button
                className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                disabled={disabled}
                onClick={() =>
                  void onCommand(() =>
                    postJson(`/api/v2i/beacons/${beacon.beacon_id}/hazard`, {
                      message: messages[beacon.beacon_id] || "Control-room hazard",
                    }),
                  )
                }
              >
                Inject
              </button>
              <button
                className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                disabled={disabled}
                onClick={() => void onCommand(() => deletePath(`/api/v2i/beacons/${beacon.beacon_id}/hazard`))}
              >
                Clear
              </button>
            </div>

            <div className="flex gap-2">
              <button
                className="flex-1 rounded-md bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-100 disabled:opacity-40"
                disabled={disabled}
                onClick={() => void onCommand(() => postJson(`/api/v2i/beacons/${beacon.beacon_id}/failure`, { failed: true }))}
              >
                Fail
              </button>
              <button
                className="flex-1 rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-40"
                disabled={disabled}
                onClick={() => void onCommand(() => postJson(`/api/v2i/beacons/${beacon.beacon_id}/failure`, { failed: false }))}
              >
                Recover
              </button>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}
