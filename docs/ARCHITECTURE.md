# Phase 5 Architecture

## Scope boundary

Phase 5 adds simulated V2I configuration and an in-memory incident lifecycle.
It has no physical-device access or UI.

```text
Simulation Clock
      v
Virtual Mine Topology
      v
Virtual Vehicles + Deterministic Routes + Virtual Beacons
      v
Deterministic Vehicle Movement
      v
ONE Authoritative SimulationState
      v
Simulated Sensor Frames
      v
Validation Records
      v
Fusion -> exact Telemetry22
      v
Deterministic Safety Engine
      v
Safety Decisions + Events + Simulated Brake State
      v
V2I Beacon Configuration + Proximity/RSSI Model
      v
Incident Manager + In-Memory History
      v
Existing Phase 2 Movement Authority
      v
REST / WebSocket simulated-state adapters
      v
Future sensor simulation, safety, and UI consumers
```

## Modules

- `third_eye.domain.telemetry`: exact ordered 22-field contract and data origin.
- `third_eye.domain.safety`: hazard, zone, and response vocabulary only.
- `third_eye.domain.v2i`: roadside-beacon message definitions only.
- `third_eye.domain.incidents`: future incident record shape only.
- `third_eye.adapters.contracts`: Python protocols for future Raspberry Pi 4,
  AMG8833, TF-Luna, left/right VL53L1X, Pi Camera, and ESP32 beacon adapters.
- `third_eye.api.contracts`: future transport response shapes only.
- `third_eye.simulation`: deterministic clock, fictional topology, fleet,
  routes, scenarios, beacons, and single-state service.
- `third_eye.api.simulation`: required REST route facade.
- `third_eye.api.asgi`: dependency-free ASGI HTTP/WebSocket adapter.
- `third_eye.simulation.sensors`: causal TF-Luna, AMG8833, left/right VL53L1X,
  camera context, diagnostics, V2I, and simulated orientation frames.
- `third_eye.simulation.validation`: reading validity, stale, timestamp, and
  finite-value validation.
- `third_eye.simulation.fusion`: validated readings to the exact Phase 1
  `TelemetrySnapshot` contract.
- `third_eye.simulation.telemetry`: the derived vehicle telemetry pipeline.
- `third_eye.safety.config`: centralized demonstration thresholds.
- `third_eye.safety.engine`: deterministic collision, cliff, visibility, V2I,
  and validation-failure evaluation.
- `third_eye.safety.events`: structured safety-event projection only.
- `third_eye.simulation.v2i`: route/road-associated beacon relevance and
  deterministic RSSI calculation.
- `third_eye.incidents.service`: safety-decision projection, deduplication,
  acknowledgement, resolution, and in-memory history.

## Hardware separation

Protocols describe future capabilities but no adapter implementation calls GPIO,
serial, I2C, UART, SPI, ESP-NOW, motors, or physical brakes. The default
telemetry origin is `simulated`; hardware data must be explicitly marked
`hardware` by a future adapter.

## Determinism and state ownership

`SimulationService` owns exactly one current immutable `SimulationState` per
process. Its clock advances only when explicitly started and advanced by a
caller. Position is calculated from route geometry, route progress, velocity,
and supplied simulation seconds. There is no random data and no wall-clock
movement. `reset()` restores the exact original paused state.

## Explicitly excluded from Phase 5

Implemented: deterministic sensor frames, validation, fusion, safety decisions,
events, simulated deceleration, V2I beacon state, and in-memory incident
lifecycle. Simulated: every sensor, diagnostic, beacon, orientation,
environment condition, threshold, and braking response. Not implemented:
thermal upscaling, physical alert hardware, physical V2I radio, durable
persistence, and every frontend.

**PHYSICAL HARDWARE CONNECTED = FALSE.**

**SIMULATED EMERGENCY BRAKING = SOFTWARE SIMULATION ONLY.** The movement engine
reduces speed by its configured simulation deceleration over elapsed simulation
time; it never accesses a motor or brake.

## Orientation clarification

`pitch_angle_degrees` and `roll_angle_degrees` remain in the mandatory proposal
telemetry contract. In this software-only prototype they mean:

> **SIMULATED VEHICLE/ENVIRONMENT ORIENTATION — NOT A PHYSICAL IMU READING.**

The proposal does not specify an IMU; no physical IMU requirement is created.

## Phase 6 addendum: control room, WebSocket streaming, and frontend

Phase 6 does not replace the diagram above; it adds a read-only view and a
transport/UI layer on top of the same `SimulationService`:

```text
ONE Authoritative SimulationState (unchanged)
      v
api/snapshot.py  — read-only control-room aggregation
      |  (per-vehicle telemetry + validation + safety, beacons,
      |   incidents, fleet KPIs; never mutates state, never advances time)
      v
api/asgi.py — dependency-free ASGI HTTP + WebSocket adapter
      |  (CORS/OPTIONS, REST dispatch, WebSocket snapshot-on-connect,
      |   snapshot-push-after-mutating-command, optional demo ticker)
      v
web/ — React (Vite + TypeScript) Control Room and Driver HUD
      (renders backend snapshots only; no local movement/sensor/
       safety/incident/RSSI/telemetry computation)
```

Additional modules:

- `third_eye.api.snapshot`: `health_payload`, `map_payload`,
  `build_control_room_snapshot`, and `control_room_message`. Pure read-model
  functions over the existing `SimulationApi`/`SimulationService`.
- `third_eye.api.asgi`: `SimulationAsgiApp` (ASGI `__call__` for `lifespan`,
  `http`, and `websocket` scopes) and `create_demo_app` (uvicorn factory).

No second simulation engine, no second mutable state, and no second WebSocket
protocol were introduced. `web/` is the only Phase 6 frontend; `frontend/` (an
older, alternative prototype) is unused and was not modified beyond adding a
short legacy notice in `frontend/README.md`.

**PHYSICAL HARDWARE CONNECTED = FALSE** remains true for Phase 6: the demo
ticker and every frontend value are driven exclusively by
`SimulationService.advance`, never by hardware or wall-clock sensor polling.
