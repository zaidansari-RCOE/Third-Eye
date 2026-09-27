# THIRD EYE

Software-only internal-demonstration prototype for the Third Eye Fog-Shield
System. This repository is rebuilding the proposal as a staged software
prototype while preserving a future Raspberry Pi 4 / ESP32 integration boundary.

## Current status

**Phase 6 complete: Control Room backend aggregation, WebSocket streaming, and
a React web frontend.** The system has a Control Room route, a per-vehicle
Driver HUD route, live map, fleet KPIs, telemetry/safety/incident/beacon
panels, and WebSocket live updates with reconnection and freeze-on-disconnect
behavior. There is still no physical V2I runtime or hardware I/O; every value
remains software-simulated and `hardware_connected` is always `false`.

**Visual design:** `web/` uses a clean, light (white/`slate-50`) Tailwind CSS
theme intended for a hackathon presentation — bold metric cards, a large
"Shift Safety Score" rollup, traffic-light vehicle markers on the map, a
black-box incident-replay slider, a foggy-vs-thermal illustrative canvas on
the Driver HUD, and a muted-by-default Web Audio alert engine. Every value
shown is still read from the real backend snapshot; nothing is hardcoded or
computed client-side beyond simple display rollups (see
`docs/SIMULATION_ASSUMPTIONS.md`).

**Demo tooling:** `src/third_eye/demo/hackathon_scenarios.py` provides
`HackathonScenarioGenerator`, a presentation choreography helper that drives
the existing `SimulationApi` (reset → scenario → start → advance) to script
three named demo narratives. It is not a second simulation engine.

## Phase 6 additions

- `GET /api/health`, `GET /api/simulation/map`, `GET /api/simulation/control-room`,
  and `POST /api/simulation/advance`, alongside the existing Phase 2-5 REST
  operations, CORS/OPTIONS handling, and the `/api/simulation/ws` WebSocket.
- A single authoritative `SimulationService` continues to back every endpoint;
  Phase 6 adds only a read-only aggregation (`api/snapshot.py`) and a
  dependency-free ASGI adapter (`api/asgi.py`) with an optional demo ticker.
- `web/`: the primary Phase 6 React (Vite + TypeScript) frontend. It renders
  the Control Room and Driver HUD from backend snapshots only — it never
  computes vehicle movement, sensor values, safety decisions, incidents, RSSI,
  or telemetry itself. Every screen displays
  `SIMULATED DIGITAL TWIN — NO PHYSICAL HARDWARE CONNECTED.`
- `frontend/` is an older, alternative frontend prototype. It is **not** the
  Phase 6 frontend, is unused, and has not been modified or merged with
  `web/`. See `frontend/README.md`.

### Running the Phase 6 stack locally

Backend (dependency-free; `uvicorn` is only needed to actually serve HTTP/WS):

```bash
pip install uvicorn
PYTHONPATH=src python -m uvicorn third_eye.api.asgi:create_demo_app --factory --host 127.0.0.1 --port 8000
```

Frontend (proxies `/api` to `http://127.0.0.1:8000` in dev, see `web/vite.config.ts`):

```bash
cd web
npm install
npm run dev      # or: npm run build
```

### Running a scripted demo narrative

With the backend running (see above), script one of the three named
presentation narratives against it — any connected browser's Control Room or
Driver HUD updates live over the existing WebSocket, since `advance`,
`scenario`, `reset`, and `start` are ordinary mutating HTTP calls that the
ASGI adapter already broadcasts after:

```bash
PYTHONPATH=src python -m third_eye.demo.hackathon_scenarios BLIND_CURVE_APPROACH --base-url http://127.0.0.1:8000
PYTHONPATH=src python -m third_eye.demo.hackathon_scenarios SUDDEN_OBSTACLE_EMERGENCY --base-url http://127.0.0.1:8000
PYTHONPATH=src python -m third_eye.demo.hackathon_scenarios CLIFF_DRIFT_PREVENTION --base-url http://127.0.0.1:8000
```

Each narrative resets, selects the underlying real scenario, starts the
clock, and advances it in verified steps — see the module docstring in
`src/third_eye/demo/hackathon_scenarios.py` for the exact real backend states
each one reaches (not invented; checked against the live engine).

## What Phase 1 provides

- Proposal-to-deliverable requirement traceability
- A backend-oriented domain model with the exact 22-field telemetry contract
- Safety, V2I/beacon, and incident definitions only
- Future-hardware protocol interfaces, without physical I/O
- Deterministic virtual mine, routes, fleet, beacons, scenarios, and clock
- REST/WebSocket API adapters for simulated state only
- Causal simulated sensors, validation records, and fusion to Telemetry22
- Explainable risk evaluation, safety state, events, and simulated braking
- Configurable virtual beacons and persistent in-memory incident lifecycle
- Simulation-boundary documentation and automated contract tests

## Run tests

Use the bundled Python runtime available in this workspace:

```powershell
& 'C:\Users\shubham\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

## Documentation

- `docs/REQUIREMENT_TRACEABILITY.md`
- `docs/ARCHITECTURE.md`
- `docs/API_CONTRACTS.md`
- `docs/API.md`
- `docs/SIMULATION_ASSUMPTIONS.md`
- `docs/PROJECT_HANDOVER.md`
