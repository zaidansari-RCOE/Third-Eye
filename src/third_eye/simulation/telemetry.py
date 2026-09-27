"""Authoritative-state telemetry pipeline: state -> sensors -> validation -> fusion."""

from __future__ import annotations

from dataclasses import dataclass

from third_eye.simulation.engine import SimulationService
from third_eye.simulation.fusion import FusedTelemetry, fuse_telemetry
from third_eye.simulation.sensors import SimulatedSensorFrame, generate_sensor_frame
from third_eye.simulation.validation import ValidatedSensorFrame, validate_sensor_frame


@dataclass(frozen=True, slots=True)
class VehicleTelemetryState:
    vehicle_id: str
    raw_frame: SimulatedSensorFrame
    validation: ValidatedSensorFrame
    fused: FusedTelemetry


class TelemetryService:
    """Produces telemetry solely from the one SimulationService authoritative state."""
    def __init__(self, simulation: SimulationService) -> None:
        self._simulation = simulation

    def vehicle_telemetry(self, vehicle_id: str) -> VehicleTelemetryState:
        state = self._simulation.state
        raw_frame = generate_sensor_frame(state, vehicle_id)
        validation = validate_sensor_frame(raw_frame)
        return VehicleTelemetryState(vehicle_id, raw_frame, validation, fuse_telemetry(validation))

