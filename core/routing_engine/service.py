# core/routing_engine/service.py
"""
Routing Engine
------------------------------------
Implements the IRoutingService interface.
"""

from domain.dto.routes import RouteRequest, RouteCandidate, RouteCandidates, RouteScores, RouteScore
from interfaces.i_routing_service import IRoutingService
from interfaces.i_road_graph_access import I_RoadGraphAccess

from routing_engine.modules.router import Router

from common.utils import search_nearest_point, build_area_from_points
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class RoutingEngine(IRoutingService):
    """
    Implements IRoutingService.
    """
    
    def __init__(self, road_graph_access: I_RoadGraphAccess):
        self.road_graph_access = road_graph_access

    def calculate_routes(self, request: RouteRequest) -> RouteCandidates:
        """
        Generate route candidates for a given request.
        """

        #TODO: Change to logging
        print(f"RE: Calculating routes from {request.origin} to {request.destination} with preferences {request.preferences}")

        # Calculate Area to request the Graph to calculate routes
        area = build_area_from_points(request.origin, request.destination)
        # TODO: We need to pass the area because downloading the entire city graph is too heavy. Do we need city in the interface?
        graph = self.road_graph_access.get_graph_data(area)
        print(f"RE: Retrieved graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        # Estimate route
        # Search the origin and destination points in the graph
        graph_origin = search_nearest_point(graph.nodes, request.origin)
        print(f"RE: Route origin set to {graph_origin}.")
        
        graph_destination = search_nearest_point(graph.nodes, request.destination)
        print(f"RE: Route destination set to {graph_destination}.")
        # TODO: send signal to UI to change loading screen
        print(f"RE: Calculating route from {(graph_origin.lat, graph_origin.lon)} to {(graph_destination.lat, graph_destination.lon)} coordinates.")

        # Load Router class
        router = Router(graph, graph_origin, graph_destination)

        routing_algorithms = {
            "dijkstra_d": partial(router._dijkstra, optimize="distance"),
            "astar_d": partial(router._astar, optimize="distance"),

            "dijkstra_t": partial(router._dijkstra, optimize="eta"),
            "astar_t": partial(router._astar, optimize="eta"),
        }

        # Execute algorithms in parallel
        routes = {}

        with ThreadPoolExecutor(max_workers=len(routing_algorithms)) as executor:

            # Submit all algorithms
            futures = {
                name: executor.submit(method)
                for name, method in routing_algorithms.items()
            }

            # Collect results
            for name, future in futures.items():

                path, distance, eta = future.result()

                routes[name] = {
                    "path": path,
                    "distance": distance,
                    "eta": eta,
                }

        # Debug output
        for name, route in routes.items():
            print(
                f"RE: {name} path: "
                f"{len(route['path'])} points"
                f"Distance: {route['distance']/1000} km."
                f"Time to arrive: {route['eta']/60} min."
            )

        # Generate route candidates
        candidates = []

        for algorithm_name, route in routes.items():

            candidate = RouteCandidate(
                id=str(uuid4()),
                geometry={
                    "coordinates": route["path"]
                },
                eta=route["eta"],
                distance=route["distance"],
            )

            candidates.append(candidate)


        return RouteCandidates(
            request_id=str(uuid4()),
            items=candidates
        )

    def get_route_scores(self, candidates: RouteCandidates) -> RouteScores:
        """
        Retrieve evaluated scores for a previously generated route request.
        """
        # Call context analyzer

        # TODO: Mock score
        scores = []
        for candidate in candidates.items:
            scores.append(
                RouteScore(
                    id=candidate.id,
                    comfort_score=0.75,
                    safety_score=0.85,
                    segment_scores=None,
                )
            )

        return RouteScores(
            scores=scores
        )