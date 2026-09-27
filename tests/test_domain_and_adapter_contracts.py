from __future__ import annotations

import pathlib
import sys
import unittest
from typing import Protocol

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.contracts import HealthResponse, TelemetryResponse
from third_eye.adapters.contracts import (
    AMG8833ThermalSensor,
    ESP32V2IBeacon,
    PiCamera,
    RaspberryPiVehicleController,
    TFLunaLidar,
    VL53L1XLeftToF,
    VL53L1XRightToF,
)
from third_eye.domain.safety import HazardType, SafetyDefinition, SafetyResponse, SafetyZone
from third_eye.domain.telemetry import DataOrigin, TelemetrySnapshot
from third_eye.domain.v2i import BeaconBroadcast


class DomainAndApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.telemetry = TelemetrySnapshot(
            1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, False, 8.0, 9.0, 10.0,
            11.0, 12.0, 13.0, 14.0, 15.0, "beacon-a", -40.0, 20.0, False,
            21.0, 22.0,
        )

    def test_api_contract_preserves_simulated_origin_by_default(self) -> None:
        response = TelemetryResponse(self.telemetry)
        self.assertEqual(response.origin, DataOrigin.SIMULATED)
        self.assertFalse(HealthResponse("third-eye", "phase-1", False).hardware_connected)

    def test_safety_definition_is_descriptive_not_an_engine(self) -> None:
        definition = SafetyDefinition(
            HazardType.FORWARD_COLLISION,
            SafetyZone.RED,
            SafetyResponse.DRIVER_WARNING,
            "Future rule definition only.",
        )
        self.assertEqual(definition.zone, SafetyZone.RED)

    def test_beacon_contract_uses_proposal_defined_fields(self) -> None:
        broadcast = BeaconBroadcast("beacon-a", -48.0, 15.0, True, 1.0, 2.0)
        self.assertTrue(broadcast.hazard_warning_flag)
        self.assertEqual(broadcast.active_beacon_id, "beacon-a")

    def test_hardware_boundaries_are_protocols_not_active_adapters(self) -> None:
        boundaries = (
            RaspberryPiVehicleController, AMG8833ThermalSensor, TFLunaLidar,
            VL53L1XLeftToF, VL53L1XRightToF, PiCamera, ESP32V2IBeacon,
        )
        for boundary in boundaries:
            self.assertTrue(issubclass(boundary, Protocol))
            self.assertTrue(boundary._is_protocol)
