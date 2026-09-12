#!/usr/bin/env python3
"""Program 4: A* search on the Mexico 1,000-city graph.

Thin entry point that reuses the same CLI as find_route.py:
    python 04_a_star_search.py --from-city Tijuana --to Cancún
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from search.cli import run  # noqa: E402

if __name__ == "__main__":
    run()
