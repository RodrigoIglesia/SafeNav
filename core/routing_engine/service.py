# core/routing_engine/service.py
"""
Routing Engine - Mock Implementation
------------------------------------
Implements the IRoutingService interface.
This version returns mock data for development/testing.
"""

from domain.dto.routes import RouteRequest, RouteCandidate, RouteCandidates, RouteScores, RouteScore
from datetime import datetime, timezone
from interfaces.i_routing_service import IRoutingService
from interfaces.i_road_graph_access import I_RoadGraphAccess
from uuid import uuid4

# Scenario 2 - Calculate routes
class RoutingEngine(IRoutingService):
    """Implements IRoutingService."""
    def __init__(self, road_graph_access: I_RoadGraphAccess):
        self.road_graph_access = road_graph_access

    def calculate_routes(self, request: RouteRequest) -> RouteCandidates:
        """
        Generate route candidates for a given request.
        """

        candidate = RouteCandidate(
            id=str(uuid4()),
            geometry={
                "coordinates": [
                    request.origin,
                    request.destination,
                ]
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
