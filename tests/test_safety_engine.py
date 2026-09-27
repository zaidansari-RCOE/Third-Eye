from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.simulation import SimulationApi
from third_eye.domain.safety import SafetyAction, SafetySeverity
from third_eye.safety.config import THRESHOLDS
from third_eye.simulation.engine import SimulationService
from third_eye.simulation.models import Scenario
from third_eye.simulation.telemetry import TelemetryService


class SafetyEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SimulationService()
        self.telemetry = TelemetryService(self.service)

    def decision(self, vehicle_id: str = "D01"):
        self.service.start()
        return next(item for item in self.service.state.safety_decisions if item.vehicle_id == vehicle_id)

    def test_normal_produces_normal_decision(self) -> None:
        decision = self.decision()
        self.assertEqual(decision.severity, SafetySeverity.NORMAL)
        self.assertEqual(decision.action, SafetyAction.NO_ACTION)

    def test_obstacle_increases_collision_risk_and_becomes_critical(self) -> None:
        self.service.select_scenario(Scenario.OBSTACLE)
        self.service.start()
        self.service.advance(44)
        decision = next(item for item in self.service.state.safety_decisions if item.vehicle_id == "D01")
        self.assertEqual(decision.severity, SafetySeverity.CRITICAL)
        self.assertEqual(decision.action, SafetyAction.EMERGENCY_OVERRIDE_SIMULATED)
        self.assertIn("collision_critical_distance_and_closure", decision.triggered_rules)

    def test_simulated_braking_reduces_speed_in_phase_two_movement_path(self) -> None:
        self.service.select_scenario(Scenario.OBSTACLE)
        self.service.start()
        self.service.advance(44)
        speed_before = self.service.state.vehicles[0].velocity_kph
        self.assertTrue(self.service.state.safety_decisions[0].simulated_brake_active)
        self.service.advance(2)
        self.assertLess(self.service.state.vehicles[0].velocity_kph, speed_before)

    def test_cliff_edge_is_critical_and_activates_simulated_override(self) -> None:
        self.service.select_scenario(Scenario.CLIFF_EDGE)
        decision = self.decision()
        self.assertEqual(decision.severity, SafetySeverity.CRITICAL)
        self.assertTrue(decision.simulated_brake_active)
        self.assertEqual(decision.hazard_type.value, "ground_loss")

    def test_fog_v2i_sensor_and_beacon_scenarios_are_detected(self) -> None:
        expected = (
            (Scenario.DENSE_FOG, SafetySeverity.WARNING),
            (Scenario.V2I_HAZARD, SafetySeverity.WARNING),
            (Scenario.SENSOR_FAILURE, SafetySeverity.WARNING),
            (Scenario.BEACON_FAILURE, SafetySeverity.WARNING),
        )
        for scenario, severity in expected:
            service = SimulationService()
            service.select_scenario(scenario)
            service.start()
            decision = next(item for item in service.state.safety_decisions if item.vehicle_id == "D01")
            self.assertEqual(decision.severity, severity)

    def test_v2i_speed_limit_violation_rule_is_explainable(self) -> None:
        self.service.select_scenario(Scenario.V2I_HAZARD)
        decision = self.decision()
        self.assertIn("beacon_hazard_speed_limit_exceeded", decision.triggered_rules)
        self.assertIn("speed exceeds", decision.explanation)

    def test_decisions_are_deterministic_for_same_telemetry(self) -> None:
        first, second = SimulationService(), SimulationService()
        first.select_scenario(Scenario.DENSE_FOG); second.select_scenario(Scenario.DENSE_FOG)
        first.start(); second.start()
        self.assertEqual(first.state.safety_decisions, second.state.safety_decisions)

    def test_thresholds_are_centralized(self) -> None:
        self.assertGreater(THRESHOLDS.collision_critical_distance_cm, 0)
        self.assertGreater(THRESHOLDS.simulated_brake_deceleration_kph_per_second, 0)

    def test_safety_api_and_event_are_structured(self) -> None:
        api = SimulationApi(self.service)
        self.service.select_scenario(Scenario.CLIFF_EDGE)
        self.service.start()
        response = api.dispatch("GET", "/api/simulation/vehicles/D01/safety")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["decision"]["severity"], "CRITICAL")
        self.assertTrue(response.body["event"]["active"])

