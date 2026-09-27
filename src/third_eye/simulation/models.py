"""Immutable domain models for the deterministic virtual mine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from third_eye.domain.safety import SafetyDecision


class ClockStatus(StrEnum):
    PAUSED = "paused"
    RUNNING = "running"


class VehicleOperatingState(StrEnum):
    ACTIVE = "active"
    SENSOR_DEGRADED = "sensor_degraded"


class BeaconOperatingState(StrEnum):
    ACTIVE = "active"
    UNAVAILABLE = "unavailable"


class BeaconCommunicationState(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class Scenario(StrEnum):
    NORMAL = "NORMAL"
    DENSE_FOG = "DENSE_FOG"
    OBSTACLE = "OBSTACLE"
    CLIFF_EDGE = "CLIFF_EDGE"
    V2I_HAZARD = "V2I_HAZARD"
    SENSOR_FAILURE = "SENSOR_FAILURE"
    BEACON_FAILURE = "BEACON_FAILURE"


@dataclass(frozen=True, slots=True)
class LocalCoordinate:
    """Fictional local-mine coordinate in metres; this is not GPS data."""

    x_m: float
    y_m: float


@dataclass(frozen=True, slots=True)
class MineArea:
    mine_id: str
    name: str
    boundary: tuple[LocalCoordinate, ...]


@dataclass(frozen=True, slots=True)
class Bench:
    bench_id: str
    name: str
    boundary: tuple[LocalCoordinate, ...]


@dataclass(frozen=True, slots=True)
class SafeZone:
    zone_id: str
    name: str
    boundary: tuple[LocalCoordinate, ...]


@dataclass(frozen=True, slots=True)
class CliffBoundary:
    boundary_id: str
    name: str
    start: LocalCoordinate
    end: LocalCoordinate


@dataclass(frozen=True, slots=True)
class Intersection:
    intersection_id: str
    name: str
    coordinate: LocalCoordinate
    is_blind_curve: bool


@dataclass(frozen=True, slots=True)
class RoadSegment:
    segment_id: str
    name: str
    start: LocalCoordinate
    end: LocalCoordinate
    associated_zone_id: str
    is_blind_curve: bool = False


@dataclass(frozen=True, slots=True)
class RouteDefinition:
    route_id: str
    name: str
    segment_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MineTopology:
    mine_area: MineArea
    benches: tuple[Bench, ...]
    safe_zones: tuple[SafeZone, ...]
    cliff_boundaries: tuple[CliffBoundary, ...]
    intersections: tuple[Intersection, ...]
    road_segments: tuple[RoadSegment, ...]
    routes: tuple[RouteDefinition, ...]


@dataclass(frozen=True, slots=True)
class VirtualVehicle:
    vehicle_id: str
    route_id: str
    route_progress_m: float
    position: LocalCoordinate
    heading_degrees: float
    velocity_kph: float
    current_road_segment_id: str
    operating_state: VehicleOperatingState = VehicleOperatingState.ACTIVE


@dataclass(frozen=True, slots=True)
class VirtualBeacon:
    beacon_id: str
    position: LocalCoordinate
    associated_road_segment_id: str
    associated_zone_id: str
    operating_state: BeaconOperatingState = BeaconOperatingState.ACTIVE
    communication_state: BeaconCommunicationState = BeaconCommunicationState.AVAILABLE
    hazard_broadcast_active: bool = False
    speed_limit_kph: float = 30.0
    hazard_message: str | None = None
    last_update_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class ScenarioConditions:
    """Scenario state only. It must not make safety decisions or actuate a vehicle."""

    dense_fog: bool = False
    obstacle_present: bool = False
    cliff_edge_active: bool = False
    v2i_hazard_active: bool = False
    sensor_failure_vehicle_ids: tuple[str, ...] = ()
    beacon_failure_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SimulationClock:
    elapsed_seconds: float = 0.0
    status: ClockStatus = ClockStatus.PAUSED


@dataclass(frozen=True, slots=True)
class SimulationState:
    """The one authoritative snapshot consumed by all future simulation phases."""

    clock: SimulationClock
    scenario: Scenario
    conditions: ScenarioConditions
    topology: MineTopology
    vehicles: tuple[VirtualVehicle, ...]
    beacons: tuple[VirtualBeacon, ...]
    safety_decisions: tuple[SafetyDecision, ...] = ()
