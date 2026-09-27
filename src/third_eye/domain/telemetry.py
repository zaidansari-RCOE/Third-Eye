"""The proposal-defined telemetry contract.

Do not add, remove, rename, or reorder telemetry fields without an explicit
proposal revision. Transport metadata belongs to an envelope, not this model.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Final


TELEMETRY_FIELD_NAMES: Final[tuple[str, ...]] = (
    "forward_lidar_cm",
    "rate_of_closure_mps",
    "thermal_temp_gradient",
    "human_detection_conf",
    "visual_fog_density_pct",
    "left_cliff_dist_cm",
    "right_cliff_dist_cm",
    "ground_loss_trigger",
    "pitch_angle_degrees",
    "roll_angle_degrees",
    "vehicle_velocity_kph",
    "motor_current_draw_ma",
    "core_temp_celsius",
    "batt_voltage_millivolts",
    "braking_pressure_psi",
    "runtime_seconds",
    "active_beacon_id",
    "beacon_rssi_dbm",
    "curve_speed_limit_kph",
    "hazard_warning_flag",
    "local_gps_lat_offset",
    "local_gps_lon_offset",
)


class DataOrigin(StrEnum):
    """Source classification that keeps simulation separate from hardware."""

    SIMULATED = "simulated"
    HARDWARE = "hardware"


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    """Exactly the 22 proposal-defined real-time telemetry fields, in order.

    ``pitch_angle_degrees`` and ``roll_angle_degrees`` are simulated vehicle/
    environment orientation values in this prototype. They are not physical IMU
    readings or an implication that an IMU is required by the proposal.
    """

    forward_lidar_cm: float
    rate_of_closure_mps: float
    thermal_temp_gradient: float
    human_detection_conf: float
    visual_fog_density_pct: float
    left_cliff_dist_cm: float
    right_cliff_dist_cm: float
    ground_loss_trigger: bool
    pitch_angle_degrees: float
    roll_angle_degrees: float
    vehicle_velocity_kph: float
    motor_current_draw_ma: float
    core_temp_celsius: float
    batt_voltage_millivolts: float
    braking_pressure_psi: float
    runtime_seconds: float
    active_beacon_id: str
    beacon_rssi_dbm: float
    curve_speed_limit_kph: float
    hazard_warning_flag: bool
    local_gps_lat_offset: float
    local_gps_lon_offset: float

    def as_ordered_dict(self) -> OrderedDict[str, object]:
        """Return the contract values in the mandated proposal order."""

        values = asdict(self)
        return OrderedDict((field, values[field]) for field in TELEMETRY_FIELD_NAMES)


@dataclass(frozen=True, slots=True)
class TelemetryEnvelope:
    """Transport-neutral telemetry envelope; the default is always simulation."""

    telemetry: TelemetrySnapshot
    origin: DataOrigin = DataOrigin.SIMULATED

