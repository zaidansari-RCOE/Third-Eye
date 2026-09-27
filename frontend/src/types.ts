export type Scenario = "NORMAL" | "DENSE_FOG" | "OBSTACLE" | "CLIFF_EDGE" | "V2I_HAZARD" | "SENSOR_FAILURE" | "BEACON_FAILURE";
export type Telemetry = Record<string, string | number | boolean>;
export interface Point { x_m: number; y_m: number }
export interface Vehicle { vehicle_id: string; position: Point; velocity_kph: number; current_road_segment_id: string; operating_state: string }
export interface Beacon { beacon_id: string; position: Point; associated_road_segment_id: string; operating_state: string; communication_state: string; hazard_broadcast_active: boolean; speed_limit_kph: number; hazard_message: string | null; last_update_seconds: number }
export interface Decision { vehicle_id: string; severity: "NORMAL" | "CAUTION" | "WARNING" | "CRITICAL"; hazard_type: string | null; action: string; simulated_brake_active: boolean; explanation: string }
export interface State { clock: { elapsed_seconds: number; status: string }; scenario: Scenario; topology: { road_segments: { segment_id: string; start: Point; end: Point }[]; safe_zones: { zone_id: string; boundary: Point[] }[]; cliff_boundaries: { boundary_id: string; start: Point; end: Point }[] }; vehicles: Vehicle[]; beacons: Beacon[]; safety_decisions: Decision[] }
export interface Incident { incident_id: string; vehicle_id: string; timestamp_seconds: number; severity: "CAUTION" | "WARNING" | "CRITICAL"; hazard_type: string; message: string; safety_action: string; simulated_brake_active: boolean; status: "open" | "acknowledged" | "resolved" }
