from __future__ import annotations

import dataclasses
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.simulation import SimulationApi
from third_eye.domain.telemetry import TELEMETRY_FIELD_NAMES
from third_eye.simulation.engine import SimulationService
from third_eye.simulation.models import Scenario
from third_eye.simulation.sensors import SensorReading, SensorSource, generate_sensor_frame
from third_eye.simulation.telemetry import TelemetryService
from third_eye.simulation.validation import validate_reading


class SensorTelemetryPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.simulation = SimulationService()
        self.telemetry = TelemetryService(self.simulation)

    def snapshot(self):
        return self.telemetry.vehicle_telemetry("D01").fused.envelope.telemetry

    def test_sensor_frame_generation_contains_simulated_sources_and_timestamp(self) -> None:
        frame = generate_sensor_frame(self.simulation.state, "D01")
        self.assertGreaterEqual(len(frame.readings), 20)
        self.assertTrue(all(item.source.value.startswith("simulated_") for item in frame.readings))
        self.assertTrue(all(item.simulation_time_seconds == 0.0 for item in frame.readings))

    def test_validation_rejects_invalid_stale_and_mismatched_readings(self) -> None:
        reading = SensorReading("test", SensorSource.TF_LUNA_LIDAR, 1.0, 0.0, valid=False, stale=True)
        result = validate_reading(reading, 0.0)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "sensor_invalid")
        self.assertEqual(validate_reading(SensorReading("test", SensorSource.CAMERA, 1.0, 1.0), 0.0).reason, "timestamp_mismatch")

    def test_fusion_preserves_exact_22_names_count_and_order(self) -> None:
        telemetry = self.snapshot()
        self.assertEqual(tuple(field.name for field in dataclasses.fields(telemetry)), TELEMETRY_FIELD_NAMES)
        self.assertEqual(tuple(telemetry.as_ordered_dict()), TELEMETRY_FIELD_NAMES)
        self.assertEqual(len(telemetry.as_ordered_dict()), 22)

    def test_sensor_values_are_deterministic_for_same_state(self) -> None:
        self.assertEqual(self.snapshot(), self.snapshot())
        twin = SimulationService()
        self.assertEqual(self.snapshot(), TelemetryService(twin).vehicle_telemetry("D01").fused.envelope.telemetry)

    def test_dense_fog_causally_changes_visual_fog_and_camera_context(self) -> None:
        normal = self.snapshot()
        self.simulation.select_scenario(Scenario.DENSE_FOG)
        fog = self.snapshot()
        self.assertGreater(fog.visual_fog_density_pct, normal.visual_fog_density_pct)
        self.assertLess(fog.human_detection_conf, normal.human_detection_conf)

    def test_obstacle_causally_reduces_lidar_and_increases_closure(self) -> None:
        normal = self.snapshot()
        self.simulation.select_scenario(Scenario.OBSTACLE)
        obstacle = self.snapshot()
        self.assertLess(obstacle.forward_lidar_cm, normal.forward_lidar_cm)
        self.assertGreater(obstacle.rate_of_closure_mps, normal.rate_of_closure_mps)

    def test_cliff_edge_causally_changes_tof_and_ground_loss(self) -> None:
        normal = self.snapshot()
        self.simulation.select_scenario(Scenario.CLIFF_EDGE)
        cliff = self.snapshot()
        self.assertLess(cliff.left_cliff_dist_cm, normal.left_cliff_dist_cm)
        self.assertTrue(cliff.ground_loss_trigger)

    def test_v2i_hazard_causally_changes_beacon_telemetry(self) -> None:
        normal = self.snapshot()
        self.simulation.select_scenario(Scenario.V2I_HAZARD)
        hazard = self.snapshot()
        self.assertTrue(hazard.hazard_warning_flag)
        self.assertEqual(hazard.active_beacon_id, "B02")
        self.assertNotEqual(hazard.curve_speed_limit_kph, normal.curve_speed_limit_kph)

    def test_sensor_and_beacon_failures_are_explicit_in_validation_and_fusion(self) -> None:
        self.simulation.select_scenario(Scenario.SENSOR_FAILURE)
        sensor_failure = self.telemetry.vehicle_telemetry("D01")
        self.assertFalse(sensor_failure.validation.reading("lidar_distance_cm").accepted)
        self.assertEqual(sensor_failure.fused.envelope.telemetry.forward_lidar_cm, -1.0)
        self.simulation.select_scenario(Scenario.BEACON_FAILURE)
        beacon_failure = self.telemetry.vehicle_telemetry("D01")
        self.assertFalse(beacon_failure.validation.reading("active_beacon_id").accepted)
        self.assertEqual(beacon_failure.fused.envelope.telemetry.active_beacon_id, "UNAVAILABLE")

    def test_orientation_is_simulated_not_a_physical_imu(self) -> None:
        frame = generate_sensor_frame(self.simulation.state, "D01")
        self.assertEqual(frame.reading("pitch_angle_degrees").source, SensorSource.ORIENTATION)
        self.assertEqual(frame.reading("roll_angle_degrees").source, SensorSource.ORIENTATION)

    def test_all_phase_three_scenarios_generate_telemetry(self) -> None:
        for scenario in Scenario:
            self.simulation.select_scenario(scenario)
            self.assertEqual(len(self.snapshot().as_ordered_dict()), 22)

    def test_telemetry_api_contract_exposes_only_simulated_origin(self) -> None:
        response = SimulationApi(self.simulation).dispatch("GET", "/api/simulation/vehicles/D01/telemetry")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["origin"], "simulated")
        self.assertEqual(tuple(response.body["telemetry"]), TELEMETRY_FIELD_NAMES)

