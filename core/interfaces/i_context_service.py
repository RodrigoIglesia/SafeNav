from typing import Protocol

from domain.dto.geospatial import ContextDescription
from domain.dto.routes import RouteCandidates, RouteScores


class IContextService(Protocol):
    """
    Provides contextual evaluation of route candidates.

    Implemented by Context Analyzer (CA).
    """

    def evaluate_routes(
        self,
        routes: RouteCandidates,
        context: ContextDescription,
    ) -> RouteScores:
        """
        Evaluate route candidates using their contextual description.

        Args:
            routes:
                Route candidates to evaluate.
            context:
                Weather and urban context associated with the routes.

        Returns:
            Comfort and safety scores for the evaluated routes.
        """
        ...