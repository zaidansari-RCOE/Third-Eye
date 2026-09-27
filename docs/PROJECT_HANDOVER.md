# Project Handover

## Current phase

**Phase 6 complete** — Control Room backend aggregation, WebSocket streaming
refinement, and a verified React web frontend (`web/`). Do not begin Phase 7
or Phase 8 without a new instruction.

## Completed work

- Reviewed the proposal as the primary source of truth.
- Created exact, ordered 22-field telemetry contracts.
- Created data-origin separation with a default of `simulated`.
- Documented the non-IMU interpretation of pitch and roll.
- Added safety, V2I/beacon, and incident domain definitions without runtime
  processing.
- Added future hardware protocols for Raspberry Pi 4, AMG8833, TF-Luna,
  left/right VL53L1X, Pi Camera, and ESP32 V2I beacon.
- Added transport-neutral API response contracts and Phase 1 documentation.
- Added standard-library automated contract tests.
- Added deterministic simulation clock with start, pause, reset, and explicit
  advance operations.
- Added fictional virtual mine topology, three deterministic loop routes, three
  virtual dump trucks, and three virtual V2I beacons.
- Added qualitative scenarios that establish state only, without safety actions.
- Added REST and WebSocket ASGI adapters for simulated state only.
- Added causal simulated sensor frames for TF-Luna, AMG8833, left/right
  VL53L1X, camera context, diagnostics, V2I, and orientation.
- Added validation records for source, simulation timestamp, validity, stale
  state, and non-finite values.
- Added fusion from validated sensor readings to the unchanged exact 22-field
  telemetry contract with `DataOrigin.SIMULATED`.
- Added deterministic safety evaluation for collision, cliff/ground-loss,
  visibility, V2I, and validation failures.
- Added typed safety decisions and future-control-room safety-event projection.
- Added centralized simulation threshold register and software-only simulated
  braking integrated into the existing Phase 2 movement authority.
- Extended the existing B01-B03 virtual beacons with speed limit, hazard
  message, and last-update state; no second beacon model was created.
- Added deterministic road-associated beacon relevance, RSSI, dynamic limits,
  hazard injection, simulated failure/recovery, and API operations.
- Added in-memory persistent-to-process incident history sourced only from
  Phase 4 safety decisions, including deduplication, acknowledgement, and
  resolution.

## Phase 6 completed work

- Verified the existing `SimulationApi.dispatch` continues to be the single
  routing surface; added `GET /api/health`, `GET /api/simulation/map`, and
  `GET /api/simulation/control-room` as read-only additions. No second
  simulation engine was created.
- Added `api/snapshot.py`: a derived, read-only control-room aggregation
  (per-vehicle telemetry/validation/safety, beacons, incidents, and fleet
  KPIs) that never mutates `SimulationState` and never invents telemetry.
- Verified `api/asgi.py`: a dependency-free ASGI HTTP/WebSocket adapter with
  CORS/OPTIONS handling, a WebSocket at `/api/simulation/ws` that sends a
  `control_room_snapshot` envelope on connect and again after any mutating
  HTTP command, and an optional demo ticker (disabled in tests, opt-in via
  `THIRD_EYE_DEMO_TICK_HZ` for `create_demo_app`).
- Verified `reset()` continues to clear `IncidentManager` history
  (`SimulationApi.reset`).
- Verified the existing `web/` React (Vite + TypeScript) frontend provides
  the Control Room route, the `/hud/:vehicleId` Driver HUD route, the local
  x_m/y_m mine map with D01-D03 and B01-B03 markers, start/pause/reset/
  scenario controls, fleet KPIs, the full 22-field telemetry panel, safety
  and incident panels, beacon/V2I controls, and WebSocket live updates with
  reconnection backoff and freeze-last-snapshot-on-disconnect behavior. The
  frontend performs no movement, sensor, safety, incident, RSSI, or telemetry
  calculation of its own.
- Confirmed the `SIMULATED DIGITAL TWIN — NO PHYSICAL HARDWARE CONNECTED.`
  banner and the `SIMULATED VEHICLE/ENVIRONMENT ORIENTATION — NOT A PHYSICAL
  IMU READING.` notice are present on the relevant screens.
- Left `frontend/` (an older, alternative frontend) untouched and unmerged;
  added `frontend/README.md` marking it as legacy/unused only.
- Did not add Phase 7 or Phase 8 functionality.

## Post-handover visual redesign and demo tooling (same Phase 6)

- Restyled `web/` in place to a clean, light Tailwind CSS theme for the
  hackathon presentation. All existing data wiring (`api.ts`, `types.ts`,
  `useSimulation.ts`) is unchanged; only presentation components were
  rewritten. No new frontend directory was created.
