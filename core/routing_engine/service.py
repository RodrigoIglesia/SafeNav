# core/routing_engine/service.py
"""
Routing Engine
------------------------------------
Implements the IRoutingService interface.
"""

from domain.dto.routes import RouteRequest, RouteCandidate, RouteCandidates, RouteScores, RouteScore
from domain.dto.common import Point, GeoPoint, Area
from interfaces.i_routing_service import IRoutingService
from interfaces.i_road_graph_access import I_RoadGraphAccess

from routing_engine.modules.router import Router

from common.utils import haversine_distance_m
from typing import List
from uuid import uuid4


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
        area = self._build_area_from_points(request.origin, request.destination)
        # TODO: We need to pass the area because downloading the entire city graph is too heavy. Do we need city in the interface?
        graph = self.road_graph_access.get_graph_data(area)
        print(f"RE: Retrieved graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        # Estimate route
        # Search the origin and destination points in the graph
        graph_origin = self._search_nearest_point(graph.nodes, request.origin)
        print(f"RE: Route origin set to {graph_origin}.")
        
        graph_destination = self._search_nearest_point(graph.nodes, request.destination)
        print(f"RE: Route destination set to {graph_destination}.")
        print(f"RE: Calculating route from {(graph_origin.lat, graph_origin.lon)} to {(graph_destination.lat, graph_destination.lon)} coordinates.")

        # Load Router class
        router = Router(graph, graph_origin, graph_destination)

        # Apply Dijkstra path planner
        # TODO: Apply more planner algorithms (paralel?)
        path = router._dijkstra()
        print(f"RE: path candidate obtained: {len(path)} points.")

        candidate = RouteCandidate(
            id=str(uuid4()),
            geometry={
                "coordinates": path
            },
            #TODO: calculate proper values
            eta=900,
            distance=1.2,
        )

        return RouteCandidates(
            request_id=str(uuid4()),
            items = [candidate]
        )

    def get_route_scores(self, candidates: RouteCandidates) -> RouteScores:
        """
        Retrieve evaluated scores for a previously generated route request.
        """

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

    def _build_area_from_points(self, origin: Point, destination: Point) -> Area:
        # Compute the center as the midpoint
        center_lat = (origin.lat + destination.lat) / 2
        center_lon = (origin.lon + destination.lon) / 2
        center = Point(lat=center_lat, lon=center_lon)

        # Compute radius as half the distance between points
        radius_m = haversine_distance_m(origin, destination) / 2

        return Area(center=center, radius_m=radius_m)
    

    def _search_nearest_point(self, nodes: List[GeoPoint], point: Point) -> GeoPoint:
        """Return the GeoPoint in nodes closest to the input Point."""
        nearest = min(nodes, key=lambda node: haversine_distance_m(point, node))
        
        return nearest