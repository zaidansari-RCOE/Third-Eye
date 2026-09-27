"""Presentation/demo choreography helpers.

Everything in this package is orchestration only: it drives the existing,
frozen ``SimulationApi`` / ``SimulationService`` through their public methods
(reset, scenario selection, start, advance). It introduces no new simulation
engine, no new telemetry, safety, or V2I formula, and no new WebSocket
protocol. It exists purely to script a live demo/presentation.
"""
