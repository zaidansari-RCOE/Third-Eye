# Requirement Traceability

Primary source: `thirdeye.pdf`, pages 1-11. Phase 1 implements contracts and
documentation only; a traceable item is not necessarily a functioning runtime.

| ID | Proposal source | Requirement | Phase 1 evidence | Status |
|---|---|---|---|---|
| RT-01 | pp. 1-3 | Work offline at the edge in fog/deep-pit conditions. | Simulation/hardware source separation and no cloud dependency. | Foundation only |
| RT-02 | p. 4 | Raspberry Pi 4 MCU performs vehicle-side sensor fusion and safety logic. | `RaspberryPiVehicleController` protocol. | Interface only |
| RT-03 | pp. 4, 6-7 | Support thermal, LiDAR, dual ToF, camera, and beacon inputs. | Hardware protocols in `adapters/contracts.py`. | Interface only |
| RT-04 | pp. 4, 8 | Preserve the 22 real-time parameters. | `TelemetrySnapshot` and contract tests. | Complete |
| RT-05 | pp. 4, 6 | Use ESP32 V2I beacons for speed and hazard communication. | Beacon definitions and ESP32 protocol. | Definition only |
| RT-06 | pp. 4-5, 9 | Represent collision, ground-loss, warnings, and override concepts. | Safety vocabulary only. | Definition only |
| RT-07 | p. 9 | Central dashboard receives vehicle diagnostic information. | Transport-neutral API contracts. | Contract only |
| RT-08 | pp. 6, 10 | Account for sensor/weather/power and radio risks. | Simulation-assumption and limitation documentation. | Documentation only |
| RT-09 | Phase 2 brief | One authoritative deterministic virtual-mine state. | `SimulationService` owns immutable `SimulationState`. | Complete |
| RT-10 | Phase 2 brief | Virtual mine with roads, benches, safe zones, cliffs, and blind curves. | `simulation/topology.py`. | Complete |
| RT-11 | Phase 2 brief | D01, D02, and D03 move by route geometry and speed. | `simulation/engine.py` and tests. | Complete |
| RT-12 | Phase 2 brief | B01, B02, and B03 are virtual V2I beacons. | `VirtualBeacon` initial state and tests. | Complete |
| RT-13 | Phase 2 brief | Support seven state-only scenarios. | `Scenario` and `ScenarioConditions`. | Complete |
| RT-14 | Phase 2 brief | Expose REST state lifecycle and WebSocket stream contracts. | `api/simulation.py`, `api/asgi.py`, and tests. | Complete |
| RT-15 | Phase 3 brief | Simulate proposal sensor inputs causally from state and scenarios. | `simulation/sensors.py`. | Complete |
| RT-16 | Phase 3 brief | Validate value/source/time/validity/stale state before fusion. | `simulation/validation.py`. | Complete |
| RT-17 | Phase 3 brief | Fuse to exact ordered 22-field telemetry only. | `simulation/fusion.py` and contract tests. | Complete |
| RT-18 | Phase 3 brief | Keep all outputs simulated and hardware-free. | Source tagging, `DataOrigin.SIMULATED`, and tests. | Complete |
| RT-19 | Phase 4 brief | Deterministic, explainable risk/severity/action decisions. | `safety/engine.py` and typed decisions. | Complete |
| RT-20 | Phase 4 brief | Centralize simulation-only safety thresholds. | `safety/config.py`. | Complete |
| RT-21 | Phase 4 brief | Software-only simulated braking through existing movement authority. | `SimulationService.advance()` and tests. | Complete |
| RT-22 | Phase 4 brief | Structured alert events for future control-room work. | `safety/events.py`. | Complete |
| RT-23 | Phase 5 brief | Simulate existing B01-B03 state, proximity, RSSI, limits, hazards, and failures. | `simulation/v2i.py`, beacon state, API tests. | Complete |
| RT-24 | Phase 5 brief | Create incident lifecycle from existing safety decisions/events. | `incidents/service.py`. | Complete |
| RT-25 | Phase 5 brief | Prevent repeated identical active incidents and preserve history/context. | Incident deduplication and telemetry context tests. | Complete |
| RT-26 | Phase 6 brief | Expose health, map, and control-room read endpoints without a second engine. | `api/snapshot.py`, `api/simulation.py` routes, `test_phase6_control_room.py`. | Complete |
| RT-27 | Phase 6 brief | Explicit `advance` endpoint that only moves vehicles while running. | `SimulationApi.advance`, `test_advance_endpoint_moves_only_when_running`. | Complete |
| RT-28 | Phase 6 brief | CORS/OPTIONS support for browser clients. | `api/asgi.py` `CORS_HEADERS`, `test_asgi_cors_and_options`. | Complete |
| RT-29 | Phase 6 brief | `reset` clears incident history. | `SimulationApi.reset`, `test_reset_clears_incident_history`. | Complete |
| RT-30 | Phase 6 brief | WebSocket sends a snapshot on connect and after mutating commands. | `api/asgi.py` `_websocket`/`_broadcast`, `test_websocket_snapshot_envelope`, `test_websocket_updates_after_mutating_http`. | Complete |
| RT-31 | Phase 6 brief | Control Room and Driver HUD routes rendering only backend state. | `web/src/App.tsx`, `pages/ControlRoom.tsx`, `pages/DriverHud.tsx`. | Complete |
| RT-32 | Phase 6 brief | Mine map using local x_m/y_m only, D01-D03 and B01-B03 markers. | `web/src/components/MineMap.tsx`. | Complete |
| RT-33 | Phase 6 brief | Fleet KPIs, telemetry (22 fields), safety, incident, and beacon panels. | `web/src/components/{TelemetryPanel,IncidentPanel,BeaconPanel}.tsx`, `pages/ControlRoom.tsx`. | Complete |
| RT-34 | Phase 6 brief | WebSocket live updates, reconnection, and freeze-on-disconnect. | `web/src/useSimulation.ts`. | Complete |
| RT-35 | Phase 6 brief | Mandatory simulated-twin and orientation banners on every screen. | `pages/ControlRoom.tsx`, `pages/DriverHud.tsx`, `components/TelemetryPanel.tsx`. | Complete |

## Deliberately deferred

Deferred behavior: physical V2I radio, durable/persistent storage beyond the
process lifetime, production server hosting/authentication, and any Phase 7/8
work. Phase 6 delivers the read-only control-room aggregation, WebSocket
streaming refinement, and the `web/` frontend; it does not add a second
frontend, a second simulation engine, or hardware I/O.
