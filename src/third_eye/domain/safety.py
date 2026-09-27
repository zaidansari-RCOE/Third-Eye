"""Safety vocabulary only; Phase 1 contains no safety evaluation or control."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SafetyZone(StrEnum):
    """Driver-facing zones represented in the proposal mock-up."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class HazardType(StrEnum):
    FORWARD_COLLISION = "forward_collision"
    GROUND_LOSS = "ground_loss"
    CLIFF_PROXIMITY = "cliff_proximity"
    BEACON_HAZARD = "beacon_hazard"
    VISIBILITY = "visibility"
    SENSOR_FAILURE = "sensor_failure"
    BEACON_COMMUNICATION = "beacon_communication"


class SafetyResponse(StrEnum):
    DRIVER_WARNING = "driver_warning"
    DECELERATION_REQUEST = "deceleration_request"


class SafetySeverity(StrEnum):
    NORMAL = "NORMAL"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class SafetyAction(StrEnum):
    NO_ACTION = "NO_ACTION"
    CAUTION_ALERT = "CAUTION_ALERT"
    WARNING_ALERT = "WARNING_ALERT"
    EMERGENCY_OVERRIDE_SIMULATED = "EMERGENCY_OVERRIDE_SIMULATED"


@dataclass(frozen=True, slots=True)
class SafetyDefinition:
    """A descriptive safety condition, not an executable rule.

    Any trigger values introduced in a later software-only demo must be marked
    ``SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT``.
    """

    hazard_type: HazardType
    zone: SafetyZone
    response: SafetyResponse
    rationale: str


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    """Explainable simulated safety result; never a physical control command."""

    vehicle_id: str
    timestamp_seconds: float
    severity: SafetySeverity
    hazard_type: HazardType | None
    triggered_rules: tuple[str, ...]
    explanation: str
    action: SafetyAction
    simulated_brake_active: bool
    source_telemetry_reference: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SafetyEvent:
    event_id: str
    vehicle_id: str
    timestamp_seconds: float
    severity: SafetySeverity
    hazard_type: HazardType
    message: str
    triggered_rule: str
    active: bool = True
