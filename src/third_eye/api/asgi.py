"""Dependency-free ASGI adapter exposing simulation REST and WebSocket paths."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from third_eye.api.simulation import SimulationApi
from third_eye.api.snapshot import control_room_message
from third_eye.simulation.models import ClockStatus


CORS_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b"access-control-allow-origin", b"*"),
    (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS"),
    (b"access-control-allow-headers", b"content-type"),
    (b"access-control-max-age", b"86400"),
)

_MUTATING_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})

# SIMULATION ASSUMPTION — NOT AN ENGINEERING LIMIT. Demo display cadence only.
DEFAULT_DEMO_TICK_HZ = 8.0


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


class SimulationAsgiApp:
    """ASGI adapter. Optional demo ticker calls ``SimulationService.advance`` only."""

    def __init__(self, api: SimulationApi | None = None, *, demo_tick_hz: float = 0.0) -> None:
        self.api = api or SimulationApi()
        self.demo_tick_hz = demo_tick_hz
        self._sockets: list[Any] = []
        self._tick_task: asyncio.Task[None] | None = None

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope["type"] == "http":
            await self._http(scope, receive, send)
            return
        if scope["type"] == "websocket" and scope.get("path") == "/api/simulation/ws":
            await self._websocket(receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})

    def _ensure_ticker(self) -> None:
        if self.demo_tick_hz <= 0 or self._tick_task is not None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._tick_task = loop.create_task(self._run_ticker())

    async def _lifespan(self, receive: Any, send: Any) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                self._ensure_ticker()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                if self._tick_task is not None:
                    self._tick_task.cancel()
                    self._tick_task = None
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def _run_ticker(self) -> None:
        dt = 1.0 / self.demo_tick_hz
        try:
            while True:
                await asyncio.sleep(dt)
                if self.api.simulation.state.clock.status is ClockStatus.RUNNING:
                    self.api.simulation.advance(dt)
                    await self._broadcast()
        except asyncio.CancelledError:
            return

    async def _broadcast(self) -> None:
        text = _json_dumps(control_room_message(self.api))
        stale: list[Any] = []
        for socket_send in self._sockets:
            try:
                await socket_send({"type": "websocket.send", "text": text})
            except Exception:
                stale.append(socket_send)
        for item in stale:
            if item in self._sockets:
                self._sockets.remove(item)

    async def _http(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        self._ensure_ticker()
        request = await receive()
        method = str(scope.get("method", "GET")).upper()
        headers = list(CORS_HEADERS)
        if method == "OPTIONS":
            await send({"type": "http.response.start", "status": 204, "headers": headers})
            await send({"type": "http.response.body", "body": b""})
            return
        raw_body = request.get("body", b"")
        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = {}
        response = self.api.dispatch(method, scope["path"], payload)
        content = _json_dumps(response.body).encode("utf-8")
        headers.append((b"content-type", b"application/json"))
        await send({"type": "http.response.start", "status": response.status_code, "headers": headers})
        await send({"type": "http.response.body", "body": content})
        if method in _MUTATING_METHODS and response.status_code < 400:
            await self._broadcast()

    async def _websocket(self, receive: Any, send: Any) -> None:
        self._ensure_ticker()
        await receive()  # websocket.connect
        await send({"type": "websocket.accept"})
        self._sockets.append(send)
        try:
            await send({"type": "websocket.send", "text": _json_dumps(control_room_message(self.api))})
            while True:
                event = await receive()
                if event["type"] == "websocket.disconnect":
                    return
                if event["type"] == "websocket.receive":
                    await send({"type": "websocket.send", "text": _json_dumps(control_room_message(self.api))})
        finally:
            if send in self._sockets:
                self._sockets.remove(send)


def create_demo_app() -> SimulationAsgiApp:
    """Factory for uvicorn: enables the demo ticker, not used by unit tests."""

    hz = float(os.environ.get("THIRD_EYE_DEMO_TICK_HZ", str(DEFAULT_DEMO_TICK_HZ)))
    return SimulationAsgiApp(demo_tick_hz=hz)
