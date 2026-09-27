"""Deterministic safety-event projection for future control-room consumers."""

from __future__ import annotations

from third_eye.domain.safety import SafetyDecision, SafetyEvent, SafetySeverity


def event_from_decision(decision: SafetyDecision) -> SafetyEvent | None:
    """Create one active event for non-normal decisions; no incident workflow exists."""
    if decision.severity is SafetySeverity.NORMAL or decision.hazard_type is None:
        return None
    return SafetyEvent(
        event_id=f"SIM-{decision.vehicle_id}-{decision.timestamp_seconds:.3f}-{decision.hazard_type.value}",
        vehicle_id=decision.vehicle_id,
        timestamp_seconds=decision.timestamp_seconds,
        severity=decision.severity,
        hazard_type=decision.hazard_type,
        message=decision.explanation,
        triggered_rule=decision.triggered_rules[0],
        active=True,
    )
