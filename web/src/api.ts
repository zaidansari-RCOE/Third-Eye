import type { ControlRoomSnapshot, MapDocument, WsEnvelope } from "./types";

// Automatically target the backend service if running on Render domain, otherwise use empty string for local dev proxy
function getBackendUrl(): string {
  const customEnv = (import.meta.env.VITE_BACKEND_URL ?? "").trim().replace(/\/$/, "");
  if (customEnv) return customEnv;

  // If hosted on Render static site, automatically map frontend name to backend name
  if (typeof window !== "undefined" && window.location.hostname.includes("onrender.com")) {
    const host = window.location.hostname;
    // Replaces "-frontend" with "-backend" in the hostname automatically
    const backendHost = host.replace(/-frontend(-[a-z0-9]+)?\.onrender\.com$/, "-backend$1.onrender.com");
    if (backendHost !== host) {
      return `https://${backendHost}`;
    }
    // Fallback if naming convention differs slightly
    return `https://third-eye-backend.onrender.com`;
  }

  return "";
}

const BACKEND_URL = getBackendUrl();

function apiUrl(path: string): string {
  return `${BACKEND_URL}${path}`;
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { error?: string };
    return body.error ?? `HTTP ${response.status}`;
  } catch {
    return `HTTP ${response.status}`;
  }
}

export async function getHealth(): Promise<{ service: string; phase: string; hardware_connected: boolean }> {
  const response = await fetch(apiUrl("/api/health"));
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function getMap(): Promise<MapDocument> {
  const response = await fetch(apiUrl("/api/simulation/map"));
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function getControlRoom(): Promise<ControlRoomSnapshot> {
  const response = await fetch(apiUrl("/api/simulation/control-room"));
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function postJson(path: string, body?: unknown): Promise<unknown> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? "{}" : JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function putJson(path: string, body: unknown): Promise<unknown> {
  const response = await fetch(apiUrl(path), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function deletePath(path: string): Promise<unknown> {
  const response = await fetch(apiUrl(path), { method: "DELETE" });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export function websocketUrl(): string {
  // Explicitly target the backend service domain via wss:// if hosted on Render
  if (typeof window !== "undefined" && window.location.hostname.includes("onrender.com")) {
    const host = window.location.hostname;
    const backendHost = host.replace(/-frontend(-[a-z0-9]+)?\.onrender\.com$/, "-backend$1.onrender.com");
    if (backendHost !== host) {
      return `wss://${backendHost}/api/simulation/ws`;
    }
    return `wss://third-eye-backend.onrender.com/api/simulation/ws`;
  }

  if (BACKEND_URL) {
    try {
      const url = new URL(BACKEND_URL);
      const protocol = url.protocol === "https:" ? "wss:" : "ws:";
      return `${protocol}//${url.host}/api/simulation/ws`;
    } catch {
      // fallback if URL parsing fails
    }
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/simulation/ws`;
}

export function parseEnvelope(raw: string): WsEnvelope {
  return JSON.parse(raw) as WsEnvelope;
}
