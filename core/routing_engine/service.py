# core/routing_engine/service.py
"""
Routing Engine
------------------------------------
Implements the IRoutingService interface.
"""

from domain.dto.common import Area
from domain.dto.routes import RouteRequest, RouteCandidate, RouteCandidates
from interfaces.i_routing_service import IRoutingService
from interfaces.i_road_graph_access import IRoadGraphAccess

from routing_engine.modules.router import Router

from common.utils import search_nearest_point, build_area_from_points
from uuid import uuid4
import time


class RoutingEngine(IRoutingService):
    """
    Implements IRoutingService.
    """

    # TODO: Move to configuration / route request preferences
    # Candidate generation (penalty method, see Router._alternatives).
    # The candidates are later evaluated by safety/comfort, so they should be
    # genuinely different routes of reasonable length, not only the fastest.
    MAX_CANDIDATES = 4          # including the optimal route
    OPTIMIZE = "eta"            # base cost: "eta" or "distance"
    PENALTY_FACTOR = 1.6        # weight multiplier for already used streets
    MAX_STRETCH = 1.5           # candidates at most 50% longer than the optimal
    MAX_OVERLAP = 0.7           # candidates share at most 70% of their length

    # Extra area around origin/destination so routes can detour outside the
    # straight-line circle. Cropping the cached city graph is cheap.
    AREA_RADIUS_FACTOR = 1.3
    AREA_MARGIN_M = 500.0

    def __init__(self, road_graph_access: IRoadGraphAccess):
        self.road_graph_access = road_graph_access

    def calculate_routes(self, request: RouteRequest) -> RouteCandidates:
        """
        Generate route candidates for a given request.
        """

        #TODO: Change to logging
        print(f"RE: Calculating routes from {request.origin} to {request.destination} with preferences {request.preferences}")

        t_start = time.perf_counter()

        # Calculate Area to request the Graph to calculate routes
        area = self._build_routing_area(request)

        # TODO: Do we need city in the interface?
        graph = self.road_graph_access.get_graph_data(area)
        print(f"RE: Retrieved graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        t_graph = time.perf_counter()

        # Search the origin and destination points in the graph
        graph_origin = search_nearest_point(graph.nodes, request.origin)
        print(f"RE: Route origin set to {graph_origin}.")

        graph_destination = search_nearest_point(graph.nodes, request.destination)
        print(f"RE: Route destination set to {graph_destination}.")
        # TODO: send signal to UI to change loading screen
        print(f"RE: Calculating route from {(graph_origin.lat, graph_origin.lon)} to {(graph_destination.lat, graph_destination.lon)} coordinates.")

        # Load Router class (builds the graph index once for all algorithms)
        router = Router(graph, graph_origin, graph_destination)

        # Generate diverse alternatives. The first one is the optimal route.
        t0 = time.perf_counter()

        alternatives = router._alternatives(
            k=self.MAX_CANDIDATES,
            optimize=self.OPTIMIZE,
            penalty_factor=self.PENALTY_FACTOR,
            max_stretch=self.MAX_STRETCH,
            max_overlap=self.MAX_OVERLAP,
        )

        print(f"RE: {len(alternatives)} alternatives in {(time.perf_counter() - t0) * 1000:.0f} ms")

        routes = {}

        for index, (path, distance, eta) in enumerate(alternatives):
            name = "optimal" if index == 0 else f"alternative_{index}"

            print(
                f"RE: {name}: {len(path)} points, "
                f"distance: {distance / 1000:.2f} km, "
                f"time to arrive: {eta / 60:.1f} min"
            )

            routes[name] = {
                "path": path,
                "distance": distance,
                "eta": eta,
            }

        # Generate route candidates (skip empty and duplicated paths)
        candidates = []
        seen_paths = set()

        for algorithm_name, route in routes.items():

            if not route["path"]:
                print(f"RE: {algorithm_name} found no path, skipping")
                continue

            path_key = tuple(point.id for point in route["path"])

            if path_key in seen_paths:
                print(f"RE: {algorithm_name} returned a duplicated path, skipping")
                continue

            seen_paths.add(path_key)

            candidate = RouteCandidate(
                id=str(uuid4()),
                geometry={
                    "coordinates": route["path"]
                },
                eta=route["eta"],
                distance=route["distance"],
            )

            candidates.append(candidate)

        if not candidates:
            raise ValueError(
                f"RE: No route found between {request.origin} and {request.destination}"
            )

        t_end = time.perf_counter()
        print(
            f"RE: {len(candidates)} candidates in {t_end - t_start:.2f}s "
            f"(graph: {t_graph - t_start:.2f}s, routing: {t_end - t_graph:.2f}s)"
        )

        return RouteCandidates(
            request_id=str(uuid4()),
            items=candidates
        )

    def _build_routing_area(self, request: RouteRequest) -> Area:
        """
        Area covering origin and destination, enlarged so the best route
        can leave the minimal circle.
        """
        base_area = build_area_from_points([request.origin, request.destination])

        return Area(
            center=base_area.center,
            radius_m=base_area.radius_m * self.AREA_RADIUS_FACTOR + self.AREA_MARGIN_M,
        )