"""Deterministic movement and authoritative-state management for Phase 2."""

from __future__ import annotations

from dataclasses import replace
from math import atan2, degrees, hypot
from threading import RLock

from third_eye.simulation.models import (
    BeaconCommunicationState,
    BeaconOperatingState,
    ClockStatus,
    LocalCoordinate,
    MineTopology,
    RoadSegment,
    Scenario,
    ScenarioConditions,
    SimulationClock,
    SimulationState,
    VehicleOperatingState,
    VirtualBeacon,
    VirtualVehicle,
)
from third_eye.safety.config import THRESHOLDS
from third_eye.simulation.topology import build_virtual_mine_topology


def _segments_for_route(topology: MineTopology, route_id: str) -> tuple[RoadSegment, ...]:
    route = next(route for route in topology.routes if route.route_id == route_id)
    segments = {segment.segment_id: segment for segment in topology.road_segments}
    return tuple(segments[segment_id] for segment_id in route.segment_ids)


def _segment_length(segment: RoadSegment) -> float:
    return hypot(segment.end.x_m - segment.start.x_m, segment.end.y_m - segment.start.y_m)


def _route_length(topology: MineTopology, route_id: str) -> float:
    return sum(_segment_length(segment) for segment in _segments_for_route(topology, route_id))


def _route_location(topology: MineTopology, route_id: str, progress_m: float) -> tuple[LocalCoordinate, float, str]:
    segments = _segments_for_route(topology, route_id)
    route_length = _route_length(topology, route_id)
    local_progress = progress_m % route_length
    travelled = 0.0
    for segment in segments:
        length = _segment_length(segment)
        if local_progress <= travelled + length:
            fraction = (local_progress - travelled) / length
            dx = segment.end.x_m - segment.start.x_m
            dy = segment.end.y_m - segment.start.y_m
            return (
                LocalCoordinate(segment.start.x_m + dx * fraction, segment.start.y_m + dy * fraction),
                degrees(atan2(dy, dx)) % 360,
                segment.segment_id,
            )
        travelled += length
    # Float arithmetic can land exactly past the final segment boundary.
    first = segments[0]
    return first.start, degrees(atan2(first.end.y_m - first.start.y_m, first.end.x_m - first.start.x_m)) % 360, first.segment_id


def _vehicle_at_progress(
    topology: MineTopology,
    vehicle_id: str,
    route_id: str,
    speed_kph: float,
    progress_m: float,
    operating_state: VehicleOperatingState = VehicleOperatingState.ACTIVE,
) -> VirtualVehicle:
    position, heading, segment_id = _route_location(topology, route_id, progress_m)
    return VirtualVehicle(vehicle_id, route_id, progress_m % _route_length(topology, route_id), position, heading, speed_kph, segment_id, operating_state)


def conditions_for(scenario: Scenario) -> ScenarioConditions:
    """Map a scenario name to environment conditions, without safety behavior."""

    if scenario is Scenario.DENSE_FOG:
        return ScenarioConditions(dense_fog=True)
    if scenario is Scenario.OBSTACLE:
        return ScenarioConditions(obstacle_present=True)
    if scenario is Scenario.CLIFF_EDGE:
        return ScenarioConditions(cliff_edge_active=True)
    if scenario is Scenario.V2I_HAZARD:
        return ScenarioConditions(v2i_hazard_active=True)
    if scenario is Scenario.SENSOR_FAILURE:
        return ScenarioConditions(sensor_failure_vehicle_ids=("D02",))
    if scenario is Scenario.BEACON_FAILURE:
        return ScenarioConditions(beacon_failure_ids=("B03",))
    return ScenarioConditions()


def _apply_conditions(state: SimulationState, scenario: Scenario) -> SimulationState:
    conditions = conditions_for(scenario)
    vehicles = tuple(
        replace(
            vehicle,
            operating_state=(VehicleOperatingState.SENSOR_DEGRADED if vehicle.vehicle_id in conditions.sensor_failure_vehicle_ids else VehicleOperatingState.ACTIVE),
        )
        for vehicle in state.vehicles
    )
    beacons = tuple(
        replace(
            beacon,
            operating_state=(BeaconOperatingState.UNAVAILABLE if beacon.beacon_id in conditions.beacon_failure_ids else BeaconOperatingState.ACTIVE),
            communication_state=(BeaconCommunicationState.UNAVAILABLE if beacon.beacon_id in conditions.beacon_failure_ids else BeaconCommunicationState.AVAILABLE),
            hazard_broadcast_active=(conditions.v2i_hazard_active and beacon.beacon_id == "B02"),
            hazard_message=("Scenario V2I hazard" if conditions.v2i_hazard_active and beacon.beacon_id == "B02" else None),
            last_update_seconds=state.clock.elapsed_seconds,
        )
        for beacon in state.beacons
    )
    return replace(state, scenario=scenario, conditions=conditions, vehicles=vehicles, beacons=beacons)


def build_initial_state() -> SimulationState:
    """Create the exact reproducible initial snapshot for every reset."""

    topology = build_virtual_mine_topology()
    return SimulationState(
        clock=SimulationClock(),
        scenario=Scenario.NORMAL,
        conditions=ScenarioConditions(),
        topology=topology,
        vehicles=(
            _vehicle_at_progress(topology, "D01", "ROUTE-N", 24.0, 0.0),
            _vehicle_at_progress(topology, "D02", "ROUTE-S", 20.0, 90.0),
            _vehicle_at_progress(topology, "D03", "ROUTE-C", 18.0, 180.0),
        ),
        beacons=(
            VirtualBeacon("B01", LocalCoordinate(400, 0), "HN02", "SAFE-N", speed_limit_kph=30.0),
            VirtualBeacon("B02", LocalCoordinate(550, 50), "HC02", "SAFE-S", speed_limit_kph=20.0),
            VirtualBeacon("B03", LocalCoordinate(350, -100), "HS02", "SAFE-S", speed_limit_kph=30.0),
        ),
    )


