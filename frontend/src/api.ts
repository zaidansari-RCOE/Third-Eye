import type { Beacon, Incident, Scenario, State, Telemetry } from "./types";

const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, { headers: { "content-type": "application/json" }, ...options });
  if (!response.ok) throw new Error(`${response.status} ${path}`);
  return response.json() as Promise<T>;
}
export const api = {
  state: () => request<State>("/api/simulation/state"),
  start: () => request<State>("/api/simulation/start", { method: "POST" }),
  pause: () => request<State>("/api/simulation/pause", { method: "POST" }),
  reset: () => request<State>("/api/simulation/reset", { method: "POST" }),
  scenario: (scenario: Scenario) => request<State>("/api/simulation/scenario", { method: "POST", body: JSON.stringify({ scenario }) }),
  telemetry: (vehicleId: string) => request<{ telemetry: Telemetry }>(`/api/simulation/vehicles/${vehicleId}/telemetry`),
  incidents: () => request<{ incidents: Incident[] }>("/api/incidents"),
  acknowledge: (id: string) => request<Incident>(`/api/incidents/${id}/acknowledge`, { method: "POST" }),
  beacons: () => request<{ beacons: Beacon[] }>("/api/v2i/beacons"),
  speedLimit: (id: string, speed_limit_kph: number) => request<Beacon>(`/api/v2i/beacons/${id}/speed-limit`, { method: "PUT", body: JSON.stringify({ speed_limit_kph }) }),
  injectHazard: (id: string, message: string) => request<Beacon>(`/api/v2i/beacons/${id}/hazard`, { method: "POST", body: JSON.stringify({ message }) }),
  clearHazard: (id: string) => request<Beacon>(`/api/v2i/beacons/${id}/hazard`, { method: "DELETE" }),
};
