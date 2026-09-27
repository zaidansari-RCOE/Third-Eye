"""Incident records for later phases; no incident processing exists yet."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from third_eye.domain.safety import HazardType, SafetyAction, SafetySeverity, SafetyZone


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class Incident:
    """Persistent simulated incident created solely from a Phase 4 decision."""
    incident_id: str
    vehicle_id: str
    timestamp_seconds: float
    created_timestamp_seconds: float
    severity: SafetySeverity
    hazard_type: HazardType
    title: str
    message: str
    triggering_rule: str
    telemetry_context: tuple[tuple[str, object], ...]
    safety_action: SafetyAction
    simulated_brake_active: bool
    status: IncidentStatus
    resolved_timestamp_seconds: float | None = None


# Backward-compatible Phase 1 definition retained as a vocabulary-only model.
@dataclass(frozen=True, slots=True)
class IncidentDefinition:
    incident_id: str
    hazard_type: HazardType
    zone: SafetyZone
    status: IncidentStatus
    description: str
