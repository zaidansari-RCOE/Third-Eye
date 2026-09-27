"""Demo choreography for the SIH26007 hackathon presentation.

``HackathonScenarioGenerator`` does not simulate anything itself. It is a
thin script runner that calls the existing, frozen ``SimulationApi`` through
its normal REST surface (reset -> scenario -> start -> advance), the same
surface any HTTP client uses. It exists only to sequence those calls into
three named, presentable narratives:

  * BLIND_CURVE_APPROACH     -> Scenario.NORMAL
  * SUDDEN_OBSTACLE_EMERGENCY -> Scenario.OBSTACLE
  * CLIFF_DRIFT_PREVENTION   -> Scenario.CLIFF_EDGE

Two transports are supported:

  * In-process (default): wraps a ``SimulationApi`` instance directly with no
    network involved. This is what the test suite uses.
  * Live HTTP: given ``base_url`` of an already-running ``create_demo_app``
    server, it drives the real endpoints with stdlib ``urllib`` (no extra
    dependency). Because the existing ASGI adapter already broadcasts a
    fresh control-room snapshot over ``/api/simulation/ws`` after every
    mutating HTTP command, any browser connected to the live Control Room or
    Driver HUD updates automatically -- this class never touches the
    WebSocket, and no second WebSocket protocol is introduced.

No telemetry formula, safety rule, safety threshold, V2I formula, or incident
lifecycle rule is changed or reimplemented here.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from third_eye.api.simulation import ApiResponse, SimulationApi

_SCENARIO_FOR_NARRATIVE = {
    "BLIND_CURVE_APPROACH": "NORMAL",
    "SUDDEN_OBSTACLE_EMERGENCY": "OBSTACLE",
    "CLIFF_DRIFT_PREVENTION": "CLIFF_EDGE",
}

_STEP_PLAN_SECONDS: dict[str, tuple[float, ...]] = {
    # D01 cruises HN01 at 24 kph under B01's 30 kph blind-curve advisory, then
    # crosses into the blind-curve segment itself (HN02) by ~70s and clears it
    # safely -- verified against the real engine, not guessed.
    "BLIND_CURVE_APPROACH": (20.0, 20.0, 20.0, 10.0, 10.0, 10.0),
    # D01's forward_lidar_cm shrinks toward the fixed OBSTACLE-scenario obstacle
    # on ROUTE-N; CRITICAL forward_collision + EMERGENCY_OVERRIDE_SIMULATED
    # trigger at ~45s, and the next step shows real simulated deceleration.
    "SUDDEN_OBSTACLE_EMERGENCY": (10.0, 10.0, 10.0, 10.0, 5.0, 5.0),
    # D01 starts essentially on the simulated pit edge (ground_loss / then
    # cliff_proximity), and ordinary forward route progression carries it back
    # to green within ~1.6s -- the "self-correction" is real engine behavior,
    # not a scripted animation.
    "CLIFF_DRIFT_PREVENTION": (0.0, 0.3, 0.3, 1.0, 2.0, 5.0),
}


class HackathonScenarioError(RuntimeError):
    """Raised when a choreography step gets an unexpected API response."""


@dataclass(frozen=True, slots=True)
class ScenarioStep:
    """One choreographed step and the real control-room snapshot right after it."""

    narrative: str
    label: str
    seconds_advanced: float
    control_room_snapshot: dict[str, Any]


class HackathonScenarioGenerator:
    """Scripts the three demo narratives against the one authoritative
    SimulationService, using only SimulationApi's existing REST surface."""

    def __init__(
        self,
        api: SimulationApi | None = None,
        *,
        base_url: str | None = None,
        pace_seconds: float = 0.0,
    ) -> None:
        if api is not None and base_url is not None:
            raise ValueError("Pass either api= or base_url=, not both.")
        if base_url is not None:
            self._api: SimulationApi | None = None
            self._base_url: str | None = base_url.rstrip("/")
        else:
            self._api = api if api is not None else SimulationApi()
            self._base_url = None
        # Real-time pause between steps, useful for a live audience walkthrough.
        # Leave at 0 for tests and scripted/instant runs.
        self.pace_seconds = pace_seconds

    # -- transport -----------------------------------------------------

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._api is not None:
            response: ApiResponse = self._api.dispatch(method, path, payload)
            if response.status_code >= 400:
                raise HackathonScenarioError(f"{method} {path} -> {response.status_code}: {response.body}")
            return response.body

        assert self._base_url is not None
        url = f"{self._base_url}{path}"
        body = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body if method != "GET" else None,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as raw:
                return json.loads(raw.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "ignore")
            raise HackathonScenarioError(f"{method} {path} -> {error.code}: {detail}") from error

    def _control_room(self) -> dict[str, Any]:
        return self._request("GET", "/api/simulation/control-room")

    def _begin(self, scenario: str) -> None:
        self._request("POST", "/api/simulation/reset")
        self._request("POST", "/api/simulation/scenario", {"scenario": scenario})
        self._request("POST", "/api/simulation/start")

    def _advance(self, narrative: str, label: str, seconds: float) -> ScenarioStep:
        self._request("POST", "/api/simulation/advance", {"seconds": seconds})
        if self.pace_seconds:
            time.sleep(self.pace_seconds)
        return ScenarioStep(
            narrative=narrative,
            label=label,
            seconds_advanced=seconds,
            control_room_snapshot=self._control_room(),
        )

    # -- the three hackathon narratives ---------------------------------

    def blind_curve_approach(self, vehicle_id: str = "D01") -> Iterator[ScenarioStep]:
        """Safely guide a truck around a hairpin corner under its V2I advisory.

        Uses the NORMAL scenario: no injected hazard. D01 already cruises at
        24 kph, under beacon B01's real 30 kph advisory for the blind-curve
        segment HN02, so the truck never needs to exceed its safe margin as
        it crosses the switchback. Verified against the real engine: a brief
        forward_collision caution is expected near the segment boundary
        (existing, legitimate behavior, not fabricated for this demo).
        """

        name = "BLIND_CURVE_APPROACH"
        self._begin(_SCENARIO_FOR_NARRATIVE[name])
        for seconds in _STEP_PLAN_SECONDS[name]:
            yield self._advance(name, f"{vehicle_id} approaching blind curve", seconds)

    def sudden_obstacle_emergency(self, vehicle_id: str = "D01") -> Iterator[ScenarioStep]:
        """A truck meets a hazard in deep fog and the simulated brake engages.

        Uses the existing OBSTACLE scenario. Verified against the real
        engine: forward_lidar_cm shrinks as D01 (route ROUTE-N) approaches the
        fixed simulated obstacle, crossing into
        CRITICAL/EMERGENCY_OVERRIDE_SIMULATED at ~45s elapsed, after which the
        next step shows real simulated deceleration (4 kph/s) applied by the
        frozen engine -- not scripted here.
        """

        name = "SUDDEN_OBSTACLE_EMERGENCY"
        self._begin(_SCENARIO_FOR_NARRATIVE[name])
        for seconds in _STEP_PLAN_SECONDS[name]:
            yield self._advance(name, f"{vehicle_id} obstacle emergency", seconds)

    def cliff_drift_prevention(self, vehicle_id: str = "D01") -> Iterator[ScenarioStep]:
        """A truck starts at a pit edge and self-corrects with a warning.

        Uses the existing CLIFF_EDGE scenario. Verified against the real
        engine: D01 starts essentially on the simulated pit edge (a critical
        ground_loss / cliff_proximity reading at t=0), and ordinary forward
        route progression -- not a scripted animation -- carries it back to a
        green zone within about 1.6 simulated seconds.
        """

        name = "CLIFF_DRIFT_PREVENTION"
        self._begin(_SCENARIO_FOR_NARRATIVE[name])
        for seconds in _STEP_PLAN_SECONDS[name]:
            yield self._advance(name, f"{vehicle_id} cliff drift prevention", seconds)

    def run(self, narrative: str, vehicle_id: str = "D01") -> Iterator[ScenarioStep]:
        """Dispatch by narrative name; see the module docstring for the mapping."""

        table: dict[str, Callable[[str], Iterator[ScenarioStep]]] = {
            "BLIND_CURVE_APPROACH": self.blind_curve_approach,
            "SUDDEN_OBSTACLE_EMERGENCY": self.sudden_obstacle_emergency,
            "CLIFF_DRIFT_PREVENTION": self.cliff_drift_prevention,
        }
        try:
            factory = table[narrative]
        except KeyError as error:
            raise HackathonScenarioError(f"Unknown demo narrative: {narrative!r}") from error
        yield from factory(vehicle_id)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a Third Eye hackathon demo narrative against a live server.")
    parser.add_argument("narrative", choices=sorted(_SCENARIO_FOR_NARRATIVE))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--vehicle-id", default="D01")
    parser.add_argument("--pace-seconds", type=float, default=1.0)
    args = parser.parse_args()

    generator = HackathonScenarioGenerator(base_url=args.base_url, pace_seconds=args.pace_seconds)
    for step in generator.run(args.narrative, args.vehicle_id):
        vehicles = step.control_room_snapshot["vehicles"]
        vehicle = next((item for item in vehicles if item["vehicle_id"] == args.vehicle_id), vehicles[0])
        zone = vehicle["safety"]["safety_zone"]
        print(f"[{step.narrative}] {step.label}: +{step.seconds_advanced}s -> safety_zone={zone}")
