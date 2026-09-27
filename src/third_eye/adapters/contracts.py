"""Hardware-neutral interfaces for the eventual Raspberry Pi / ESP32 build.

These are protocols only. Phase 1 has no GPIO, I2C, UART, SPI, serial,
ESP-NOW, motor, or brake implementation.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from third_eye.domain.telemetry import TelemetrySnapshot
from third_eye.domain.v2i import BeaconBroadcast


class RaspberryPiVehicleController(Protocol):
    """Future boundary for vehicle-side orchestration on Raspberry Pi 4."""

    def read_telemetry(self) -> TelemetrySnapshot: ...


class AMG8833ThermalSensor(Protocol):
    """Future AMG8833 thermal-array boundary."""

    def read_temperature_matrix(self) -> Sequence[Sequence[float]]: ...


class TFLunaLidar(Protocol):
    """Future TF-Luna forward-distance boundary."""

    def read_distance_cm(self) -> float: ...


class VL53L1XLeftToF(Protocol):
    """Future left cliff-sensor boundary."""

    def read_distance_cm(self) -> float: ...


class VL53L1XRightToF(Protocol):
    """Future right cliff-sensor boundary."""

    def read_distance_cm(self) -> float: ...


class PiCamera(Protocol):
    """Future Pi Camera boundary; frame format is intentionally unspecified."""

    def capture_frame(self) -> object: ...


class ESP32V2IBeacon(Protocol):
    """Future ESP32 beacon boundary; no radio implementation is supplied."""

    def receive_broadcast(self) -> BeaconBroadcast: ...

