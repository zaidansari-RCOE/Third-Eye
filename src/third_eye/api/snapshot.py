"""Phase 6 control-room snapshot: derived read-model over the existing twin.

This module never advances time, never mutates ``SimulationState``, and never
invents telemetry. KPIs and validation stay outside ``TelemetrySnapshot``.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from third_eye.api.contracts import HealthResponse
from third_eye.domain.safety import SafetySeverity, SafetyZone
from third_eye.domain.telemetry import DataOrigin, TELEMETRY_FIELD_NAMES
from third_eye.safety.engine import evaluate_safety
from third_eye.safety.events import event_from_decision


def safety_zone_for(severity: SafetySeverity) -> SafetyZone:
    """Project Phase 4 severity onto the proposal driver-facing zones."""

    if severity is SafetySeverity.NORMAL:
        return SafetyZone.GREEN
    if severity is SafetySeverity.CAUTION:
        return SafetyZone.YELLOW
    return SafetyZone.RED


def health_payload() -> dict[str, Any]:
    health = HealthResponse(service="third-eye", phase="6", hardware_connected=False)
    return asdict(health)


def map_payload(api: Any) -> dict[str, Any]:
    topology = api.simulation.state.topology
    return {
        "origin": DataOrigin.SIMULATED.value,
        "hardware_connected": False,
        "mine_area": asdict(topology.mine_area),
        "benches": [asdict(item) for item in topology.benches],
        "safe_zones": [asdict(item) for item in topology.safe_zones],
        "cliff_boundaries": [asdict(item) for item in topology.cliff_boundaries],
        "intersections": [asdict(item) for item in topology.intersections],
        "road_segments": [asdict(item) for item in topology.road_segments],
        "routes": [asdict(item) for item in topology.routes],
    }


def _decision_for_vehicle(api: Any, vehicle_id: str) -> Any:
    state = api.simulation.state
    existing = next((item for item in state.safety_decisions if item.vehicle_id == vehicle_id), None)
    if existing is not None:
        return existing
    result = api.telemetry.vehicle_telemetry(vehicle_id)
    return evaluate_safety(
        vehicle_id,
        state.clock.elapsed_seconds,
        result.fused.envelope.telemetry,
        result.validation,
    )


def _vehicle_snapshot(api: Any, vehicle: Any) -> dict[str, Any]:
    result = api.telemetry.vehicle_telemetry(vehicle.vehicle_id)
    decision = _decision_for_vehicle(api, vehicle.vehicle_id)
    event = event_from_decision(decision)
    telemetry = result.fused.envelope.telemetry.as_ordered_dict()
    return {
        "vehicle_id": vehicle.vehicle_id,
        "route_id": vehicle.route_id,
        "route_progress_m": vehicle.route_progress_m,
        "position": asdict(vehicle.position),
        "heading_degrees": vehicle.heading_degrees,
        "velocity_kph": vehicle.velocity_kph,
        "current_road_segment_id": vehicle.current_road_segment_id,
        "operating_state": vehicle.operating_state,
        "origin": result.fused.envelope.origin,
        "telemetry": telemetry,
        "validation": {
            item.reading.name: {"accepted": item.accepted, "reason": item.reason}
            for item in result.validation.readings
        },
        "safety": {
            **asdict(decision),
            "safety_zone": safety_zone_for(decision.severity),
            "event": asdict(event) if event else None,
        },
    }


def _kpis(state: Any, vehicles: list[dict[str, Any]], incidents_active: list[Any]) -> dict[str, Any]:
    speeds = [item["velocity_kph"] for item in vehicles]
    severity_counts = {item.value: 0 for item in SafetySeverity}
    braking = 0
    for item in vehicles:
        severity_counts[item["safety"]["severity"]] += 1
        if item["safety"]["simulated_brake_active"]:
            braking += 1
    return {
        "fleet_size": len(vehicles),
        "elapsed_seconds": state.clock.elapsed_seconds,
        "clock_status": state.clock.status,
        "scenario": state.scenario,
        "active_incident_count": len(incidents_active),
        "severity_counts": severity_counts,
        "simulated_braking_count": braking,
        "mean_velocity_kph": (sum(speeds) / len(speeds)) if speeds else 0.0,
        "max_velocity_kph": max(speeds) if speeds else 0.0,
        "origin": DataOrigin.SIMULATED.value,
        "hardware_connected": False,
    }


def build_control_room_snapshot(api: Any) -> dict[str, Any]:
    """Read-only aggregation for the control room and driver HUD.

    ``IncidentManager`` may update its in-memory history (existing Phase 5
    behaviour). ``SimulationService.state`` is not replaced.
    """

    state = api.simulation.state
    vehicles = [_vehicle_snapshot(api, vehicle) for vehicle in state.vehicles]
    incidents_recent = [asdict(item) for item in api.incidents.recent()]
    incidents_active = [item for item in incidents_recent if item["status"] != "resolved"]
    return {
        "origin": DataOrigin.SIMULATED.value,
        "hardware_connected": False,
        "clock": asdict(state.clock),
        "scenario": state.scenario,
        "conditions": asdict(state.conditions),
        "routes": [asdict(item) for item in state.topology.routes],
        "road_segments": [asdict(item) for item in state.topology.road_segments],
        "vehicles": vehicles,
        "beacons": [asdict(item) for item in state.beacons],
        "incidents_active": incidents_active,
        "incidents_recent": incidents_recent,
        "kpis": _kpis(state, vehicles, incidents_active),
        "telemetry_field_names": list(TELEMETRY_FIELD_NAMES),
    }


def control_room_message(api: Any) -> dict[str, Any]:
    return {
        "type": "control_room_snapshot",
        "origin": DataOrigin.SIMULATED.value,
        "payload": build_control_room_snapshot(api),
    }
