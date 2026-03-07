# core/routing_engine/service.py
"""
Routing Engine - Mock Implementation
------------------------------------
Implements the IRoutingService interface.
This version returns mock data for development/testing.
"""

from domain.dto.routes import RouteRequest, RouteCandidate, RouteCandidates, RouteScores, RouteScore
from domain.dto.common import GeoPoint, Polygon
from datetime import datetime, timezone
from interfaces.i_routing_service import IRoutingService
from interfaces.i_road_graph_access import I_RoadGraphAccess
from uuid import uuid4

import heapq


# Scenario 2 - Calculate routes
class RoutingEngine(IRoutingService):
    """Implements IRoutingService."""
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
        graph = self.road_graph_access.get_graph_data(area)
        print(f"RE: Retrieved graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        # Estimate route
        # TODO: Change to models module methods
        path = self._dijkstra(graph, request.origin, request.destination)


        candidate = RouteCandidate(
            id=str(uuid4()),
            geometry={
                "coordinates": path
            },
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

    def _build_area_from_points(self,origin, destination) -> Polygon:
        min_lat = min(origin.lat, destination.lat)
        max_lat = max(origin.lat, destination.lat)
        min_lon = min(origin.lon, destination.lon)
        max_lon = max(origin.lon, destination.lon)

        return Polygon(
            coordinates=[
                GeoPoint(lat=min_lat, lon=min_lon),
                GeoPoint(lat=min_lat, lon=max_lon),
                GeoPoint(lat=max_lat, lon=max_lon),
                GeoPoint(lat=max_lat, lon=min_lon),
            ]
        )

    def _dijkstra(self, graph, start, goal):
        # TODO: Refine algorithm and move code to models
        distances = {node: float("inf") for node in graph.nodes}
        previous = {}
        distances[start] = 0

        pq = [(0, start)]

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            if current_node == goal:
                break

            for edge in graph.edges:
                if edge.from_node == current_node:
                    neighbor = edge.to_node
                    distance = current_dist + edge.weight

                    if distance < distances[neighbor]:
                        distances[neighbor] = distance
                        previous[neighbor] = current_node
                        heapq.heappush(pq, (distance, neighbor))

        # reconstruct path
        path = []
        node = goal
        while node in previous:
            path.insert(0, node)
            node = previous[node]
        path.insert(0, start)

        return path
