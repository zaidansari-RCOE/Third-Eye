"""Stable response contracts for a future API layer."""

from __future__ import annotations

from dataclasses import dataclass

from third_eye.domain.telemetry import DataOrigin, TelemetrySnapshot


@dataclass(frozen=True, slots=True)
class TelemetryResponse:
    """Future read-model response, with origin outside the 22-field payload."""

    telemetry: TelemetrySnapshot
    origin: DataOrigin = DataOrigin.SIMULATED


@dataclass(frozen=True, slots=True)
class HealthResponse:
    """Minimal contract for a future service health endpoint."""

    service: str
    phase: str
    hardware_connected: bool

