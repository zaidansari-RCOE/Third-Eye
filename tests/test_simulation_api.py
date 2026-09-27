from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from third_eye.api.simulation import SimulationApi
from third_eye.api.asgi import SimulationAsgiApp


class SimulationApiTests(unittest.TestCase):
    def test_required_state_and_lifecycle_routes(self) -> None:
        api = SimulationApi()
        self.assertEqual(api.dispatch("GET", "/api/simulation/state").status_code, 200)
        self.assertEqual(api.dispatch("POST", "/api/simulation/start").body["clock"]["status"], "running")
        self.assertEqual(api.dispatch("POST", "/api/simulation/pause").body["clock"]["status"], "paused")
        self.assertEqual(api.dispatch("POST", "/api/simulation/reset").body["scenario"], "NORMAL")

    def test_scenario_route_and_error_contract(self) -> None:
        api = SimulationApi()
        response = api.dispatch("POST", "/api/simulation/scenario", {"scenario": "DENSE_FOG"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.body["conditions"]["dense_fog"])
        self.assertEqual(api.dispatch("POST", "/api/simulation/scenario", {}).status_code, 400)
        self.assertEqual(api.dispatch("GET", "/unknown").status_code, 404)

    def test_websocket_stream_sends_authoritative_state_on_connect(self) -> None:
        sent: list[dict[str, object]] = []
        events = iter(({"type": "websocket.connect"}, {"type": "websocket.disconnect"}))

        async def receive() -> dict[str, object]:
            return next(events)

        async def send(event: dict[str, object]) -> None:
            sent.append(event)

        asyncio.run(
            SimulationAsgiApp(SimulationApi())(
                {"type": "websocket", "path": "/api/simulation/ws"}, receive, send
            )
        )
        self.assertEqual(sent[0]["type"], "websocket.accept")
        self.assertEqual(sent[1]["type"], "websocket.send")
        message = json.loads(str(sent[1]["text"]))
        self.assertEqual(message["type"], "control_room_snapshot")
        self.assertEqual(message["origin"], "simulated")
        self.assertEqual(message["payload"]["scenario"], "NORMAL")
