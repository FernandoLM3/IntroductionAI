"""Road-map graph for the Mexico 1,000-city proximity graph.

Cities are keyed by their string node id (the ``id`` field in
``mexico_cities_graph.json``). Edges are undirected and weighted by
``edges[].km`` (haversine kilometres), built as 4-nearest-neighbors unioned
with a minimum spanning tree, so the graph is one connected component.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the "Mexico map" folder
GRAPH_PATH = ROOT / "mexico_cities_graph.json"


class Graph:
    """Undirected weighted graph over string city ids."""

    def __init__(self) -> None:
        self._adj: dict[str, dict[str, float]] = defaultdict(dict)

    def add_undirected(self, a: str, b: str, cost: float) -> None:
        self._adj[a][b] = cost
        self._adj[b][a] = cost

    def cities(self) -> list[str]:
        return sorted(self._adj, key=int)

    def has_city(self, city: str) -> bool:
        return city in self._adj

    def neighbors(self, city: str) -> list[tuple[str, float]]:
        return sorted(self._adj[city].items(), key=lambda kv: int(kv[0]))

    def cost(self, a: str, b: str) -> float:
        if b not in self._adj[a]:
            raise KeyError(f"no edge between {a} and {b}")
        return self._adj[a][b]

    def edge_count(self) -> int:
        return sum(len(nbrs) for nbrs in self._adj.values()) // 2


def load_mexico() -> tuple[Graph, dict[str, dict]]:
    """Load the Mexico graph and a ``{id: node}`` lookup of city metadata."""
    data = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    graph = Graph()
    for edge in data["edges"]:
        graph.add_undirected(str(edge["source"]), str(edge["target"]), edge["km"])
    nodes = {str(node["id"]): node for node in data["nodes"]}
    return graph, nodes


def mexico_map() -> Graph:
    graph, _nodes = load_mexico()
    return graph
