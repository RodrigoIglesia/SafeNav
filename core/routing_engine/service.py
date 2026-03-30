# core/routing_engine/service.py
"""
Routing Engine - Mock Implementation
------------------------------------
Implements the IRoutingService interface.
This version returns mock data for development/testing.
"""

from domain.dto.routes import RouteRequest, RouteCandidate, RouteCandidates, RouteScores, RouteScore
from domain.dto.common import Point, GeoPoint, Area
from domain.dto.map_data import GraphData
from interfaces.i_routing_service import IRoutingService
from interfaces.i_road_graph_access import I_RoadGraphAccess
from typing import List
from uuid import uuid4

import heapq
from math import radians, cos, sin, asin, sqrt

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
        graph_destination = self._search_nearest_point(graph.nodes, request.destination)
        print(f"RE: Calculating route from {(graph_origin.lat, graph_origin.lon)} to {(graph_destination.lat, graph_destination.lon)} coordinates.")

        # TODO: Change to models module methods
        path = self._dijkstra(graph, graph_origin, graph_destination)
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
        radius_m = self._haversine_distance_m(origin, destination) / 2

        return Area(center=center, radius_m=radius_m)
    
    def _haversine_distance_m(self, p1, p2) -> float:
        """
        Calculate the great-circle distance in meters between two points.
        The function must accept both Point and GeoPoint
        """
        lat1, lon1, lat2, lon2 = map(
        radians,
        [p1.lat, p1.lon, p2.lat, p2.lon]
        )
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        R = 6371000 # Radius of the Earth in meters
        return R * c

    def _search_nearest_point(self, nodes: List[GeoPoint], point: Point) -> GeoPoint:
        """Return the GeoPoint in nodes closest to the input Point."""
        nearest = min(nodes, key=lambda node: self._haversine_distance_m(point, node))
        
        return nearest
    
    def _dijkstra(self, graph: GraphData, start: GeoPoint, goal: GeoPoint) -> List[GeoPoint]:
        """
        Routing Model: Dijkstra
        Applies Dijkstra algorithm to a graph, using the start and end GeoPoint in the graph.
        """
        # Map node.id → GeoPoint for easy lookup
        node_map = {node.id: node for node in graph.nodes}

        # Initialize distances and previous nodes using IDs
        distances = {node.id: float("inf") for node in graph.nodes}
        previous = {node.id: None for node in graph.nodes}

        distances[start.id] = 0
        pq = [(0, start.id)]  # priority queue of (distance, node_id)

        while pq:
            current_dist, current_id = heapq.heappop(pq)
            current_node = node_map[current_id]

            if current_id == goal.id:
                break

            # Iterate only over edges starting from current node
            for edge in graph.edges:
                if edge.from_node.id == current_id:
                    neighbor_id = edge.to_node.id
                    alt_distance = current_dist + edge.weight

                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current_id
                        heapq.heappush(pq, (alt_distance, neighbor_id))

        # Reconstruct path as list of GeoPoint
        path_ids = []
        node_id = goal.id
        while node_id is not None:
            path_ids.insert(0, node_id)
            node_id = previous[node_id]

        path = [node_map[node_id] for node_id in path_ids]
        return path