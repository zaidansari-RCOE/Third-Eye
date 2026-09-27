"""Central safety values for the demonstration, not mining engineering limits."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SafetyThresholds:
    """SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT."""

    collision_warning_distance_cm: float = 3_000.0
    collision_critical_distance_cm: float = 1_000.0
    collision_closure_warning_mps: float = 1.0
    cliff_warning_distance_cm: float = 500.0
    fog_caution_density_pct: float = 50.0
    fog_warning_density_pct: float = 85.0
    fog_low_confidence: float = 0.70
    v2i_weak_rssi_dbm: float = -80.0
    simulated_brake_deceleration_kph_per_second: float = 4.0


THRESHOLDS = SafetyThresholds()
