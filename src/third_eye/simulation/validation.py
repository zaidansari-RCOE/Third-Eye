"""Validation boundary between simulated/physical adapters and telemetry fusion."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from third_eye.simulation.sensors import SensorReading, SimulatedSensorFrame


@dataclass(frozen=True, slots=True)
class ValidatedReading:
    reading: SensorReading
    accepted: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ValidatedSensorFrame:
    vehicle_id: str
    simulation_time_seconds: float
    readings: tuple[ValidatedReading, ...]

    def reading(self, name: str) -> ValidatedReading:
        return next(item for item in self.readings if item.reading.name == name)


def validate_reading(reading: SensorReading, expected_time_seconds: float) -> ValidatedReading:
    """Reject invalid/stale/non-finite readings rather than silently using them."""
    if not reading.valid:
        return ValidatedReading(reading, False, "sensor_invalid")
    if reading.stale:
        return ValidatedReading(reading, False, "sensor_stale")
    if reading.simulation_time_seconds != expected_time_seconds:
        return ValidatedReading(reading, False, "timestamp_mismatch")
    if isinstance(reading.value, float) and not isfinite(reading.value):
        return ValidatedReading(reading, False, "non_finite_value")
    return ValidatedReading(reading, True)


def validate_sensor_frame(frame: SimulatedSensorFrame) -> ValidatedSensorFrame:
    return ValidatedSensorFrame(frame.vehicle_id, frame.simulation_time_seconds, tuple(validate_reading(item, frame.simulation_time_seconds) for item in frame.readings))

