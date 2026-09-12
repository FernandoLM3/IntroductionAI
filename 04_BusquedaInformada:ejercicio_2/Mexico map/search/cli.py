"""Shared CLI and result printing for A* search on the Mexico graph."""

from __future__ import annotations

import argparse
import sys
import unicodedata
from collections.abc import Callable

from romania.heuristics import heuristic_for
from romania.map import Graph, load_mexico
from romania.problem import RouteFindingProblem
from search.astar import a_star_search
from search.result import SearchResult

MAX_PATH_SHOWN = 7  # first/last cities printed when a path is long


def normalize(text: str) -> str:
    """Lowercase and strip accents so 'Cancún' == 'cancun'."""
    decomposed = unicodedata.normalize("NFD", text)
    without_accents = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return without_accents.strip().lower()


def search_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--from-city", dest="start", default=None, help="Origin city name")
    group.add_argument("--from-id", dest="start_id", default=None, help="Origin city id (disambiguates repeated names)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--to", dest="goal", default=None, help="Destination city name")
    group.add_argument("--to-id", dest="goal_id", default=None, help="Destination city id (disambiguates repeated names)")
    return parser


def resolve_city(nodes: dict[str, dict], query: str, role: str) -> dict:
    """Resolve a city name to its node, choosing the most populous when ambiguous.

    Repeated names (~39 in the graph, e.g. "Puebla", "Guadalupe") are never
    picked silently: the alternatives are printed to stderr.
    """
    key = normalize(query)
    exact = [n for n in nodes.values() if normalize(n["name"]) == key]
    if exact:
        chosen = max(exact, key=lambda n: n["population"])
        alternatives = [n for n in exact if n["id"] != chosen["id"]]
        if alternatives:
            print(f"Note: '{query}' matches {len(exact)} cities; using the most populous.", file=sys.stderr)
            print(f"      chosen {role}: {chosen['name']} ({chosen['state']}, id={chosen['id']}, pop={chosen['population']:,})", file=sys.stderr)
            for alt in alternatives:
                print(f"      alternative: {alt['name']} ({alt['state']}, id={alt['id']}, pop={alt['population']:,})", file=sys.stderr)
        return chosen
    contains = [n for n in nodes.values() if key in normalize(n["name"])]
    if contains:
        chosen = max(contains, key=lambda n: n["population"])
        print(f"Note: no exact match for '{query}'; using closest match '{chosen['name']}' ({chosen['state']}, id={chosen['id']}).", file=sys.stderr)
        return chosen
    prefix = [n for n in nodes.values() if normalize(n["name"]).startswith(key)]
    if prefix:
        chosen = max(prefix, key=lambda n: n["population"])
        print(f"Note: no exact match for '{query}'; using closest match '{chosen['name']}' ({chosen['state']}, id={chosen['id']}).", file=sys.stderr)
        return chosen
    raise ValueError(f"city not found: {query!r}")


def resolve_args(graph: Graph, nodes: dict[str, dict], args: argparse.Namespace) -> tuple[dict, dict]:
    """Resolve the --from/--to (name or id) arguments into start and goal nodes."""
    if args.start is None and args.start_id is None:
        print("Error: provide --from-city <name> (or --from-id <id>)", file=sys.stderr)
        sys.exit(1)
    if args.goal is None and args.goal_id is None:
        print("Error: provide --to <name> (or --to-id <id>)", file=sys.stderr)
        sys.exit(1)

    if args.start_id is not None:
        start_node = nodes.get(str(args.start_id))
        if start_node is None:
            print(f"Error: --from-id {args.start_id} out of range", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            start_node = resolve_city(nodes, args.start, "origin")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    if args.goal_id is not None:
        goal_node = nodes.get(str(args.goal_id))
        if goal_node is None:
            print(f"Error: --to-id {args.goal_id} out of range", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            goal_node = resolve_city(nodes, args.goal, "destination")
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    return start_node, goal_node


def make_problem(graph: Graph, start_id: str, goal_id: str) -> RouteFindingProblem:
    return RouteFindingProblem(graph, start_id, goal_id)


def format_path(nodes: dict[str, dict], path: list[str], max_shown: int = MAX_PATH_SHOWN) -> str:
    names = [nodes[city]["name"] for city in path]
    if len(names) <= 2 * max_shown:
        return " → ".join(names)
    head = names[:max_shown]
    tail = names[-max_shown:]
    hidden = len(names) - 2 * max_shown
    return " → ".join(head) + f" → … ({hidden} más) … → " + " → ".join(tail)


def print_result(
    name: str,
    problem: RouteFindingProblem,
    result: SearchResult,
    h: Callable[[str], float],
    h_label: str,
    nodes: dict[str, dict],
) -> None:
    start_name = nodes[problem.start]["name"]
    goal_name = nodes[problem.goal]["name"]
    print(f"Algorithm: {name}")
    print(f"Problem:   {start_name} → {goal_name}")
    print(f"Heuristic: {h_label}")
    print(f"Status:    {result.status}")
    if result.extra:
        print(f"Detail:    {result.extra}")
    if result.node is not None:
        print(f"Path:      {format_path(nodes, result.path)}")
        print(f"Depth:     {result.depth} hops")
        print(f"Cost:      {result.cost:.2f} km")
    print()
    print(f"Expanded:  {result.nodes_expanded} nodes")
    print(f"Generated: {result.nodes_generated} nodes")
    print(f"Frontier:  max size {result.max_frontier}")


def run(argv: list[str] | None = None) -> None:
    """Run the full A* route-finding CLI (used by find_route.py)."""
    parser = search_parser("A* search: expand lowest f(n) = g(n) + h(n).")
    args = parser.parse_args(argv)
    graph, nodes = load_mexico()
    start_node, goal_node = resolve_args(graph, nodes, args)

    start_id, goal_id = str(start_node["id"]), str(goal_node["id"])

    if start_id == goal_id:
        print("Algorithm: A* search")
        print(f"Problem:   {start_node['name']} → {goal_node['name']}")
        print("Heuristic: haversine straight-line distance to goal (admissible)")
        print("Status:    success (start == goal)")
        print(f"Path:      {start_node['name']}")
        print("Depth:     0 hops")
        print("Cost:      0.00 km")
        print("Expanded:  0 nodes")
        return

    problem = make_problem(graph, start_id, goal_id)
    h, label = heuristic_for(goal_id, nodes)
    result = a_star_search(problem, h)
    print_result("A* search", problem, result, h, label, nodes)
