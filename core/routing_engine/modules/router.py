# core/routing_engine/modules/router.py
"""
Router Class
------------------------------------
Implements the path planning algorithms of the router.

Performance notes:
- The graph is indexed once into an adjacency list (node -> outgoing edges),
  so each search step only looks at the current node's edges instead of
  scanning every edge in the graph. Complexity goes from O(V * E) to
  O(E log V).
- The index is cached per GraphData object, so several Router instances
  created for the same graph (e.g. multiple route candidates) reuse it.
- Stale priority-queue entries are skipped (lazy deletion).
- Distance/ETA are accumulated from the edges actually used in the path.
"""

# TODO: Review and document algorithms -- investigate further optimization parameters and how to compute them
from domain.dto.common import GeoPoint
from domain.dto.map_data import GraphData

from common.utils import haversine_distance_m

from collections import OrderedDict
from typing import List
import heapq
import threading


class _GraphIndex:
    """
    Precomputed lookup structures for a GraphData object.
    """

    def __init__(self, graph: GraphData):
        self.node_map = {node.id: node for node in graph.nodes}

        # node_id -> list of (to_node_id, weight_d, weight_t, edge)
        self.adjacency: dict = {node_id: [] for node_id in self.node_map}

        max_speed = 0.0

        for edge in graph.edges:
            from_id = edge.from_node.id
            to_id = edge.to_node.id

            weight_d = edge.weight_d
            weight_t = edge.weight_t

            # Edges referencing unknown nodes cannot be routed
            if from_id not in self.node_map or to_id not in self.node_map:
                continue

            self.adjacency[from_id].append((to_id, weight_d, weight_t, edge))

            # Fastest speed in the graph (m/s), used for an admissible
            # A* heuristic when optimizing by travel time.
            if weight_d is not None and weight_t:
                speed = weight_d / weight_t
                if speed > max_speed:
                    max_speed = speed

        self.max_speed_m_s = max_speed


