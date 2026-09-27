from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.asgi import SimulationAsgiApp
from third_eye.api.simulation import SimulationApi
from third_eye.api.snapshot import build_control_room_snapshot
from third_eye.domain.telemetry import TELEMETRY_FIELD_NAMES
from third_eye.simulation.models import Scenario
from third_eye.simulation.topology import build_virtual_mine_topology


class PhaseSixControlRoomTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = SimulationApi()

    def test_health_endpoint_reports_phase_six_without_hardware(self) -> None:
        response = self.api.dispatch("GET", "/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["service"], "third-eye")
        self.assertEqual(response.body["phase"], "6")
        self.assertIs(response.body["hardware_connected"], False)

    def test_map_endpoint_matches_authoritative_topology(self) -> None:
        topology = build_virtual_mine_topology()
        response = self.api.dispatch("GET", "/api/simulation/map")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body["origin"], "simulated")
        self.assertIs(response.body["hardware_connected"], False)
        self.assertEqual(response.body["mine_area"]["mine_id"], topology.mine_area.mine_id)
        self.assertEqual(
            [item["segment_id"] for item in response.body["road_segments"]],
            [item.segment_id for item in topology.road_segments],
        )
        self.assertEqual(
            [item["route_id"] for item in response.body["routes"]],
            [item.route_id for item in topology.routes],
        )

    def test_control_room_snapshot_has_exact_22_fields_and_simulated_origin(self) -> None:
        response = self.api.dispatch("GET", "/api/simulation/control-room")
        body = response.body
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["origin"], "simulated")
        self.assertIs(body["hardware_connected"], False)
        self.assertEqual(tuple(body["telemetry_field_names"]), TELEMETRY_FIELD_NAMES)
        self.assertEqual(len(body["vehicles"]), 3)
        self.assertIn("clock", body)
        self.assertIn("scenario", body)
        self.assertIn("conditions", body)
        self.assertIn("routes", body)
        self.assertIn("road_segments", body)
        self.assertIn("beacons", body)
        self.assertIn("kpis", body)
        self.assertNotIn("kpis", body["vehicles"][0]["telemetry"])
        self.assertNotIn("validation", body["vehicles"][0]["telemetry"])
        for vehicle in body["vehicles"]:
            self.assertEqual(tuple(vehicle["telemetry"]), TELEMETRY_FIELD_NAMES)
            self.assertEqual(len(vehicle["telemetry"]), 22)
            self.assertEqual(vehicle["origin"], "simulated")
            self.assertIn("position", vehicle)
            self.assertIn("x_m", vehicle["position"])
            self.assertIn("y_m", vehicle["position"])
            self.assertIn("velocity_kph", vehicle)
            self.assertIn("validation", vehicle)
            self.assertIn("safety", vehicle)
            self.assertIn("safety_zone", vehicle["safety"])
        self.assertIs(body["kpis"]["hardware_connected"], False)
        self.assertEqual(body["kpis"]["origin"], "simulated")
        self.assertEqual(body["kpis"]["fleet_size"], 3)

    def test_snapshot_does_not_mutate_simulation_state(self) -> None:
        before = self.api.simulation.state
        build_control_room_snapshot(self.api)
        after = self.api.simulation.state
        self.assertIs(before, after)
        self.assertEqual(before.clock.elapsed_seconds, after.clock.elapsed_seconds)
        self.assertEqual(before.vehicles, after.vehicles)

    def test_advance_endpoint_moves_only_when_running(self) -> None:
        paused = self.api.dispatch("POST", "/api/simulation/advance", {"seconds": 5})
        self.assertEqual(paused.status_code, 200)
        self.assertEqual(paused.body["clock"]["elapsed_seconds"], 0.0)
        self.api.dispatch("POST", "/api/simulation/start")
        moved = self.api.dispatch("POST", "/api/simulation/advance", {"seconds": 5})
        self.assertGreater(moved.body["clock"]["elapsed_seconds"], 0.0)
        self.assertNotEqual(
            moved.body["vehicles"][0]["position"],
            paused.body["vehicles"][0]["position"],
        )
        bad = self.api.dispatch("POST", "/api/simulation/advance", {"seconds": -1})
        self.assertEqual(bad.status_code, 400)

    def test_reset_clears_incident_history(self) -> None:
        self.api.dispatch("POST", "/api/simulation/scenario", {"scenario": "CLIFF_EDGE"})
        self.api.dispatch("POST", "/api/simulation/start")
        incidents = self.api.dispatch("GET", "/api/incidents").body["incidents"]
        self.assertGreater(len(incidents), 0)
        self.api.dispatch("POST", "/api/simulation/reset")
        self.assertEqual(self.api.dispatch("GET", "/api/incidents").body["incidents"], [])
        self.assertEqual(self.api.simulation.state.scenario, Scenario.NORMAL)

    def test_beacon_and_incident_commands_remain_on_dispatch(self) -> None:
        speed = self.api.dispatch("PUT", "/api/v2i/beacons/B02/speed-limit", {"speed_limit_kph": 12})
        self.assertEqual(speed.status_code, 200)
        self.assertEqual(speed.body["speed_limit_kph"], 12.0)
        hazard = self.api.dispatch("POST", "/api/v2i/beacons/B02/hazard", {"message": "Demo hazard"})
        self.assertTrue(hazard.body["hazard_broadcast_active"])
        self.api.dispatch("POST", "/api/simulation/scenario", {"scenario": "SENSOR_FAILURE"})
        self.api.dispatch("POST", "/api/simulation/start")
        active = self.api.dispatch("GET", "/api/incidents/active").body["incidents"]
        self.assertGreater(len(active), 0)
        incident_id = active[0]["incident_id"]
        acknowledged = self.api.dispatch("POST", f"/api/incidents/{incident_id}/acknowledge")
        self.assertEqual(acknowledged.body["status"], "acknowledged")
        resolved = self.api.dispatch("POST", f"/api/incidents/{incident_id}/resolve")
        self.assertEqual(resolved.body["status"], "resolved")

    def test_websocket_snapshot_envelope(self) -> None:
        sent: list[dict[str, object]] = []
        events = iter(({"type": "websocket.connect"}, {"type": "websocket.disconnect"}))

        async def receive() -> dict[str, object]:
            return next(events)

        async def send(event: dict[str, object]) -> None:
            sent.append(event)

        asyncio.run(
            SimulationAsgiApp(self.api)(
                {"type": "websocket", "path": "/api/simulation/ws"}, receive, send
            )
        )
        message = json.loads(str(sent[1]["text"]))
        self.assertEqual(message["type"], "control_room_snapshot")
        self.assertEqual(message["origin"], "simulated")
        self.assertEqual(tuple(message["payload"]["vehicles"][0]["telemetry"]), TELEMETRY_FIELD_NAMES)
        self.assertFalse(message["payload"]["hardware_connected"])

    def test_websocket_updates_after_mutating_http(self) -> None:
        async def exercise() -> list[dict[str, object]]:
            app = SimulationAsgiApp(self.api)
            sent: list[dict[str, object]] = []
            inbound: asyncio.Queue[dict[str, object]] = asyncio.Queue()

            async def ws_receive() -> dict[str, object]:
                return await inbound.get()

            async def ws_send(event: dict[str, object]) -> None:
                sent.append(event)

            task = asyncio.create_task(
                app({"type": "websocket", "path": "/api/simulation/ws"}, ws_receive, ws_send)
            )
            await inbound.put({"type": "websocket.connect"})
            for _ in range(20):
                if any(item.get("type") == "websocket.send" for item in sent):
                    break
                await asyncio.sleep(0)
            first_sends = len([item for item in sent if item.get("type") == "websocket.send"])

            async def http_receive() -> dict[str, object]:
                return {"type": "http.request", "body": b"{}"}

            http_sent: list[dict[str, object]] = []

            async def http_send(event: dict[str, object]) -> None:
                http_sent.append(event)

            await app(
                {"type": "http", "method": "POST", "path": "/api/simulation/start"},
                http_receive,
                http_send,
            )
            for _ in range(20):
                if len([item for item in sent if item.get("type") == "websocket.send"]) > first_sends:
                    break
                await asyncio.sleep(0)
            await inbound.put({"type": "websocket.disconnect"})
            await task
            return sent

        sent = asyncio.run(exercise())
        snapshots = [json.loads(str(item["text"])) for item in sent if item.get("type") == "websocket.send"]
        self.assertGreaterEqual(len(snapshots), 2)
        self.assertEqual(snapshots[0]["type"], "control_room_snapshot")
        self.assertEqual(snapshots[-1]["payload"]["clock"]["status"], "running")

    def test_asgi_cors_and_options(self) -> None:
        async def exercise() -> tuple[int, list[tuple[bytes, bytes]]]:
            app = SimulationAsgiApp(self.api)
            sent: list[dict[str, object]] = []

            async def receive() -> dict[str, object]:
                return {"type": "http.request", "body": b""}

            async def send(event: dict[str, object]) -> None:
                sent.append(event)

            await app({"type": "http", "method": "OPTIONS", "path": "/api/health"}, receive, send)
            start = next(item for item in sent if item["type"] == "http.response.start")
            return int(start["status"]), list(start["headers"])

        status, headers = asyncio.run(exercise())
        header_map = dict(headers)
        self.assertEqual(status, 204)
        self.assertEqual(header_map[b"access-control-allow-origin"], b"*")

    def test_demo_ticker_is_disabled_by_default_for_tests(self) -> None:
        app = SimulationAsgiApp(self.api)
        self.assertEqual(app.demo_tick_hz, 0.0)
        self.assertIsNone(app._tick_task)
        self.api.dispatch("POST", "/api/simulation/start")
        self.assertEqual(self.api.simulation.state.clock.elapsed_seconds, 0.0)
