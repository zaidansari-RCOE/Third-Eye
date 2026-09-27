"""Causal deterministic sensor-frame generation from authoritative twin state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite, sin
from typing import Any

from third_eye.simulation.models import BeaconCommunicationState, Scenario, SimulationState, VirtualVehicle
from third_eye.simulation.v2i import distance_m, relevant_beacon, simulated_rssi_dbm


class SensorSource(StrEnum):
    TF_LUNA_LIDAR = "simulated_tf_luna_lidar"
    AMG8833_THERMAL = "simulated_amg8833_thermal"
    LEFT_VL53L1X = "simulated_left_vl53l1x"
    RIGHT_VL53L1X = "simulated_right_vl53l1x"
    CAMERA = "simulated_pi_camera"
    VEHICLE_DIAGNOSTICS = "simulated_vehicle_diagnostics"
    V2I_BEACON = "simulated_esp32_v2i"
    ORIENTATION = "simulated_vehicle_environment_orientation"


@dataclass(frozen=True, slots=True)
class SensorReading:
    """One raw simulated value and its validation-relevant provenance."""
    name: str
    source: SensorSource
    value: Any
    simulation_time_seconds: float
    valid: bool = True
    stale: bool = False


@dataclass(frozen=True, slots=True)
class SimulatedSensorFrame:
    vehicle_id: str
    simulation_time_seconds: float
    readings: tuple[SensorReading, ...]

    def reading(self, name: str) -> SensorReading:
        return next(reading for reading in self.readings if reading.name == name)


def _current_segment_remaining_metres(state: SimulationState, vehicle: VirtualVehicle) -> float:
    segment = next(item for item in state.topology.road_segments if item.segment_id == vehicle.current_road_segment_id)
    return distance_m(vehicle.position, segment.end)


def _obstacle_distance_cm(state: SimulationState, vehicle: VirtualVehicle, normal_distance_cm: float) -> float:
    """Fixed fictional obstacle on ROUTE-N; it becomes nearer as D01 progresses."""
    if state.scenario is not Scenario.OBSTACLE or vehicle.route_id != "ROUTE-N":
        return normal_distance_cm
    forward_distance_m = 300.0 - vehicle.route_progress_m
    if not 0.0 <= forward_distance_m <= 450.0:
        return normal_distance_cm
    return min(normal_distance_cm, max(50.0, forward_distance_m * 100.0))


def _cliff_distances_cm(state: SimulationState, vehicle: VirtualVehicle) -> tuple[float, float]:
    if state.scenario is not Scenario.CLIFF_EDGE or vehicle.route_id != "ROUTE-N":
        return 2500.0, 2500.0
    proximity_cm = max(10.0, abs(vehicle.route_progress_m) * 100.0)
    return min(2500.0, proximity_cm), 2500.0


def generate_sensor_frame(state: SimulationState, vehicle_id: str) -> SimulatedSensorFrame:
    """Generate deterministic readings from one authoritative state snapshot."""
    vehicle = next(item for item in state.vehicles if item.vehicle_id == vehicle_id)
    time = state.clock.elapsed_seconds
    dense_fog = state.conditions.dense_fog
    normal_lidar_cm = min(45_000.0, _current_segment_remaining_metres(state, vehicle) * 100.0)
    lidar_cm = _obstacle_distance_cm(state, vehicle, normal_lidar_cm)
    lidar_healthy = state.scenario is not Scenario.SENSOR_FAILURE
    left_tof_cm, right_tof_cm = _cliff_distances_cm(state, vehicle)
    selected_beacon = relevant_beacon(state, vehicle)
    beacon_available = selected_beacon.communication_state is BeaconCommunicationState.AVAILABLE
    beacon_distance_m = distance_m(vehicle.position, selected_beacon.position)
    speed_mps = vehicle.velocity_kph / 3.6
    heading_component = (vehicle.heading_degrees - 180.0) / 180.0
    readings = (
        SensorReading("lidar_distance_cm", SensorSource.TF_LUNA_LIDAR, lidar_cm, time, lidar_healthy, not lidar_healthy),
        SensorReading("lidar_rate_of_closure_mps", SensorSource.TF_LUNA_LIDAR, speed_mps if state.scenario is Scenario.OBSTACLE else 0.0, time, lidar_healthy, not lidar_healthy),
        SensorReading("thermal_temp_gradient", SensorSource.AMG8833_THERMAL, 7.5 if state.scenario is Scenario.OBSTACLE else 3.0, time),
        SensorReading("thermal_human_detection_conf", SensorSource.AMG8833_THERMAL, 0.62 if dense_fog else 0.92, time),
        SensorReading("visual_fog_density_pct", SensorSource.CAMERA, 95.0 if dense_fog else 10.0, time),
        SensorReading("left_tof_distance_cm", SensorSource.LEFT_VL53L1X, left_tof_cm, time),
        SensorReading("right_tof_distance_cm", SensorSource.RIGHT_VL53L1X, right_tof_cm, time),
        SensorReading("pitch_angle_degrees", SensorSource.ORIENTATION, heading_component * 2.0, time),
        SensorReading("roll_angle_degrees", SensorSource.ORIENTATION, sin(vehicle.route_progress_m / 100.0) * 1.5 + (3.0 if state.conditions.cliff_edge_active else 0.0), time),
        SensorReading("vehicle_velocity_kph", SensorSource.VEHICLE_DIAGNOSTICS, vehicle.velocity_kph, time),
        SensorReading("motor_current_draw_ma", SensorSource.VEHICLE_DIAGNOSTICS, 4_500.0 + vehicle.velocity_kph * 60.0 + (250.0 if dense_fog else 0.0), time),
        SensorReading("core_temp_celsius", SensorSource.VEHICLE_DIAGNOSTICS, 42.0 + vehicle.velocity_kph * 0.12 + time * 0.002, time),
        SensorReading("batt_voltage_millivolts", SensorSource.VEHICLE_DIAGNOSTICS, max(10_500.0, 12_600.0 - time * 0.08), time),
        SensorReading("braking_pressure_psi", SensorSource.VEHICLE_DIAGNOSTICS, 0.0, time),
        SensorReading("runtime_seconds", SensorSource.VEHICLE_DIAGNOSTICS, time, time),
        SensorReading("active_beacon_id", SensorSource.V2I_BEACON, selected_beacon.beacon_id if beacon_available else "UNAVAILABLE", time, beacon_available, not beacon_available),
        SensorReading("beacon_rssi_dbm", SensorSource.V2I_BEACON, simulated_rssi_dbm(beacon_distance_m) if beacon_available else -999.0, time, beacon_available, not beacon_available),
        SensorReading("curve_speed_limit_kph", SensorSource.V2I_BEACON, selected_beacon.speed_limit_kph if beacon_available else 0.0, time, beacon_available, not beacon_available),
        SensorReading("hazard_warning_flag", SensorSource.V2I_BEACON, selected_beacon.hazard_broadcast_active and beacon_available, time, beacon_available, not beacon_available),
        SensorReading("local_gps_lat_offset", SensorSource.V2I_BEACON, selected_beacon.position.y_m - vehicle.position.y_m if beacon_available else 0.0, time, beacon_available, not beacon_available),
        SensorReading("local_gps_lon_offset", SensorSource.V2I_BEACON, selected_beacon.position.x_m - vehicle.position.x_m if beacon_available else 0.0, time, beacon_available, not beacon_available),
    )
    for reading in readings:
        if isinstance(reading.value, float) and not isfinite(reading.value):
            raise ValueError(f"Non-finite simulated value for {reading.name}")
    return SimulatedSensorFrame(vehicle_id, time, readings)
