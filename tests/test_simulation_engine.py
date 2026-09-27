from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.simulation.engine import SimulationService, build_initial_state
from third_eye.simulation.models import ClockStatus, Scenario


class SimulationEngineTests(unittest.TestCase):
    def test_initial_topology_has_fictional_mine_structure(self) -> None:
        state = build_initial_state()
        self.assertEqual(state.topology.mine_area.mine_id, "MINE-01")
        self.assertEqual(len(state.topology.benches), 2)
        self.assertGreaterEqual(len(state.topology.road_segments), 12)
        self.assertGreaterEqual(len(state.topology.cliff_boundaries), 2)
        self.assertTrue(any(item.is_blind_curve for item in state.topology.intersections))

    def test_initial_fleet_and_beacons_match_phase_two_minimum(self) -> None:
        state = build_initial_state()
        self.assertEqual(tuple(vehicle.vehicle_id for vehicle in state.vehicles), ("D01", "D02", "D03"))
        self.assertEqual(tuple(beacon.beacon_id for beacon in state.beacons), ("B01", "B02", "B03"))
        self.assertEqual(len(state.topology.routes), 3)

    def test_clock_start_pause_and_explicit_advancement(self) -> None:
        service = SimulationService()
        self.assertEqual(service.state.clock.status, ClockStatus.PAUSED)
        self.assertEqual(service.advance(10).clock.elapsed_seconds, 0.0)
        self.assertEqual(service.start().clock.status, ClockStatus.RUNNING)
        self.assertEqual(service.advance(10).clock.elapsed_seconds, 10.0)
        self.assertEqual(service.pause().clock.status, ClockStatus.PAUSED)
        self.assertEqual(service.advance(10).clock.elapsed_seconds, 10.0)

    def test_vehicle_moves_by_route_geometry_and_progresses_segments(self) -> None:
        service = SimulationService()
        initial = service.state.vehicles[0]
        moved = service.start()
        moved = service.advance(70).vehicles[0]
        self.assertNotEqual(initial.position, moved.position)
        self.assertNotEqual(initial.current_road_segment_id, moved.current_road_segment_id)
        self.assertGreater(moved.route_progress_m, initial.route_progress_m)

    def test_same_initial_state_and_elapsed_time_are_deterministic(self) -> None:
        first = SimulationService()
        second = SimulationService()
        first.start(); second.start()
        self.assertEqual(first.advance(123.5), second.advance(123.5))

    def test_reset_restores_exact_initial_state(self) -> None:
        service = SimulationService()
        initial = service.state
        service.start()
        service.advance(120)
        service.select_scenario(Scenario.BEACON_FAILURE)
        self.assertNotEqual(service.state, initial)
        self.assertEqual(service.reset(), initial)
        self.assertEqual(service.state.scenario, Scenario.NORMAL)

    def test_scenarios_establish_state_without_safety_processing(self) -> None:
        service = SimulationService()
        v2i = service.select_scenario(Scenario.V2I_HAZARD)
        self.assertTrue(v2i.conditions.v2i_hazard_active)
        self.assertTrue(next(beacon for beacon in v2i.beacons if beacon.beacon_id == "B02").hazard_broadcast_active)
        failed = service.select_scenario(Scenario.SENSOR_FAILURE)
        self.assertEqual(next(vehicle for vehicle in failed.vehicles if vehicle.vehicle_id == "D02").operating_state.value, "sensor_degraded")
        beacon_failed = service.select_scenario(Scenario.BEACON_FAILURE)
        self.assertEqual(next(beacon for beacon in beacon_failed.beacons if beacon.beacon_id == "B03").communication_state.value, "unavailable")

