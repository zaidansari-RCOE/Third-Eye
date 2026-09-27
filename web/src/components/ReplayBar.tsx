import { useEffect, useState } from "react";
import type { IncidentView } from "../types";

type Props = { incidents: IncidentView[]; onSelectIncident?: (incident: IncidentView | null) => void };

export function ReplayBar({ incidents, onSelectIncident }: Props) {
  const ordered = [...incidents].sort((a, b) => a.created_timestamp_seconds - b.created_timestamp_seconds);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    // Follow the most recent stored incident as new ones arrive, unless the
    // presenter has already scrubbed backward to review an earlier one.
    setIndex((current) => (current >= ordered.length - 1 ? Math.max(0, ordered.length - 1) : current));
  }, [ordered.length]);

  useEffect(() => {
    onSelectIncident?.(ordered[Math.min(index, ordered.length - 1)] ?? null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, ordered.length]);

  if (ordered.length === 0) {
    return (
      <div className="flex items-center gap-3 text-sm text-slate-400">
        <span className="font-semibold text-slate-500">Black-box replay</span>
        <span>No stored incident logs yet — this fills in as safety events occur.</span>
      </div>
    );
  }

  const incident = ordered[Math.min(index, ordered.length - 1)];

  return (
    <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
      <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
        <span>Black-box replay</span>
        <span className="tabular text-slate-400">
          {index + 1} / {ordered.length}
        </span>
      </div>
      <div className="flex flex-1 items-center gap-3">
        <button
          className="rounded-full border border-slate-200 px-2.5 py-1 text-sm font-semibold text-slate-500 hover:bg-slate-50 disabled:opacity-30"
          disabled={index <= 0}
          onClick={() => setIndex((value) => Math.max(0, value - 1))}
          aria-label="Previous stored incident"
        >
          ◀
        </button>
        <input
          type="range"
          className="h-2 flex-1 cursor-pointer accent-signal-600"
          min={0}
          max={Math.max(0, ordered.length - 1)}
          value={index}
          onChange={(event) => setIndex(Number(event.target.value))}
          aria-label="Scrub stored incident history"
        />
        <button
          className="rounded-full border border-slate-200 px-2.5 py-1 text-sm font-semibold text-slate-500 hover:bg-slate-50 disabled:opacity-30"
          disabled={index >= ordered.length - 1}
          onClick={() => setIndex((value) => Math.min(ordered.length - 1, value + 1))}
          aria-label="Next stored incident"
        >
          ▶
        </button>
      </div>
      <div className="flex min-w-0 flex-1 items-center gap-2 truncate text-sm text-slate-600 sm:justify-end">
        <span className="tabular font-semibold text-slate-900">t={incident.created_timestamp_seconds.toFixed(1)}s</span>
        <span className="truncate">
          {incident.vehicle_id} · {incident.title}
        </span>
      </div>
    </div>
  );
}
