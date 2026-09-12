"""Heuristics for the Mexico graph: haversine straight-line distance.

The straight-line distance on the sphere between a city and the goal is
admissible (it never overestimates the true road distance) and consistent
(it obeys the triangle inequality), so A* returns optimal-cost paths.
"""

from __future__ import annotations

import math
from collections.abc import Callable

EARTH_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(min(1.0, a)))


def heuristic_for(goal: str, nodes: dict[str, dict]) -> tuple[Callable[[str], float], str]:
    """Return h(state) and a short label for the haversine heuristic to goal."""
    goal_node = nodes[goal]

    def h_sld(state: str) -> float:
        node = nodes[state]
        return haversine_km(node["lat"], node["lon"], goal_node["lat"], goal_node["lon"])

    return h_sld, "haversine straight-line distance to goal (admissible)"
