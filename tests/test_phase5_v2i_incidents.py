from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.simulation import SimulationApi
from third_eye.domain.incidents import IncidentStatus
from third_eye.simulation.engine import SimulationService
from third_eye.simulation.models import BeaconCommunicationState, Scenario
from third_eye.simulation.telemetry import TelemetryService
from third_eye.simulation.v2i import relevant_beacon, simulated_rssi_dbm


class PhaseFiveV2IAndIncidentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SimulationService()
        self.api = SimulationApi(self.service)

    def test_existing_beacon_definitions_have_runtime_state_and_defaults(self) -> None:
        response = self.api.dispatch("GET", "/api/v2i/beacons")
        self.assertEqual(tuple(item["beacon_id"] for item in response.body["beacons"]), ("B01", "B02", "B03"))
        self.assertEqual(response.body["beacons"][0]["speed_limit_kph"], 30.0)
        self.assertIn("last_update_seconds", response.body["beacons"][0])

    def test_route_geometry_selects_relevant_beacon_and_rssi_is_deterministic(self) -> None:
        vehicle = self.service.state.vehicles[0]
        beacon = relevant_beacon(self.service.state, vehicle)
        self.assertEqual(beacon.beacon_id, "B01")
        self.assertEqual(simulated_rssi_dbm(100.0), simulated_rssi_dbm(100.0))
        self.service.start(); self.service.advance(30)
        later = relevant_beacon(self.service.state, self.service.state.vehicles[0])
        self.assertEqual(later.beacon_id, "B01")

    def test_dynamic_speed_limit_and_hazard_injection_affect_telemetry(self) -> None:
        response = self.api.dispatch("PUT", "/api/v2i/beacons/B01/speed-limit", {"speed_limit_kph": 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["speed_limit_kph"], 10.0)
        self.api.dispatch("POST", "/api/v2i/beacons/B01/hazard", {"message": "Heavy machinery ahead"})
        telemetry = TelemetryService(self.service).vehicle_telemetry("D01").fused.envelope.telemetry
        self.assertEqual(telemetry.curve_speed_limit_kph, 10.0)
        self.assertTrue(telemetry.hazard_warning_flag)
        self.api.dispatch("DELETE", "/api/v2i/beacons/B01/hazard")
        self.assertFalse(TelemetryService(self.service).vehicle_telemetry("D01").fused.envelope.telemetry.hazard_warning_flag)

    def test_beacon_failure_and_recovery_stop_and_restore_fresh_v2i_data(self) -> None:
        self.api.dispatch("POST", "/api/v2i/beacons/B01/failure", {"failed": True})
        beacon = self.api.dispatch("GET", "/api/v2i/beacons/B01").body
        self.assertEqual(beacon["communication_state"], BeaconCommunicationState.UNAVAILABLE)
        telemetry = TelemetryService(self.service).vehicle_telemetry("D01")
        self.assertEqual(telemetry.fused.envelope.telemetry.active_beacon_id, "UNAVAILABLE")
        self.assertFalse(telemetry.validation.reading("active_beacon_id").accepted)
        self.api.dispatch("POST", "/api/v2i/beacons/B01/failure", {"failed": False})
        self.assertEqual(TelemetryService(self.service).vehicle_telemetry("D01").fused.envelope.telemetry.active_beacon_id, "B01")

    def test_v2i_hazard_scenario_still_selects_b02(self) -> None:
        self.service.select_scenario(Scenario.V2I_HAZARD)
        telemetry = TelemetryService(self.service).vehicle_telemetry("D01").fused.envelope.telemetry
        self.assertEqual(telemetry.active_beacon_id, "B02")
        self.assertTrue(telemetry.hazard_warning_flag)

    def test_safety_event_creates_deduplicated_incident_with_context(self) -> None:
        self.service.select_scenario(Scenario.OBSTACLE)
        self.service.start(); self.service.advance(44)
        incidents = self.api.dispatch("GET", "/api/incidents").body["incidents"]
        collision = next(item for item in incidents if item["vehicle_id"] == "D01")
        self.assertEqual(collision["severity"], "CRITICAL")
        self.assertEqual(collision["status"], "open")
        self.assertIn("forward_lidar_cm", dict(collision["telemetry_context"]))
        self.assertEqual(len(self.api.dispatch("GET", "/api/incidents").body["incidents"]), len(incidents))

    def test_incident_acknowledgement_resolution_and_new_condition_history(self) -> None:
        self.service.select_scenario(Scenario.CLIFF_EDGE)
        self.service.start()
        incident = self.api.dispatch("GET", "/api/incidents/active").body["incidents"][0]
        acknowledged = self.api.dispatch("POST", f"/api/incidents/{incident['incident_id']}/acknowledge").body
        self.assertEqual(acknowledged["status"], IncidentStatus.ACKNOWLEDGED)
        resolved = self.api.dispatch("POST", f"/api/incidents/{incident['incident_id']}/resolve").body
        self.assertEqual(resolved["status"], IncidentStatus.RESOLVED)
        self.service.select_scenario(Scenario.NORMAL)
        active = self.api.dispatch("GET", "/api/incidents/active").body["incidents"]
        self.assertFalse(any(item["incident_id"] == incident["incident_id"] for item in active))
        count_before_recurrence = len(self.api.dispatch("GET", "/api/incidents").body["incidents"])
        self.service.select_scenario(Scenario.CLIFF_EDGE)
        self.assertEqual(len(self.api.dispatch("GET", "/api/incidents").body["incidents"]), count_before_recurrence + 1)

    def test_beacon_failure_scenario_produces_unavailable_v2i_and_incident(self) -> None:
        self.service.select_scenario(Scenario.BEACON_FAILURE)
        self.service.start()
        telemetry = TelemetryService(self.service).vehicle_telemetry("D01").fused.envelope.telemetry
        self.assertEqual(telemetry.active_beacon_id, "UNAVAILABLE")
        incidents = self.api.dispatch("GET", "/api/incidents/active").body["incidents"]
        self.assertTrue(any(item["hazard_type"] == "beacon_communication" for item in incidents))