- Added `ThermalUpscalingCanvas.tsx` (Driver HUD) and `useAlertSiren.ts`
  (Web Audio, silent by default, user-gesture-gated), both driven only by
  real telemetry fields already in `VehicleView` — no client-side safety
  computation.
- Added `ReplayBar.tsx`: a black-box replay slider that scrubs the existing,
  already-stored `incidents_recent` telemetry context. It reads history only
  and introduces no new backend replay engine.
- Added `src/third_eye/demo/hackathon_scenarios.py`
  (`HackathonScenarioGenerator`): a presentation choreography helper that
  calls the existing frozen `SimulationApi` through its normal REST surface
  to script three named demo narratives (`BLIND_CURVE_APPROACH`,
  `SUDDEN_OBSTACLE_EMERGENCY`, `CLIFF_DRIFT_PREVENTION`). Each narrative's
  timing was verified against the live engine, not guessed; see the module
  docstring. It is not a second simulation engine and does not touch the
  WebSocket protocol directly — mutating HTTP calls it makes are broadcast by
  the existing, unmodified `asgi.py`.
- Added `tests/test_hackathon_scenarios.py` (7 tests, in-process, no
  network) asserting the real backend states each narrative reaches.

## Files created

- `pyproject.toml`
- `src/third_eye/__init__.py`
- `src/third_eye/domain/{__init__,telemetry,safety,v2i,incidents}.py`
- `src/third_eye/adapters/{__init__,contracts}.py`
- `src/third_eye/api/{__init__,contracts}.py`
- `tests/{__init__,test_telemetry_contract,test_domain_and_adapter_contracts}.py`
- `README.md`
- `docs/{REQUIREMENT_TRACEABILITY,ARCHITECTURE,API_CONTRACTS,SIMULATION_ASSUMPTIONS,PROJECT_HANDOVER}.md`

## Phase 2 files created

- `src/third_eye/simulation/{__init__,models,topology,engine}.py`
- `src/third_eye/api/{simulation,asgi}.py`
- `docs/API.md`
- `tests/test_simulation_engine.py`
- `tests/test_simulation_api.py`

## Phase 2 files modified

- `README.md`
- `src/third_eye/api/__init__.py`
- `docs/ARCHITECTURE.md`
- `docs/SIMULATION_ASSUMPTIONS.md`
- `docs/PROJECT_HANDOVER.md`

## Phase 3 files created

- `src/third_eye/simulation/{sensors,validation,fusion,telemetry}.py`
- `tests/test_sensor_telemetry_pipeline.py`

## Phase 3 files modified

- `README.md`
- `src/third_eye/simulation/__init__.py`
- `src/third_eye/api/simulation.py`
- `docs/{ARCHITECTURE,API,SIMULATION_ASSUMPTIONS,REQUIREMENT_TRACEABILITY,PROJECT_HANDOVER}.md`

## Phase 4 files created

- `src/third_eye/safety/{__init__,config,engine,events}.py`
- `tests/test_safety_engine.py`

## Phase 4 files modified

- `README.md`
- `src/third_eye/domain/safety.py`
- `src/third_eye/simulation/{models,engine}.py`
- `src/third_eye/api/simulation.py`
- `docs/{ARCHITECTURE,API,SIMULATION_ASSUMPTIONS,REQUIREMENT_TRACEABILITY,PROJECT_HANDOVER}.md`

## Phase 5 files created

- `src/third_eye/simulation/v2i.py`
- `src/third_eye/incidents/{__init__,service}.py`
- `tests/test_phase5_v2i_incidents.py`

## Phase 5 files modified

- `README.md`
- `src/third_eye/domain/incidents.py`
- `src/third_eye/simulation/{models,engine,sensors}.py`
- `src/third_eye/api/simulation.py`
- `docs/{ARCHITECTURE,API,SIMULATION_ASSUMPTIONS,REQUIREMENT_TRACEABILITY,PROJECT_HANDOVER}.md`

## Phase 6 files (pre-existing at handover, verified only)

- `src/third_eye/api/snapshot.py`
- `src/third_eye/api/asgi.py`
- `tests/test_phase6_control_room.py`
- `web/` (full React + TypeScript frontend: `index.html`, `package.json`,
  `vite.config.ts`, `tsconfig.json`, and `src/{App.tsx, api.ts, types.ts,
  useSimulation.ts, main.tsx, index.css, vite-env.d.ts,
  components/{BeaconPanel,IncidentPanel,MineMap,TelemetryPanel}.tsx,
  pages/{ControlRoom,DriverHud}.tsx}`)

