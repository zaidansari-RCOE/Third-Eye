"""V2I/beacon message definitions; no ESP-NOW runtime is present in Phase 1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BeaconDefinition:
    """A future ESP32 roadside beacon placed at a blind spot or curve."""

    beacon_id: str
    location_label: str


@dataclass(frozen=True, slots=True)
class BeaconBroadcast:
    """Proposal-defined information broadcast by a roadside beacon."""

    active_beacon_id: str
    beacon_rssi_dbm: float
    curve_speed_limit_kph: float
    hazard_warning_flag: bool
    local_gps_lat_offset: float
    local_gps_lon_offset: float

