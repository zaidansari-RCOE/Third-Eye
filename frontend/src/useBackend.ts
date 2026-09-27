import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Incident, State, Telemetry } from "./types";

export function useBackend() {
  const [state, setState] = useState<State | null>(null); const [incidents, setIncidents] = useState<Incident[]>([]); const [telemetry, setTelemetry] = useState<Telemetry | null>(null); const [selectedVehicle, setSelectedVehicle] = useState("D01"); const [connected, setConnected] = useState(false);
  const refresh = useCallback(async () => { try { const next = await api.state(); const list = await api.incidents(); const t = await api.telemetry(selectedVehicle); setState(next); setIncidents(list.incidents); setTelemetry(t.telemetry); setConnected(true); } catch { setConnected(false); } }, [selectedVehicle]);
  useEffect(() => { refresh(); const timer = window.setInterval(refresh, 1500); return () => window.clearInterval(timer); }, [refresh]);
  return { state, incidents, telemetry, selectedVehicle, setSelectedVehicle, connected, refresh };
}
