"""Static fictional topology and deterministic routes for the virtual mine."""

from __future__ import annotations

from third_eye.simulation.models import (
    Bench,
    CliffBoundary,
    Intersection,
    LocalCoordinate,
    MineArea,
    MineTopology,
    RoadSegment,
    RouteDefinition,
    SafeZone,
)


def build_virtual_mine_topology() -> MineTopology:
    """Build the fixed fictional local-coordinate mine used by Phase 2."""

    return MineTopology(
        mine_area=MineArea(
            "MINE-01",
            "Third Eye Demonstration Mine",
            (
                LocalCoordinate(-150, -200), LocalCoordinate(800, -200),
                LocalCoordinate(800, 550), LocalCoordinate(-150, 550),
            ),
        ),
        benches=(
            Bench("BENCH-N", "North Bench", (LocalCoordinate(0, 0), LocalCoordinate(650, 0), LocalCoordinate(650, 250), LocalCoordinate(0, 250))),
            Bench("BENCH-S", "South Bench", (LocalCoordinate(0, 250), LocalCoordinate(650, 250), LocalCoordinate(650, 500), LocalCoordinate(0, 500))),
        ),
        safe_zones=(
            SafeZone("SAFE-N", "North Refuge Bay", (LocalCoordinate(120, 60), LocalCoordinate(190, 60), LocalCoordinate(190, 130), LocalCoordinate(120, 130))),
            SafeZone("SAFE-S", "South Refuge Bay", (LocalCoordinate(430, 280), LocalCoordinate(500, 280), LocalCoordinate(500, 350), LocalCoordinate(430, 350))),
        ),
        cliff_boundaries=(
            CliffBoundary("CLIFF-E", "East Drop-off", LocalCoordinate(700, -50), LocalCoordinate(700, 450)),
            CliffBoundary("CLIFF-N", "North Highwall", LocalCoordinate(80, 470), LocalCoordinate(620, 470)),
        ),
        intersections=(
            Intersection("INT-01", "North Switchback", LocalCoordinate(400, 0), True),
            Intersection("INT-02", "Central Junction", LocalCoordinate(300, 200), False),
            Intersection("INT-03", "South Curve", LocalCoordinate(550, 50), True),
        ),
        road_segments=(
            RoadSegment("HN01", "North Haul East", LocalCoordinate(0, 0), LocalCoordinate(400, 0), "SAFE-N"),
            RoadSegment("HN02", "North Switchback", LocalCoordinate(400, 0), LocalCoordinate(600, 200), "SAFE-N", True),
            RoadSegment("HN03", "North Bench Return", LocalCoordinate(600, 200), LocalCoordinate(250, 400), "SAFE-S"),
            RoadSegment("HN04", "North Loop Descent", LocalCoordinate(250, 400), LocalCoordinate(0, 0), "SAFE-N"),
            RoadSegment("HS01", "South Haul East", LocalCoordinate(50, 50), LocalCoordinate(350, -100), "SAFE-N"),
            RoadSegment("HS02", "South Blind Curve", LocalCoordinate(350, -100), LocalCoordinate(650, 50), "SAFE-S", True),
            RoadSegment("HS03", "South Ramp", LocalCoordinate(650, 50), LocalCoordinate(450, 350), "SAFE-S"),
            RoadSegment("HS04", "South Loop Return", LocalCoordinate(450, 350), LocalCoordinate(50, 50), "SAFE-S"),
            RoadSegment("HC01", "Central Access", LocalCoordinate(-50, 200), LocalCoordinate(300, 200), "SAFE-N"),
            RoadSegment("HC02", "Central Curve", LocalCoordinate(300, 200), LocalCoordinate(550, 50), "SAFE-S", True),
            RoadSegment("HC03", "East Ramp", LocalCoordinate(550, 50), LocalCoordinate(700, 300), "SAFE-S"),
            RoadSegment("HC04", "Central Return", LocalCoordinate(700, 300), LocalCoordinate(-50, 200), "SAFE-N"),
        ),
        routes=(
            RouteDefinition("ROUTE-N", "North Bench Loop", ("HN01", "HN02", "HN03", "HN04")),
            RouteDefinition("ROUTE-S", "South Bench Loop", ("HS01", "HS02", "HS03", "HS04")),
            RouteDefinition("ROUTE-C", "Central Access Loop", ("HC01", "HC02", "HC03", "HC04")),
        ),
    )

