# Simulation API (Phase 3-6)

The API exposes simulated Digital Twin state and deterministic fused telemetry
only. It contains no hardware I/O and no physical sensor data. As of Phase 6
it also serves a read-only control-room aggregation and backs the `web/`
React frontend; the API itself still makes no UI decisions.

## REST endpoints

| Method | Path | Result |
|---|---|---|
| GET | `/api/health` | Phase 6 health payload: `service`, `phase`, `hardware_connected` (always `false`). |
| GET | `/api/simulation/map` | Phase 6 static topology document (mine area, benches, safe zones, cliff boundaries, intersections, road segments, routes) for map rendering. |
| GET | `/api/simulation/control-room` | Phase 6 read-only aggregation: clock, scenario, conditions, per-vehicle telemetry/validation/safety, beacons, active/recent incidents, and fleet KPIs. Never mutates state. |
| POST | `/api/simulation/advance` | Explicitly advances the deterministic clock; body: `{"seconds": 1.0}`. Only moves vehicles while the clock is running. |
| GET | `/api/simulation/state` | Current authoritative simulated state. |
| POST | `/api/simulation/start` | Marks the deterministic clock as running. |
| POST | `/api/simulation/pause` | Marks the deterministic clock as paused. |
| POST | `/api/simulation/reset` | Restores the exact initial paused state and clears incident history. |
| POST | `/api/simulation/scenario` | Selects a qualitative scenario. Body: `{"scenario":"NORMAL"}`. |
| GET | `/api/simulation/vehicles/{vehicle_id}/telemetry` | Derived simulated telemetry and per-reading validation status. |
| GET | `/api/simulation/vehicles/{vehicle_id}/safety` | Current derived safety decision and optional active safety event. |
| GET | `/api/v2i/beacons` | All existing simulated beacon states. |
| GET | `/api/v2i/beacons/{beacon_id}` | One beacon state. |
| PUT | `/api/v2i/beacons/{beacon_id}/speed-limit` | Set simulated speed limit; body: `{"speed_limit_kph":10}`. |
| POST/DELETE | `/api/v2i/beacons/{beacon_id}/hazard` | Inject with `{"message":"..."}` or clear simulated hazard. |
| POST | `/api/v2i/beacons/{beacon_id}/failure` | Simulate failure/recovery; body: `{"failed":true}`. |
| GET | `/api/incidents` | In-memory incident history. |
| GET | `/api/incidents/active` | Active and acknowledged incidents. |
| GET | `/api/incidents/{incident_id}` | One incident. |
| POST | `/api/incidents/{incident_id}/acknowledge` | Mark active incident acknowledged. |
| POST | `/api/incidents/{incident_id}/resolve` | Resolve incident. |
| OPTIONS | any path | CORS preflight; returns `204` with CORS headers. |

Invalid or missing scenario/seconds values return `400`; unknown paths return `404`.

## WebSocket endpoint

`/api/simulation/ws` accepts an ASGI WebSocket connection and immediately sends
a control-room snapshot envelope:

```json
{
  "type": "control_room_snapshot",
  "origin": "simulated",
  "payload": { "...": "the same document as GET /api/simulation/control-room" }
}
```

Phase 6 behavior:

- Any client message (`websocket.receive`) is answered with another current
  snapshot; the socket does not itself advance time.
- After any state-changing HTTP command (`start`, `pause`, `reset`, `scenario`,
  `advance`, beacon updates, incident acknowledge/resolve) that returns a
  non-error status, the adapter broadcasts a fresh `control_room_snapshot` to
  every connected socket.
- An optional demo ticker (`SimulationAsgiApp(demo_tick_hz=...)`, or
  `create_demo_app()` reading `THIRD_EYE_DEMO_TICK_HZ`, default 8 Hz) calls
  `SimulationService.advance` on a fixed interval only while the clock is
  running, then broadcasts. It is disabled by default (`demo_tick_hz=0.0`) and
  stays disabled in the test suite. This cadence is a
  **SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT**, purely for display.

The telemetry endpoint returns an envelope with `origin: "simulated"`, a
`telemetry` object containing exactly the 22 Phase 1 fields in order, and a
separate `validation` object. Validation metadata is never a 23rd telemetry
field.

Safety responses expose structured, simulated decisions only. An
`EMERGENCY_OVERRIDE_SIMULATED` action means the Phase 2 movement authority will
apply configured software-only deceleration on a later explicit time advance; it
does not command physical braking hardware.

V2I and incident operations are framework-neutral API facade methods. They use
the existing simulated beacon objects and in-memory incident repository only.

## Phase 6 frontend consumer

`web/` is the only frontend that consumes this API. It calls the REST
endpoints above for one-shot reads/commands and subscribes to
`/api/simulation/ws` for live updates; on disconnect it freezes the last
received snapshot and reconnects with exponential backoff rather than
computing anything locally. `frontend/` (an older prototype) does not consume
Phase 6 endpoints and is not the supported client.

## Serving

`SimulationAsgiApp` is dependency-free and ASGI-compatible; `create_demo_app()`
is the uvicorn-facing factory used to serve `web/` in development
(`PYTHONPATH=src python -m uvicorn third_eye.api.asgi:create_demo_app --factory`).
The API facade is fully testable without installing a web framework.