def advance_state(state: SimulationState, seconds: float, braking_vehicle_ids: tuple[str, ...] = ()) -> SimulationState:
    """Advance a running state by an explicit amount of simulation time."""

    if seconds < 0:
        raise ValueError("Simulation advancement must be non-negative.")
    if state.clock.status is not ClockStatus.RUNNING or seconds == 0:
        return state
    vehicles = []
    for vehicle in state.vehicles:
        braking = vehicle.vehicle_id in braking_vehicle_ids
        final_speed = max(0.0, vehicle.velocity_kph - THRESHOLDS.simulated_brake_deceleration_kph_per_second * seconds) if braking else vehicle.velocity_kph
        average_speed = (vehicle.velocity_kph + final_speed) / 2.0 if braking else vehicle.velocity_kph
        vehicles.append(_vehicle_at_progress(state.topology, vehicle.vehicle_id, vehicle.route_id, final_speed, vehicle.route_progress_m + average_speed / 3.6 * seconds, vehicle.operating_state))
    return replace(state, clock=replace(state.clock, elapsed_seconds=state.clock.elapsed_seconds + seconds), vehicles=tuple(vehicles))


class SimulationService:
    """Owns the single authoritative simulation state for the process."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._initial_state = build_initial_state()
        self._state = self._initial_state

    @property
    def state(self) -> SimulationState:
        with self._lock:
            return self._state

    def start(self) -> SimulationState:
        with self._lock:
            self._state = replace(self._state, clock=replace(self._state.clock, status=ClockStatus.RUNNING))
            self._state = self._refresh_safety(self._state)
            return self._state

    def pause(self) -> SimulationState:
        with self._lock:
            self._state = replace(self._state, clock=replace(self._state.clock, status=ClockStatus.PAUSED))
            return self._state

    def reset(self) -> SimulationState:
        with self._lock:
            self._state = self._initial_state
            return self._state

    def select_scenario(self, scenario: Scenario) -> SimulationState:
        with self._lock:
            self._state = _apply_conditions(self._state, scenario)
            self._state = self._refresh_safety(self._state)
            return self._state

    def advance(self, seconds: float) -> SimulationState:
        with self._lock:
            self._state = self._refresh_safety(self._state)
            braking_ids = tuple(item.vehicle_id for item in self._state.safety_decisions if item.simulated_brake_active)
            self._state = advance_state(self._state, seconds, braking_ids)
            self._state = self._refresh_safety(self._state)
            return self._state

    def update_beacon(self, beacon_id: str, *, speed_limit_kph: float | None = None, hazard_active: bool | None = None, hazard_message: str | None = None, recovered: bool = False) -> SimulationState:
        """Update the existing virtual beacon; no physical radio is contacted."""
        with self._lock:
            updated, found = [], False
            for beacon in self._state.beacons:
                if beacon.beacon_id != beacon_id:
                    updated.append(beacon)
                    continue
                found = True
                updated.append(replace(
                    beacon,
                    speed_limit_kph=beacon.speed_limit_kph if speed_limit_kph is None else speed_limit_kph,
                    hazard_broadcast_active=beacon.hazard_broadcast_active if hazard_active is None else hazard_active,
                    hazard_message=(beacon.hazard_message if hazard_active is None else hazard_message) if hazard_active else None,
                    operating_state=BeaconOperatingState.ACTIVE if recovered else beacon.operating_state,
                    communication_state=BeaconCommunicationState.AVAILABLE if recovered else beacon.communication_state,
                    last_update_seconds=self._state.clock.elapsed_seconds,
                ))
            if not found:
                raise KeyError(beacon_id)
            self._state = replace(self._state, beacons=tuple(updated))
            self._state = self._refresh_safety(self._state)
            return self._state

    def set_beacon_failure(self, beacon_id: str, failed: bool) -> SimulationState:
        """Simulate beacon loss/recovery; unavailable beacons publish no fresh data."""
        if not failed:
            return self.update_beacon(beacon_id, recovered=True)
        with self._lock:
            updated, found = [], False
            for beacon in self._state.beacons:
                if beacon.beacon_id == beacon_id:
                    found = True
                    updated.append(replace(beacon, operating_state=BeaconOperatingState.UNAVAILABLE, communication_state=BeaconCommunicationState.UNAVAILABLE, last_update_seconds=self._state.clock.elapsed_seconds))
                else:
                    updated.append(beacon)
            if not found:
                raise KeyError(beacon_id)
            self._state = replace(self._state, beacons=tuple(updated))
            self._state = self._refresh_safety(self._state)
            return self._state

    @staticmethod
    def _refresh_safety(state: SimulationState) -> SimulationState:
        """Derive safety state from the existing Phase 3 pipeline without mutation."""
        from third_eye.safety.engine import evaluate_safety
        from third_eye.simulation.fusion import fuse_telemetry
        from third_eye.simulation.sensors import generate_sensor_frame
        from third_eye.simulation.validation import validate_sensor_frame

        decisions = []
        for vehicle in state.vehicles:
            validation = validate_sensor_frame(generate_sensor_frame(state, vehicle.vehicle_id))
            fused = fuse_telemetry(validation)
            decisions.append(evaluate_safety(vehicle.vehicle_id, state.clock.elapsed_seconds, fused.envelope.telemetry, validation))
        return replace(state, safety_decisions=tuple(decisions))
