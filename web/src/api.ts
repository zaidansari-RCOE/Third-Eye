import type { ControlRoomSnapshot, MapDocument, WsEnvelope } from "./types";

const BACKEND_URL = "https://third-eye-backend-1nwu.onrender.com";

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
  return "wss://third-eye-backend-1nwu.onrender.com/api/simulation/ws";
}

export function parseEnvelope(raw: string): WsEnvelope {
  return JSON.parse(raw) as WsEnvelope;
}
