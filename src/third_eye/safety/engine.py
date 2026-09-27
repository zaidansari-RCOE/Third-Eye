"""Explainable deterministic safety rules over fused simulated telemetry."""

from __future__ import annotations

from dataclasses import dataclass

from third_eye.domain.safety import HazardType, SafetyAction, SafetyDecision, SafetySeverity
from third_eye.domain.telemetry import TelemetrySnapshot
from third_eye.safety.config import THRESHOLDS
from third_eye.simulation.validation import ValidatedSensorFrame


@dataclass(frozen=True, slots=True)
class _Risk:
    severity: SafetySeverity
    hazard: HazardType
    rule: str
    explanation: str
    fields: tuple[str, ...]


_RANK = {SafetySeverity.NORMAL: 0, SafetySeverity.CAUTION: 1, SafetySeverity.WARNING: 2, SafetySeverity.CRITICAL: 3}


def _collision(telemetry: TelemetrySnapshot) -> _Risk | None:
    if telemetry.forward_lidar_cm < 0:
        return None
    fields = ("forward_lidar_cm", "rate_of_closure_mps", "vehicle_velocity_kph")
    if telemetry.forward_lidar_cm <= THRESHOLDS.collision_critical_distance_cm and telemetry.rate_of_closure_mps > 0:
        return _Risk(SafetySeverity.CRITICAL, HazardType.FORWARD_COLLISION, "collision_critical_distance_and_closure", "Simulated forward distance is inside the configured critical zone while closure is positive.", fields)
    if telemetry.forward_lidar_cm <= THRESHOLDS.collision_warning_distance_cm or (telemetry.rate_of_closure_mps >= THRESHOLDS.collision_closure_warning_mps and telemetry.vehicle_velocity_kph > 0):
        return _Risk(SafetySeverity.WARNING, HazardType.FORWARD_COLLISION, "collision_reduced_distance_or_closure", "Simulated forward distance or closing rate indicates increased collision risk.", fields)
    return None


def _cliff(telemetry: TelemetrySnapshot) -> _Risk | None:
    fields = ("left_cliff_dist_cm", "right_cliff_dist_cm", "ground_loss_trigger", "pitch_angle_degrees", "roll_angle_degrees")
    if telemetry.ground_loss_trigger:
        return _Risk(SafetySeverity.CRITICAL, HazardType.GROUND_LOSS, "ground_loss_trigger", "Simulated ground-loss telemetry is active.", fields)
    valid = [item for item in (telemetry.left_cliff_dist_cm, telemetry.right_cliff_dist_cm) if item >= 0]
    if valid and min(valid) <= THRESHOLDS.cliff_warning_distance_cm:
        return _Risk(SafetySeverity.WARNING, HazardType.CLIFF_PROXIMITY, "cliff_reduced_distance", "Simulated ToF edge distance is below the configured warning distance.", fields)
    return None


def _visibility(telemetry: TelemetrySnapshot) -> _Risk | None:
    fields = ("visual_fog_density_pct", "human_detection_conf", "forward_lidar_cm")
    if telemetry.visual_fog_density_pct >= THRESHOLDS.fog_warning_density_pct and telemetry.human_detection_conf < THRESHOLDS.fog_low_confidence:
        return _Risk(SafetySeverity.WARNING, HazardType.VISIBILITY, "fog_warning_density_and_confidence", "Simulated visual fog is high and simulated detection confidence is reduced.", fields)
    if telemetry.visual_fog_density_pct >= THRESHOLDS.fog_caution_density_pct:
        return _Risk(SafetySeverity.CAUTION, HazardType.VISIBILITY, "fog_caution_density", "Simulated visual fog exceeds the configured caution level.", fields)
    return None


def _v2i(telemetry: TelemetrySnapshot) -> _Risk | None:
    fields = ("active_beacon_id", "beacon_rssi_dbm", "curve_speed_limit_kph", "hazard_warning_flag", "vehicle_velocity_kph")
    if telemetry.active_beacon_id == "UNAVAILABLE":
        return _Risk(SafetySeverity.WARNING, HazardType.BEACON_COMMUNICATION, "beacon_unavailable", "Simulated roadside-beacon communication is unavailable.", fields)
    if telemetry.hazard_warning_flag and telemetry.curve_speed_limit_kph > 0 and telemetry.vehicle_velocity_kph > telemetry.curve_speed_limit_kph:
        return _Risk(SafetySeverity.WARNING, HazardType.BEACON_HAZARD, "beacon_hazard_speed_limit_exceeded", "Simulated beacon hazard is active and vehicle speed exceeds its simulated advisory.", fields)
    if telemetry.hazard_warning_flag:
        return _Risk(SafetySeverity.CAUTION, HazardType.BEACON_HAZARD, "beacon_hazard_active", "Simulated beacon hazard broadcast is active.", fields)
    if telemetry.beacon_rssi_dbm <= THRESHOLDS.v2i_weak_rssi_dbm:
        return _Risk(SafetySeverity.CAUTION, HazardType.BEACON_COMMUNICATION, "beacon_weak_signal", "Simulated beacon RSSI is weak.", fields)
    return None


def _sensor_failure(validation: ValidatedSensorFrame) -> _Risk | None:
    rejected = tuple(item.reading.name for item in validation.readings if not item.accepted)
    if not rejected:
        return None
    severity = SafetySeverity.CRITICAL if "lidar_distance_cm" in rejected and "left_tof_distance_cm" in rejected else SafetySeverity.WARNING
    return _Risk(severity, HazardType.SENSOR_FAILURE, "sensor_validation_rejected", f"Simulated validation rejected: {', '.join(rejected)}.", rejected)


def evaluate_safety(vehicle_id: str, timestamp_seconds: float, telemetry: TelemetrySnapshot, validation: ValidatedSensorFrame) -> SafetyDecision:
    """Evaluate all rules deterministically; ties retain deterministic rule order."""
    risks = tuple(item for item in (_collision(telemetry), _cliff(telemetry), _visibility(telemetry), _v2i(telemetry), _sensor_failure(validation)) if item)
    if not risks:
        return SafetyDecision(vehicle_id, timestamp_seconds, SafetySeverity.NORMAL, None, (), "No simulated safety rule is active.", SafetyAction.NO_ACTION, False, ())
    selected = max(risks, key=lambda item: _RANK[item.severity])
    all_rules = tuple(item.rule for item in risks)
    if selected.severity is SafetySeverity.CRITICAL and selected.hazard in (HazardType.FORWARD_COLLISION, HazardType.GROUND_LOSS):
        action = SafetyAction.EMERGENCY_OVERRIDE_SIMULATED
        brake_active = True
    elif selected.severity is SafetySeverity.WARNING:
        action = SafetyAction.WARNING_ALERT
        brake_active = False
    else:
        action = SafetyAction.CAUTION_ALERT
        brake_active = False
    return SafetyDecision(vehicle_id, timestamp_seconds, selected.severity, selected.hazard, all_rules, selected.explanation, action, brake_active, selected.fields)

