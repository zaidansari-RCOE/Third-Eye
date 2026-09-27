"""Framework-neutral API facade for the deterministic simulation state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from third_eye.api.snapshot import build_control_room_snapshot, health_payload, map_payload
from third_eye.simulation.engine import SimulationService
from third_eye.simulation.models import Scenario, SimulationState
from third_eye.simulation.telemetry import TelemetryService
from third_eye.safety.events import event_from_decision
from third_eye.incidents.service import IncidentManager


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status_code: int
    body: dict[str, Any]


def state_payload(state: SimulationState) -> dict[str, Any]:
    """Serialize simulated state without exposing hardware or telemetry runtime."""

    return asdict(state)


class SimulationApi:
    """The five required REST operations; this class does not run a web server."""

    def __init__(self, simulation: SimulationService | None = None) -> None:
        self.simulation = simulation or SimulationService()
        self.telemetry = TelemetryService(self.simulation)
        self.incidents = IncidentManager(self.simulation)

    def get_state(self) -> ApiResponse:
        return ApiResponse(200, state_payload(self.simulation.state))

    def start(self) -> ApiResponse:
        return ApiResponse(200, state_payload(self.simulation.start()))

    def pause(self) -> ApiResponse:
        return ApiResponse(200, state_payload(self.simulation.pause()))

    def reset(self) -> ApiResponse:
        state = self.simulation.reset()
        self.incidents.clear()
        return ApiResponse(200, state_payload(state))

    def health(self) -> ApiResponse:
        return ApiResponse(200, health_payload())

    def control_room(self) -> ApiResponse:
        return ApiResponse(200, build_control_room_snapshot(self))

    def simulation_map(self) -> ApiResponse:
        return ApiResponse(200, map_payload(self))

    def advance(self, payload: dict[str, Any]) -> ApiResponse:
        seconds = payload.get("seconds")
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return ApiResponse(400, {"error": "seconds must be a non-negative number"})
        return ApiResponse(200, state_payload(self.simulation.advance(float(seconds))))

    def scenario(self, payload: dict[str, Any]) -> ApiResponse:
        try:
            scenario = Scenario(payload["scenario"])
        except (KeyError, TypeError, ValueError):
            return ApiResponse(400, {"error": "scenario must be one of: " + ", ".join(item.value for item in Scenario)})
        return ApiResponse(200, state_payload(self.simulation.select_scenario(scenario)))

    def vehicle_telemetry(self, vehicle_id: str) -> ApiResponse:
        try:
            result = self.telemetry.vehicle_telemetry(vehicle_id)
        except StopIteration:
            return ApiResponse(404, {"error": "vehicle not found"})
        return ApiResponse(
            200,
            {
                "vehicle_id": vehicle_id,
                "origin": result.fused.envelope.origin,
                "telemetry": result.fused.envelope.telemetry.as_ordered_dict(),
                "validation": {
                    item.reading.name: {"accepted": item.accepted, "reason": item.reason}
                    for item in result.validation.readings
                },
            },
        )

    def vehicle_safety(self, vehicle_id: str) -> ApiResponse:
        state = self.simulation.state
        decision = next((item for item in state.safety_decisions if item.vehicle_id == vehicle_id), None)
        if decision is None:
            # A paused initial state has no refreshed decision yet; evaluate via
            # the Phase 3 pipeline without changing vehicle movement or clock.
            result = self.telemetry.vehicle_telemetry(vehicle_id)
            from third_eye.safety.engine import evaluate_safety
            decision = evaluate_safety(vehicle_id, state.clock.elapsed_seconds, result.fused.envelope.telemetry, result.validation)
        if decision is None:
            return ApiResponse(404, {"error": "vehicle not found"})
        event = event_from_decision(decision)
        return ApiResponse(200, {"decision": asdict(decision), "event": asdict(event) if event else None})

    def beacon(self, beacon_id: str | None = None) -> ApiResponse:
        beacons = self.simulation.state.beacons
        if beacon_id is None:
            return ApiResponse(200, {"beacons": [asdict(item) for item in beacons]})
        item = next((beacon for beacon in beacons if beacon.beacon_id == beacon_id), None)
        return ApiResponse(200, asdict(item)) if item else ApiResponse(404, {"error": "beacon not found"})

    def update_beacon_speed(self, beacon_id: str, payload: dict[str, Any]) -> ApiResponse:
        value = payload.get("speed_limit_kph")
        if not isinstance(value, (int, float)) or value < 0:
            return ApiResponse(400, {"error": "speed_limit_kph must be a non-negative number"})
        try:
            state = self.simulation.update_beacon(beacon_id, speed_limit_kph=float(value))
        except KeyError:
            return ApiResponse(404, {"error": "beacon not found"})
        return ApiResponse(200, asdict(next(item for item in state.beacons if item.beacon_id == beacon_id)))

    def inject_beacon_hazard(self, beacon_id: str, payload: dict[str, Any]) -> ApiResponse:
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            return ApiResponse(400, {"error": "message must be a non-empty string"})
        try:
            state = self.simulation.update_beacon(beacon_id, hazard_active=True, hazard_message=message)
        except KeyError:
            return ApiResponse(404, {"error": "beacon not found"})
        return ApiResponse(200, asdict(next(item for item in state.beacons if item.beacon_id == beacon_id)))

    def clear_beacon_hazard(self, beacon_id: str) -> ApiResponse:
        try:
            state = self.simulation.update_beacon(beacon_id, hazard_active=False)
        except KeyError:
            return ApiResponse(404, {"error": "beacon not found"})
        return ApiResponse(200, asdict(next(item for item in state.beacons if item.beacon_id == beacon_id)))

    def beacon_failure(self, beacon_id: str, payload: dict[str, Any]) -> ApiResponse:
        failed = payload.get("failed")
        if not isinstance(failed, bool):
            return ApiResponse(400, {"error": "failed must be boolean"})
        try:
            state = self.simulation.set_beacon_failure(beacon_id, failed)
        except KeyError:
            return ApiResponse(404, {"error": "beacon not found"})
        return ApiResponse(200, asdict(next(item for item in state.beacons if item.beacon_id == beacon_id)))

    def incident_list(self, active_only: bool = False) -> ApiResponse:
        items = self.incidents.active() if active_only else self.incidents.recent()
        return ApiResponse(200, {"incidents": [asdict(item) for item in items]})

    def incident_action(self, incident_id: str, action: str) -> ApiResponse:
        try:
            incident = self.incidents.acknowledge(incident_id) if action == "acknowledge" else self.incidents.resolve(incident_id)
        except KeyError:
            return ApiResponse(404, {"error": "incident not found"})
        return ApiResponse(200, asdict(incident))

    def dispatch(self, method: str, path: str, payload: dict[str, Any] | None = None) -> ApiResponse:
        """Route the required Phase 2 endpoints for HTTP adapters and tests."""

        routes = {
            ("GET", "/api/health"): self.health,
            ("GET", "/api/simulation/state"): self.get_state,
            ("GET", "/api/simulation/control-room"): self.control_room,
            ("GET", "/api/simulation/map"): self.simulation_map,
            ("POST", "/api/simulation/start"): self.start,
            ("POST", "/api/simulation/pause"): self.pause,
            ("POST", "/api/simulation/reset"): self.reset,
        }
        handler = routes.get((method.upper(), path))
        if handler:
            return handler()
        if (method.upper(), path) == ("POST", "/api/simulation/scenario"):
            return self.scenario(payload or {})
        if (method.upper(), path) == ("POST", "/api/simulation/advance"):
            return self.advance(payload or {})
        path_parts = path.strip("/").split("/")
        if method.upper() == "GET" and len(path_parts) == 5 and path_parts[:3] == ["api", "simulation", "vehicles"] and path_parts[4] == "telemetry":
            return self.vehicle_telemetry(path_parts[3])
        if method.upper() == "GET" and len(path_parts) == 5 and path_parts[:3] == ["api", "simulation", "vehicles"] and path_parts[4] == "safety":
            return self.vehicle_safety(path_parts[3])
        if path_parts[:3] == ["api", "v2i", "beacons"]:
            if method.upper() == "GET" and len(path_parts) == 3:
                return self.beacon()
            if method.upper() == "GET" and len(path_parts) == 4:
                return self.beacon(path_parts[3])
            if len(path_parts) == 5 and path_parts[4] == "speed-limit" and method.upper() in ("PUT", "POST"):
                return self.update_beacon_speed(path_parts[3], payload or {})
            if len(path_parts) == 5 and path_parts[4] == "hazard":
                return self.inject_beacon_hazard(path_parts[3], payload or {}) if method.upper() == "POST" else self.clear_beacon_hazard(path_parts[3]) if method.upper() == "DELETE" else ApiResponse(404, {"error": "not found"})
            if len(path_parts) == 5 and path_parts[4] == "failure" and method.upper() == "POST":
                return self.beacon_failure(path_parts[3], payload or {})
        if path_parts[:2] == ["api", "incidents"]:
            if method.upper() == "GET" and len(path_parts) == 2:
                return self.incident_list()
            if method.upper() == "GET" and len(path_parts) == 3 and path_parts[2] == "active":
                return self.incident_list(True)
            if method.upper() == "GET" and len(path_parts) == 3:
                try:
                    return ApiResponse(200, asdict(self.incidents.get(path_parts[2])))
                except KeyError:
                    return ApiResponse(404, {"error": "incident not found"})
            if method.upper() == "POST" and len(path_parts) == 4 and path_parts[3] in ("acknowledge", "resolve"):
                return self.incident_action(path_parts[2], path_parts[3])
        return ApiResponse(404, {"error": "not found"})