class Router:

    # Small identity-based cache of graph indexes (GraphData may be unhashable)
    _INDEX_CACHE_SIZE = 4
    _index_cache: "OrderedDict[int, tuple]" = OrderedDict()
    _index_lock = threading.Lock()

    def __init__(self, graph: GraphData, start: GeoPoint, goal: GeoPoint):
        self.graph = graph
        self.start = start
        self.goal = goal

        self._index = self._get_index(graph)

    # ----------------------------------------------------------
    # Index cache
    # ----------------------------------------------------------
    @classmethod
    def _get_index(cls, graph: GraphData) -> _GraphIndex:
        key = id(graph)

        with cls._index_lock:
            cached = cls._index_cache.get(key)

            # Check identity: id() values can be reused after garbage collection
            if cached is not None and cached[0] is graph:
                cls._index_cache.move_to_end(key)
                return cached[1]

        index = _GraphIndex(graph)

        with cls._index_lock:
            cls._index_cache[key] = (graph, index)
            cls._index_cache.move_to_end(key)

            while len(cls._index_cache) > cls._INDEX_CACHE_SIZE:
                cls._index_cache.popitem(last=False)

        return index

    # ----------------------------------------------------------
    # Algorithms
    # ----------------------------------------------------------
    def _dijkstra(self, optimize="distance") -> List[GeoPoint]:
        """
        Routing Model: Dijkstra
        Applies Dijkstra algorithm to a graph, using the start and end GeoPoint in the graph.

        Returns (path, distance, eta). If no path exists, returns ([], 0, 0).
        """
        return self._search(optimize, use_heuristic=False)

    def _astar(self, optimize="distance") -> List[GeoPoint]:
        """
        Routing Model: A*
        Faster than Dijkstra using a spatial heuristic:
        - optimize="distance": straight-line (haversine) distance to goal.
        - optimize="eta": straight-line distance / fastest speed in the graph,
          so the heuristic never overestimates travel time.

        Returns (path, distance, eta). If no path exists, returns ([], 0, 0).
        """
        return self._search(optimize, use_heuristic=True)

    def _search(self, optimize: str, use_heuristic: bool):
        path, distance, eta, _ = self._search_full(optimize, use_heuristic)
        return path, distance, eta

    def _search_full(self, optimize: str, use_heuristic: bool, penalties: dict | None = None):
        """
        Core search. `penalties` maps (from_id, to_id) -> multiplier (>= 1)
        applied to the edge weight during the search only. Returned distance
        and ETA always use the real (unpenalized) edge weights.

        Returns (path, distance, eta, path_ids).
        """
        weight_position = self._weight_position(optimize)

        index = self._index
        adjacency = index.adjacency

        start_id = self.start.id
        goal_id = self.goal.id

        if start_id not in index.node_map:
            raise ValueError(f"RE: Start node {start_id} is not in the graph")
        if goal_id not in index.node_map:
            raise ValueError(f"RE: Goal node {goal_id} is not in the graph")

        heuristic = self._build_heuristic(optimize) if use_heuristic else None

        # Only visited/reached nodes are stored (no full-graph initialization)
        cost = {start_id: 0.0}
        previous = {start_id: None}       # node_id -> (prev_node_id, edge_tuple)
        closed = set()

        start_priority = heuristic(start_id) if heuristic else 0.0
        pq = [(start_priority, 0.0, start_id)]

        found = start_id == goal_id

        while pq:
            _, current_cost, current_id = heapq.heappop(pq)

            # Skip stale entries left in the queue
            if current_id in closed:
                continue
            closed.add(current_id)

            if current_id == goal_id:
                found = True
                break

            for edge_tuple in adjacency.get(current_id, ()):
                neighbor_id = edge_tuple[0]

                if neighbor_id in closed:
                    continue

                weight = edge_tuple[weight_position]

                # Dijkstra/A* require non-negative weights
                if weight is None or weight < 0:
                    continue

                if penalties:
                    weight *= penalties.get((current_id, neighbor_id), 1.0)

                new_cost = current_cost + weight

                if new_cost < cost.get(neighbor_id, float("inf")):
                    cost[neighbor_id] = new_cost
                    previous[neighbor_id] = (current_id, edge_tuple)

                    priority = new_cost + heuristic(neighbor_id) if heuristic else new_cost
                    heapq.heappush(pq, (priority, new_cost, neighbor_id))

        if not found:
            print(f"RE: No path found between {start_id} and {goal_id}")
            return [], 0, 0, []

        return self._reconstruct(goal_id, previous)

    def _weight_position(self, optimize: str) -> int:
        # Positions inside the adjacency tuple (to_id, weight_d, weight_t, edge)
        if optimize == "distance":
            return 1
        if optimize == "eta":
            return 2

        raise ValueError(
            f"RE: No valid optimization parameter '{optimize}' (use 'distance' or 'eta')"
        )

    def _build_heuristic(self, optimize: str):
        node_map = self._index.node_map
        goal = self.goal

        if optimize == "distance":
            scale = 1.0
        else:
            max_speed = self._index.max_speed_m_s
            if max_speed <= 0:
                # No usable speed information: fall back to Dijkstra behavior
                return lambda node_id: 0.0
            scale = 1.0 / max_speed

        cache = {}

        def heuristic(node_id):
            value = cache.get(node_id)
            if value is None:
                value = haversine_distance_m(node_map[node_id], goal) * scale
                cache[node_id] = value
            return value

        return heuristic

    def _reconstruct(self, goal_id, previous):
        node_map = self._index.node_map

        path_ids = []
        total_distance = 0
        total_eta = 0

        node_id = goal_id

        while node_id is not None:
            path_ids.append(node_id)

            step = previous.get(node_id)
            if step is None:
                break

            prev_id, (_, weight_d, weight_t, _) = step
            total_distance += weight_d or 0
            total_eta += weight_t or 0

            node_id = prev_id

        path_ids.reverse()

        path = [node_map[nid] for nid in path_ids]

        return path, total_distance, total_eta, path_ids

    # ----------------------------------------------------------
    # Alternative routes
    # ----------------------------------------------------------
    def _alternatives(
        self,
        k: int = 4,
        optimize: str = "eta",
        penalty_factor: float = 1.6,
        max_stretch: float = 1.5,
        max_overlap: float = 0.7,
        max_iterations: int | None = None,
    ):
        """
        Generates up to k alternative routes with the penalty method.

        1. Find the optimal route (always the first result).
        2. Multiply the weight of every edge used by that route (both
           directions) by `penalty_factor`, and search again with A*.
        3. Accept the new route only if:
           - its real cost is <= max_stretch * optimal cost, and
           - it shares at most `max_overlap` of its length with every
             already accepted route.
        4. Repeat until k routes are accepted or max_iterations is reached.

        Returns a list of (path, distance, eta), best first. Empty if no
        path exists.
        """
        if k < 1:
            return []

        max_iterations = max_iterations or k * 4
        cost_position = self._weight_position(optimize)

        penalties: dict = {}
        accepted = []          # list of (path, distance, eta, edge_lengths)
        best_cost = None

        for _ in range(max_iterations):
            path, distance, eta, path_ids = self._search_full(
                optimize, use_heuristic=True, penalties=penalties
            )

            if not path_ids:
                break

            real_cost = distance if cost_position == 1 else eta
            edges = self._path_edge_lengths(path_ids)

            if best_cost is None:
                best_cost = real_cost
                accepted.append((path, distance, eta, edges))
            elif real_cost <= best_cost * max_stretch and all(
                self._overlap_ratio(edges, other_edges) <= max_overlap
                for *_, other_edges in accepted
            ):
                accepted.append((path, distance, eta, edges))

            if len(accepted) >= k:
                break

            # Penalize the edges of the route just found (accepted or not),
            # so the next search explores different streets.
            for from_id, to_id in zip(path_ids[:-1], path_ids[1:]):
                for key in ((from_id, to_id), (to_id, from_id)):
                    penalties[key] = penalties.get(key, 1.0) * penalty_factor

        return [(path, distance, eta) for path, distance, eta, _ in accepted]

    def _path_edge_lengths(self, path_ids) -> dict:
        """
        Undirected edge key -> length (m) for the edges of a path.
        """
        adjacency = self._index.adjacency
        edges = {}

        for from_id, to_id in zip(path_ids[:-1], path_ids[1:]):
            lengths = [
                t[1] for t in adjacency.get(from_id, ())
                if t[0] == to_id and t[1] is not None
            ]
            key = (from_id, to_id) if str(from_id) <= str(to_id) else (to_id, from_id)
            edges[key] = min(lengths) if lengths else 0.0

        return edges

    def _overlap_ratio(self, edges: dict, other_edges: dict) -> float:
        """
        Fraction of the route length (edges) shared with another route.
        """
        total = sum(edges.values())

        if total <= 0:
            return 1.0

        shared = sum(length for key, length in edges.items() if key in other_edges)

        return shared / total

    def _estimate_dist_eta(self, graph, path_ids):
        """
        Auxiliary function to compute the estimated time arrival of a calculated route.

        Kept for compatibility. Uses the adjacency index; when parallel edges
        exist, the shortest one between each pair of nodes is used.
        """
        index = self._index if graph is self.graph else self._get_index(graph)

        total_distance = 0
        total_eta = 0

        for from_id, to_id in zip(path_ids[:-1], path_ids[1:]):
            candidates = [
                edge_tuple
                for edge_tuple in index.adjacency.get(from_id, ())
                if edge_tuple[0] == to_id
            ]

            if not candidates:
                continue

            _, weight_d, weight_t, _ = min(
                candidates,
                key=lambda t: t[1] if t[1] is not None else float("inf"),
            )

            total_distance += weight_d or 0
            total_eta += weight_t or 0

        return total_distance, total_eta