## Phase 6 files created or modified during this handover

- `README.md` (status, Phase 6 additions, local run instructions)
- `docs/PROJECT_HANDOVER.md` (this file)
- `docs/API.md` (Phase 6 endpoint and WebSocket envelope documentation)
- `docs/ARCHITECTURE.md` (Phase 6 addendum)
- `docs/REQUIREMENT_TRACEABILITY.md` (Phase 6 rows)
- `frontend/README.md` (new; marks the legacy frontend as unused)

No Phase 1-5 source file, and no Phase 1-5 test, was modified. The 57
pre-existing tests were re-run and pass unchanged.

## Files modified

None. The repository initially contained only `thirdeye.pdf`.

## Tests

Run:

```powershell
& 'C:\Users\shubham\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest verified result: **64 tests passed, 0 failed** (46 from Phase 1-4, plus
Phase 5's `test_phase5_v2i_incidents.py`, Phase 6's
`test_phase6_control_room.py`, and 7 from `test_hackathon_scenarios.py`). Coverage includes Phase 1 exact telemetry and
hardware separation, Phase 2 deterministic topology/movement/state/API
behavior, Phase 3 raw sensor frames/validation/fusion, Phase 4 deterministic
risk evaluation, explanations, scenarios, simulated braking, safety events,
centralized thresholds, Phase 5 V2I configuration, beacon failure, and
incident lifecycle, and Phase 6 health/map/control-room endpoints, CORS/
OPTIONS, `advance` gating, WebSocket snapshot-on-connect and push-after-
mutation, the demo ticker being disabled by default in tests, and
`reset()` clearing incident history. No external test dependency is required
for the Python suite; `web/` additionally passed `tsc --noEmit && vite build`.

## Known limitations

- No physical sensor or telemetry hardware; every sensor input remains
  software simulated and `hardware_connected` is always `false`.
- No physical safety actuation or alert hardware outside this backend API.
  Simulated braking and the `SIMULATED BRAKE ACTIVE` HUD indicator are
  software-only.
- Incidents persist in-process only (no durable storage); a process restart
  clears history, and `reset()` clears it explicitly.
- No production server hosting, TLS termination, or authentication is
  specified; the demo ticker (`create_demo_app`) is a display-cadence
  convenience, not an engineering requirement.
- The proposal leaves numerous runtime choices unspecified; see
  `SIMULATION_ASSUMPTIONS.md`.
- `frontend/` (the older, alternative prototype) remains unused and was not
  extended.

## Exact next phase

Phase 6 is complete. Any Phase 7 or Phase 8 work requires a new, explicit user
instruction; do not begin it speculatively. Whatever it is, it must not alter
the Phase 1 telemetry contract, must not create physical actuation, and any
numerical additions remain **SIMULATION ASSUMPTION — NOT AN ENGINEERING
LIMIT**.

## Instructions for another AI

1. Read `README.md` and every file in `docs/` before editing.
2. Treat `thirdeye.pdf` as the primary source; do not invent proposal claims.
3. Do not alter the 22 telemetry names, count, or order; run the existing tests
   after every change.
4. Keep hardware adapters as interfaces until an explicitly approved hardware
   phase. Never add GPIO/I2C/UART/SPI/ESP-NOW access to a software-only phase.
5. Keep simulation metadata outside the 22-field telemetry payload and default
   it to `simulated`.
6. Preserve the exact non-IMU orientation statement in simulation documentation.
7. Treat `SimulationService.state` as the only authoritative state. Do not create
   a second mutable vehicle, map, beacon, or clock state for later consumers.
8. Treat Phase 3 telemetry as derived from `SimulationService.state` through
   `TelemetryService`; do not bypass validation or mutate `TelemetrySnapshot`.
9. Keep Phase 4 threshold values centralized in `safety/config.py`; never label
   them as mining engineering limits or physical brake behavior.
10. Keep beacon state in the existing `VirtualBeacon` objects and incidents in
    `IncidentManager`; do not create parallel V2I/hazard or incident engines.
11. Treat `web/` as the only Phase 6 frontend. Do not create another frontend,
    and do not merge or delete `frontend/` (the older, unused prototype).
12. Keep `api/snapshot.py` read-only: it must never mutate `SimulationState`
    or advance the clock; it only derives a control-room view from existing
    state.
13. The frontend must never compute vehicle movement, sensor values, safety
    decisions, incidents, RSSI, or telemetry; those come only from the Python
    backend via REST/WebSocket.
14. Do not begin Phase 7 or Phase 8 without an explicit new instruction.
