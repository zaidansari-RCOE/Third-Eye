"""Deterministic in-memory incident repository sourced from safety decisions."""

from __future__ import annotations

from dataclasses import replace

from third_eye.domain.incidents import Incident, IncidentStatus
from third_eye.domain.safety import SafetyDecision, SafetySeverity
from third_eye.simulation.engine import SimulationService
from third_eye.simulation.telemetry import TelemetryService


class IncidentManager:
    """Keeps history in memory and deduplicates one active condition per key."""

    def __init__(self, simulation: SimulationService) -> None:
        self._simulation = simulation
        self._telemetry = TelemetryService(simulation)
        self._history: list[Incident] = []
        self._next_id = 1

    @staticmethod
    def _key(decision: SafetyDecision) -> tuple[str, str, str]:
        return (decision.vehicle_id, decision.hazard_type.value if decision.hazard_type else "none", decision.triggered_rules[0] if decision.triggered_rules else "normal")

    def _new_incident(self, decision: SafetyDecision) -> Incident:
        telemetry = self._telemetry.vehicle_telemetry(decision.vehicle_id).fused.envelope.telemetry
        incident = Incident(
            incident_id=f"INC-{self._next_id:04d}",
            vehicle_id=decision.vehicle_id,
            timestamp_seconds=decision.timestamp_seconds,
            created_timestamp_seconds=decision.timestamp_seconds,
            severity=decision.severity,
            hazard_type=decision.hazard_type,  # type: ignore[arg-type]
            title=f"{decision.severity.value}: {decision.hazard_type.value.replace('_', ' ')}",
            message=decision.explanation,
            triggering_rule=decision.triggered_rules[0],
            telemetry_context=tuple(telemetry.as_ordered_dict().items()),
            safety_action=decision.action,
            simulated_brake_active=decision.simulated_brake_active,
            status=IncidentStatus.OPEN,
        )
        self._next_id += 1
        return incident

    def synchronize(self) -> tuple[Incident, ...]:
        """Project current safety state into incident lifecycle deterministically."""
        state = self._simulation.state
        decisions = tuple(item for item in state.safety_decisions if item.severity is not SafetySeverity.NORMAL and item.hazard_type is not None)
        active_keys = {self._key(item) for item in decisions}
        refreshed = []
        for incident in self._history:
            key = (incident.vehicle_id, incident.hazard_type.value, incident.triggering_rule)
            if incident.status is not IncidentStatus.RESOLVED and key not in active_keys:
                refreshed.append(replace(incident, status=IncidentStatus.RESOLVED, resolved_timestamp_seconds=state.clock.elapsed_seconds))
            else:
                refreshed.append(incident)
        self._history = refreshed
        existing = {(item.vehicle_id, item.hazard_type.value, item.triggering_rule) for item in self._history if item.status is not IncidentStatus.RESOLVED}
        for decision in decisions:
            if self._key(decision) not in existing:
                self._history.append(self._new_incident(decision))
                existing.add(self._key(decision))
        return tuple(self._history)

    def active(self) -> tuple[Incident, ...]:
        self.synchronize()
        return tuple(item for item in self._history if item.status is not IncidentStatus.RESOLVED)

    def recent(self) -> tuple[Incident, ...]:
        self.synchronize()
        return tuple(self._history)

    def get(self, incident_id: str) -> Incident:
        self.synchronize()
        return next(item for item in self._history if item.incident_id == incident_id)

    def acknowledge(self, incident_id: str) -> Incident:
        self.synchronize()
        for index, incident in enumerate(self._history):
            if incident.incident_id == incident_id:
                if incident.status is IncidentStatus.OPEN:
                    incident = replace(incident, status=IncidentStatus.ACKNOWLEDGED)
                    self._history[index] = incident
                return incident
        raise KeyError(incident_id)

    def resolve(self, incident_id: str) -> Incident:
        self.synchronize()
        for index, incident in enumerate(self._history):
            if incident.incident_id == incident_id:
                incident = replace(incident, status=IncidentStatus.RESOLVED, resolved_timestamp_seconds=self._simulation.state.clock.elapsed_seconds)
                self._history[index] = incident
                return incident
        raise KeyError(incident_id)

    def clear(self) -> None:
        """Drop in-memory history so a simulation reset does not leak incidents."""

        self._history = []
        self._next_id = 1
