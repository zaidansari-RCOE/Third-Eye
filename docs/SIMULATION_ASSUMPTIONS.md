# Simulation Assumptions

The proposal specifies intended hardware and high-level behavior, not numerical
engineering limits or a software simulation model. Every later value or behavior
in the following categories must carry this label:

> **SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT**

- Sensor ranges, noise, calibration, latency, update rates, and loss behavior
- Fog density generation and thermal/camera interpretation
- Collision, rate-of-closure, cliff, tilt, and hazard thresholds
- Warning-zone boundaries and alert escalation
- Braking/deceleration response and stopping behavior
- Vehicle movement, map, geofence, routes, cliffs, curves, and road geometry
- Beacon location, coverage, RSSI, packet loss, message timing, and handover
- Local GPS offset generation
- Dashboard/API transport cadence and data retention
- Sensor failure, stale-data, and fail-safe behaviors

## Mandatory orientation statement

> **SIMULATED VEHICLE/ENVIRONMENT ORIENTATION — NOT A PHYSICAL IMU READING.**

`pitch_angle_degrees` and `roll_angle_degrees` are retained because they are two
of the proposal's 22 telemetry fields. They do not create a physical IMU
requirement.

## Origin default

All telemetry envelopes default to `simulated`. Phase 3 derives telemetry from
the software-only Digital Twin and never presents it as hardware-originated.

## Phase 2 virtual-mine assumptions

The mine boundary, benches, roads, safe zones, cliff boundaries, blind curves,
intersections, routes, vehicle speeds, starting positions, and beacon positions
are fictional local coordinates in metres. They are not surveyed mine or GPS
coordinates. Route-loop behavior and the selected scenario-to-condition mapping
are also **SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT**.

Phase 2 scenario names establish qualitative simulated state only:

- `NORMAL`: no special condition.
- `DENSE_FOG`: dense-fog condition.
- `OBSTACLE`: obstacle-present condition.
- `CLIFF_EDGE`: cliff-edge condition.
- `V2I_HAZARD`: hazard broadcast enabled on simulated B02.
- `SENSOR_FAILURE`: simulated D02 marked sensor-degraded.
- `BEACON_FAILURE`: simulated B03 marked unavailable.

None creates telemetry, evaluates risk, sends warnings, creates incidents, or
brakes a vehicle.

## Phase 3 sensor and fusion assumptions

Every item below is a **SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT**:

- TF-Luna normal forward range is capped at 45,000 cm; a fictional `ROUTE-N`
  obstacle is positioned at local route progress 300 m.
- `DENSE_FOG` produces 95% visual fog versus 10% normal visual fog; thermal
  human-detection confidence is correspondingly 0.62 versus 0.92.
- `CLIFF_EDGE` places a fictional left-side drop-off at `ROUTE-N` local origin.
  Fusion sets `ground_loss_trigger` when a valid simulated ToF value is below
  100 cm. This is not a safety threshold.
- `V2I_HAZARD` selects B02 and supplies a simulated 15 kph curve advisory;
  `BEACON_FAILURE` selects unavailable B03.
- Simulated unavailable numeric values use `-1.0`, unavailable beacon RSSI uses
  `-999.0`, and unavailable beacon ID uses `UNAVAILABLE`. Validation records
  keep these from being mistaken for healthy sensor readings.
- Diagnostic current, temperature, voltage, braking pressure, RSSI attenuation,
  pitch, and roll formulas are deterministic demonstration formulas only.
- `SENSOR_FAILURE` makes the simulated TF-Luna reading invalid and stale. No
  physical sensor is disabled and no safety action follows.

Raw sensor frames carry source, simulation timestamp, validity, and stale state.
Validation rejects invalid, stale, timestamp-mismatched, and non-finite values
before fusion. Fusion then uses explicit unavailable sentinels rather than
silently treating failed data as valid.

## Phase 4 safety and braking assumptions

All values in `third_eye.safety.config.THRESHOLDS` are **SIMULATION ASSUMPTION —
NOT AN ENGINEERING LIMIT**. They centralize the fictional collision distance and
closure, cliff distance, fog density/confidence, weak RSSI, and 4 kph-per-second
deceleration values used for this demonstration.

The safety engine is deterministic and explainable: it evaluates fused
telemetry plus Phase 3 validation records, retains rule names and source fields,
then selects the highest severity among `NORMAL`, `CAUTION`, `WARNING`, and
`CRITICAL`. Critical forward-collision and ground-loss conditions produce
`EMERGENCY_OVERRIDE_SIMULATED`; Phase 2 movement then applies its deterministic
deceleration model when simulation time advances.

> **SIMULATED SAFETY ACTION — NO PHYSICAL BRAKE HARDWARE CONNECTED.**

Safety events are an active event projection for future control-room use. They
are not incidents and have no acknowledgement or resolution workflow.

## Phase 5 V2I and incident assumptions

The B01/B02/B03 defaults (30/20/30 kph), 300 m relevance range, road/next-road
association, RSSI formula, and dynamic updates are **SIMULATION ASSUMPTION — NOT
AN ENGINEERING LIMIT**. Relevance is selected deterministically from a vehicle's
current and next route segment, then geometric distance with beacon ID tie-break;
it is never random. B02 remains explicitly selected for the pre-existing
`V2I_HAZARD` scenario and B03 for `BEACON_FAILURE`.

Beacon failures mark the existing beacon communication unavailable; Phase 3
then emits its documented unavailable/stale V2I values instead of healthy data.
Speed limits and hazards can be changed through the backend API without a UI.

Incidents persist in the process only (**SIMULATION ASSUMPTION — NOT AN
ENGINEERING LIMIT**). One active incident is deduplicated by vehicle, selected
hazard type, and primary triggered rule. It is resolved automatically when that
condition clears or manually by API; a later recurrence creates a new incident.
Each incident preserves the ordered Telemetry22 context for a later black-box
replay phase.

## Phase 6 control-room and frontend assumptions

The default demo ticker rate (`DEFAULT_DEMO_TICK_HZ = 8.0`, overridable via
`THIRD_EYE_DEMO_TICK_HZ`) is a **SIMULATION ASSUMPTION — NOT AN ENGINEERING
LIMIT**: it is a display cadence for `create_demo_app()`, not a physical
control-loop rate, and it is disabled by default (and in every test) so it
never affects deterministic behavior.

The `web/` frontend performs no server-authoritative computation. It renders
`SimulationState`-derived snapshots as received; if it ever interpolates
between two received snapshots for smoother animation, that interpolation is
display-only and does not feed back into any decision, telemetry value, or
stored state. As of this handover the frontend does not perform such
interpolation at all — it renders each received snapshot directly.

Freezing the last snapshot on WebSocket disconnect, and the reconnect backoff
schedule in `web/src/useSimulation.ts`, are UI-layer conveniences and are also
**SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT**.
