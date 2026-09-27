"""Deterministic virtual V2I relevance and RSSI calculations."""

from __future__ import annotations

from math import hypot

from third_eye.simulation.models import LocalCoordinate, Scenario, SimulationState, VirtualBeacon, VirtualVehicle


V2I_RELEVANCE_RANGE_M = 300.0


def distance_m(a: LocalCoordinate, b: LocalCoordinate) -> float:
    return hypot(a.x_m - b.x_m, a.y_m - b.y_m)


def relevant_beacon(state: SimulationState, vehicle: VirtualVehicle) -> VirtualBeacon:
    """Select by route/road association, then distance; no random selection occurs."""
    if state.scenario is Scenario.V2I_HAZARD:
        return next(item for item in state.beacons if item.beacon_id == "B02")
    if state.scenario is Scenario.BEACON_FAILURE:
        return next(item for item in state.beacons if item.beacon_id == "B03")
    route = next(item for item in state.topology.routes if item.route_id == vehicle.route_id)
    current_index = route.segment_ids.index(vehicle.current_road_segment_id)
    relevant_segments = {vehicle.current_road_segment_id, route.segment_ids[(current_index + 1) % len(route.segment_ids)]}
    candidates = [item for item in state.beacons if item.associated_road_segment_id in relevant_segments]
    if not candidates:
        candidates = list(state.beacons)
    return min(candidates, key=lambda item: (distance_m(vehicle.position, item.position), item.beacon_id))


def simulated_rssi_dbm(distance_metres: float) -> float:
    """SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT."""
    return max(-95.0, -30.0 - distance_metres * 0.12)

