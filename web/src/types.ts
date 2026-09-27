export const TELEMETRY_FIELDS = [
  "forward_lidar_cm",
  "rate_of_closure_mps",
  "thermal_temp_gradient",
  "human_detection_conf",
  "visual_fog_density_pct",
  "left_cliff_dist_cm",
  "right_cliff_dist_cm",
  "ground_loss_trigger",
  "pitch_angle_degrees",
  "roll_angle_degrees",
  "vehicle_velocity_kph",
  "motor_current_draw_ma",
  "core_temp_celsius",
  "batt_voltage_millivolts",
  "braking_pressure_psi",
  "runtime_seconds",
  "active_beacon_id",
  "beacon_rssi_dbm",
  "curve_speed_limit_kph",
  "hazard_warning_flag",
  "local_gps_lat_offset",
  "local_gps_lon_offset",
] as const;

export type TelemetryField = (typeof TELEMETRY_FIELDS)[number];

export const SCENARIOS = [
  "NORMAL",
  "DENSE_FOG",
  "OBSTACLE",
  "CLIFF_EDGE",
  "V2I_HAZARD",
  "SENSOR_FAILURE",
  "BEACON_FAILURE",
] as const;

export type ScenarioName = (typeof SCENARIOS)[number];

export type ConnectionStatus = "connecting" | "live" | "reconnecting" | "disconnected";

export type LocalCoordinate = { x_m: number; y_m: number };

export type ValidationRecord = { accepted: boolean; reason: string | null };

export type SafetyView = {
  vehicle_id: string;
  timestamp_seconds: number;
  severity: string;
  hazard_type: string | null;
  triggered_rules: string[];
  explanation: string;
  action: string;
  simulated_brake_active: boolean;
  source_telemetry_reference: string[];
  safety_zone: "green" | "yellow" | "red";
  event: Record<string, unknown> | null;
};

export type VehicleView = {
  vehicle_id: string;
  route_id: string;
  route_progress_m: number;
  position: LocalCoordinate;
  heading_degrees: number;
  velocity_kph: number;
  current_road_segment_id: string;
  operating_state: string;
  origin: string;
  telemetry: Record<string, string | number | boolean>;
  validation: Record<string, ValidationRecord>;
  safety: SafetyView;
};

export type BeaconView = {
  beacon_id: string;
  position: LocalCoordinate;
  associated_road_segment_id: string;
  associated_zone_id: string;
  operating_state: string;
  communication_state: string;
  hazard_broadcast_active: boolean;
  speed_limit_kph: number;
  hazard_message: string | null;
  last_update_seconds: number;
};

export type IncidentView = {
  incident_id: string;
  vehicle_id: string;
  timestamp_seconds: number;
  created_timestamp_seconds: number;
  severity: string;
  hazard_type: string;
  title: string;
  message: string;
  triggering_rule: string;
  telemetry_context: [string, unknown][];
  safety_action: string;
  simulated_brake_active: boolean;
  status: string;
  resolved_timestamp_seconds: number | null;
};

export type ControlRoomSnapshot = {
  origin: string;
  hardware_connected: boolean;
  clock: { elapsed_seconds: number; status: string };
  scenario: ScenarioName | string;
  conditions: Record<string, unknown>;
  routes: { route_id: string; name: string; segment_ids: string[] }[];
  road_segments: {
    segment_id: string;
    name: string;
    start: LocalCoordinate;
    end: LocalCoordinate;
    associated_zone_id: string;
    is_blind_curve: boolean;
  }[];
  vehicles: VehicleView[];
  beacons: BeaconView[];
  incidents_active: IncidentView[];
  incidents_recent: IncidentView[];
  kpis: {
    fleet_size: number;
    elapsed_seconds: number;
    clock_status: string;
    scenario: string;
    active_incident_count: number;
    severity_counts: Record<string, number>;
    simulated_braking_count: number;
    mean_velocity_kph: number;
    max_velocity_kph: number;
    origin: string;
    hardware_connected: boolean;
  };
  telemetry_field_names: string[];
};

export type MapDocument = {
  origin: string;
  hardware_connected: boolean;
  mine_area: { mine_id: string; name: string; boundary: LocalCoordinate[] };
  benches: { bench_id: string; name: string; boundary: LocalCoordinate[] }[];
  safe_zones: { zone_id: string; name: string; boundary: LocalCoordinate[] }[];
  cliff_boundaries: { boundary_id: string; name: string; start: LocalCoordinate; end: LocalCoordinate }[];
  intersections: { intersection_id: string; name: string; coordinate: LocalCoordinate; is_blind_curve: boolean }[];
  road_segments: ControlRoomSnapshot["road_segments"];
  routes: ControlRoomSnapshot["routes"];
};

export type WsEnvelope = {
  type: string;
  origin: string;
  payload: ControlRoomSnapshot;
};
