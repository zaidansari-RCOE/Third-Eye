from __future__ import annotations

import dataclasses
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.domain.telemetry import (
    DataOrigin,
    TELEMETRY_FIELD_NAMES,
    TelemetryEnvelope,
    TelemetrySnapshot,
)


EXPECTED_FIELDS = (
    "forward_lidar_cm", "rate_of_closure_mps", "thermal_temp_gradient",
    "human_detection_conf", "visual_fog_density_pct", "left_cliff_dist_cm",
    "right_cliff_dist_cm", "ground_loss_trigger", "pitch_angle_degrees",
    "roll_angle_degrees", "vehicle_velocity_kph", "motor_current_draw_ma",
    "core_temp_celsius", "batt_voltage_millivolts", "braking_pressure_psi",
    "runtime_seconds", "active_beacon_id", "beacon_rssi_dbm",
    "curve_speed_limit_kph", "hazard_warning_flag", "local_gps_lat_offset",
    "local_gps_lon_offset",
)


class TelemetryContractTests(unittest.TestCase):
    def test_contract_contains_exactly_22_fields_in_proposal_order(self) -> None:
        self.assertEqual(TELEMETRY_FIELD_NAMES, EXPECTED_FIELDS)
        self.assertEqual(len(TELEMETRY_FIELD_NAMES), 22)

    def test_snapshot_field_names_and_order_match_contract(self) -> None:
        self.assertEqual(
            tuple(field.name for field in dataclasses.fields(TelemetrySnapshot)),
            EXPECTED_FIELDS,
        )

    def test_envelope_defaults_to_simulated_origin(self) -> None:
        snapshot = TelemetrySnapshot(
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, "", 0.0, 0.0, False, 0.0, 0.0,
        )
        self.assertEqual(TelemetryEnvelope(snapshot).origin, DataOrigin.SIMULATED)
        self.assertEqual(tuple(snapshot.as_ordered_dict()), EXPECTED_FIELDS)

