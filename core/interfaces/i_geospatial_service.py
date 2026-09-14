from typing import Protocol

from domain.dto.geospatial import ContextDescription
from domain.dto.routes import RouteCandidates


class IGeospatialService(Protocol):
    """
    Provides geospatial context descriptions for route candidates.

    Implemented by Geospatial Engine (GE).
    """

    def get_routes_context(
        self,
        routes: RouteCandidates,
    ) -> ContextDescription:
        """
        Generate contextual descriptions for the supplied route candidates.

        Returns weather and urban context associated with each route.
        """
        ...