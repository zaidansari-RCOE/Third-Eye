"""Fuse validated sensor records into the immutable Phase 1 TelemetrySnapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from third_eye.domain.telemetry import DataOrigin, TelemetryEnvelope, TelemetrySnapshot
from third_eye.simulation.validation import ValidatedSensorFrame


GROUND_LOSS_SIMULATION_DISTANCE_CM = 100.0


@dataclass(frozen=True, slots=True)
class FusedTelemetry:
    envelope: TelemetryEnvelope
    validation: ValidatedSensorFrame


def _value(frame: ValidatedSensorFrame, name: str, fallback: Any) -> Any:
    record = frame.reading(name)
    return record.reading.value if record.accepted else fallback


def fuse_telemetry(frame: ValidatedSensorFrame) -> FusedTelemetry:
    """Build exactly 22 fields; fallbacks are explicit simulation sentinels."""
    left_tof = _value(frame, "left_tof_distance_cm", -1.0)
    right_tof = _value(frame, "right_tof_distance_cm", -1.0)
    valid_tof = [value for value in (left_tof, right_tof) if value >= 0.0]
    telemetry = TelemetrySnapshot(
        forward_lidar_cm=_value(frame, "lidar_distance_cm", -1.0),
        rate_of_closure_mps=_value(frame, "lidar_rate_of_closure_mps", 0.0),
        thermal_temp_gradient=_value(frame, "thermal_temp_gradient", -1.0),
        human_detection_conf=_value(frame, "thermal_human_detection_conf", 0.0),
        visual_fog_density_pct=_value(frame, "visual_fog_density_pct", -1.0),
        left_cliff_dist_cm=left_tof,
        right_cliff_dist_cm=right_tof,
        ground_loss_trigger=bool(valid_tof and min(valid_tof) < GROUND_LOSS_SIMULATION_DISTANCE_CM),
        pitch_angle_degrees=_value(frame, "pitch_angle_degrees", 0.0),
        roll_angle_degrees=_value(frame, "roll_angle_degrees", 0.0),
        vehicle_velocity_kph=_value(frame, "vehicle_velocity_kph", 0.0),
        motor_current_draw_ma=_value(frame, "motor_current_draw_ma", -1.0),
        core_temp_celsius=_value(frame, "core_temp_celsius", -1.0),
        batt_voltage_millivolts=_value(frame, "batt_voltage_millivolts", -1.0),
        braking_pressure_psi=_value(frame, "braking_pressure_psi", -1.0),
        runtime_seconds=_value(frame, "runtime_seconds", 0.0),
        active_beacon_id=_value(frame, "active_beacon_id", "UNAVAILABLE"),
        beacon_rssi_dbm=_value(frame, "beacon_rssi_dbm", -999.0),
        curve_speed_limit_kph=_value(frame, "curve_speed_limit_kph", 0.0),
        hazard_warning_flag=_value(frame, "hazard_warning_flag", False),
        local_gps_lat_offset=_value(frame, "local_gps_lat_offset", 0.0),
        local_gps_lon_offset=_value(frame, "local_gps_lon_offset", 0.0),
    )
    return FusedTelemetry(TelemetryEnvelope(telemetry, DataOrigin.SIMULATED), frame)

