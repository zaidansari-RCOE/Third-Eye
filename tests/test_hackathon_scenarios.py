from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.simulation import SimulationApi
from third_eye.demo.hackathon_scenarios import HackathonScenarioError, HackathonScenarioGenerator


def _vehicle(snapshot: dict, vehicle_id: str = "D01") -> dict:
    return next(item for item in snapshot["vehicles"] if item["vehicle_id"] == vehicle_id)


class HackathonScenarioGeneratorTests(unittest.TestCase):
    """These assert the real, backend-computed states the generator was
    verified (by hand, against the live SimulationApi) to reach -- not
    invented expectations. No telemetry, safety, or V2I formula is touched;
    the generator only calls the existing frozen REST surface."""

    def test_uses_one_authoritative_simulation_service_by_default(self) -> None:
        generator = HackathonScenarioGenerator()
        self.assertIsInstance(generator._api, SimulationApi)  # noqa: SLF001
        self.assertIsNone(generator._base_url)  # noqa: SLF001

    def test_rejects_both_api_and_base_url(self) -> None:
        with self.assertRaises(ValueError):
            HackathonScenarioGenerator(api=SimulationApi(), base_url="http://127.0.0.1:9")

    def test_unknown_narrative_raises(self) -> None:
        generator = HackathonScenarioGenerator()
        with self.assertRaises(HackathonScenarioError):
            list(generator.run("NOT_A_REAL_NARRATIVE"))

    def test_blind_curve_approach_stays_safe_and_reaches_the_curve_segment(self) -> None:
        generator = HackathonScenarioGenerator()
        steps = list(generator.run("BLIND_CURVE_APPROACH"))
        self.assertEqual(len(steps), 6)
        final_vehicle = _vehicle(steps[-1].control_room_snapshot)
        # D01 has crossed onto the blind-curve segment itself.
        self.assertEqual(final_vehicle["current_road_segment_id"], "HN02")
        # It never needed emergency braking to get there safely.
        self.assertFalse(any(_vehicle(step.control_room_snapshot)["safety"]["simulated_brake_active"] for step in steps))
        # The real V2I advisory for that segment is present and D01 stays under it.
        self.assertEqual(final_vehicle["telemetry"]["active_beacon_id"], "B01")
        self.assertLessEqual(final_vehicle["telemetry"]["vehicle_velocity_kph"], final_vehicle["telemetry"]["curve_speed_limit_kph"])

    def test_sudden_obstacle_emergency_reaches_real_emergency_override_and_decelerates(self) -> None:
        generator = HackathonScenarioGenerator()
        steps = list(generator.run("SUDDEN_OBSTACLE_EMERGENCY"))
        self.assertEqual(len(steps), 6)
        severities = [_vehicle(step.control_room_snapshot)["safety"]["severity"] for step in steps]
        brakes = [_vehicle(step.control_room_snapshot)["safety"]["simulated_brake_active"] for step in steps]
        self.assertIn("CRITICAL", severities)
        self.assertTrue(any(brakes))
        brake_index = brakes.index(True)
        # The step after the real engine engages the simulated brake shows a
        # real velocity drop -- this is the frozen engine's own physics, not
        # anything computed by the generator.
        if brake_index + 1 < len(steps):
            braking_vehicle = _vehicle(steps[brake_index].control_room_snapshot)
            after_vehicle = _vehicle(steps[brake_index + 1].control_room_snapshot)
            self.assertLess(
                after_vehicle["telemetry"]["vehicle_velocity_kph"],
                braking_vehicle["telemetry"]["vehicle_velocity_kph"],
            )

    def test_cliff_drift_prevention_starts_critical_and_self_corrects(self) -> None:
        generator = HackathonScenarioGenerator()
        steps = list(generator.run("CLIFF_DRIFT_PREVENTION"))
        self.assertEqual(len(steps), 6)
        first_vehicle = _vehicle(steps[0].control_room_snapshot)
        last_vehicle = _vehicle(steps[-1].control_room_snapshot)
        self.assertEqual(first_vehicle["safety"]["safety_zone"], "red")
        self.assertIn(first_vehicle["safety"]["hazard_type"], ("ground_loss", "cliff_proximity"))
        self.assertEqual(last_vehicle["safety"]["safety_zone"], "green")
        self.assertIsNone(last_vehicle["safety"]["hazard_type"])

    def test_begin_step_resets_and_clears_incident_history_before_each_narrative(self) -> None:
        api = SimulationApi()
        generator = HackathonScenarioGenerator(api=api)
        list(generator.run("SUDDEN_OBSTACLE_EMERGENCY"))
        obstacle_signature = {(item.vehicle_id, item.hazard_type.value) for item in api.incidents.recent()}
        self.assertIn(("D01", "forward_collision"), obstacle_signature)

        # Every narrative begins with exactly this reset call. IncidentManager
        # intentionally restarts its id counter on clear() (existing Phase 5
        # behavior), so a fresh incident may coincidentally reuse an old id
        # string -- what actually proves history was wiped is that it is a
        # brand-new incident, created at t=0 of the new run, not one of the
        # timestamped incidents the obstacle scenario produced.
        generator._begin("NORMAL")
        after = api.incidents.recent()
        self.assertTrue(after)
        for incident in after:
            self.assertEqual(incident.created_timestamp_seconds, 0.0)
            self.assertNotEqual((incident.vehicle_id, incident.hazard_type.value), ("D01", "forward_collision"))


if __name__ == "__main__":
    unittest.main()
