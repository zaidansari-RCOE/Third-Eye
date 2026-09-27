# API Contracts

Phase 1 provides Python response models, not an HTTP server or endpoints.
This preserves the boundary for a later API without inventing runtime behavior.

## `TelemetryResponse`

- `telemetry`: one `TelemetrySnapshot`, containing exactly the 22 proposal
  fields in their required order.
- `origin`: `simulated` by default; `hardware` only for a future physical
  adapter.

`origin` is envelope metadata, not a 23rd telemetry field.

## `HealthResponse`

- `service`: service identifier
- `phase`: implementation phase identifier
- `hardware_connected`: whether a future runtime has connected physical hardware

## Deferred API decisions

Endpoint paths, authentication, authorization, timestamping, serialization,
versioning, persistence, WebSockets, error schemas, and control commands are
**NOT SPECIFIED IN PROPOSAL** and are intentionally deferred.

