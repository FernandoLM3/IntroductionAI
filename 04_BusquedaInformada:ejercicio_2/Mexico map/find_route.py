#!/usr/bin/env python3
"""A* route finding on the Mexico 1,000-city graph (CLI).

Example:
    python find_route.py --from-city Tijuana --to Cancún

State = a city node. Action = travel to a neighbour. Step cost = edges[].km.
Heuristic = haversine straight-line distance to the goal (admissible).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from search.cli import run  # noqa: E402

if __name__ == "__main__":
    run()
