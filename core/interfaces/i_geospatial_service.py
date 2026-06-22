# core/interfaces/i_geospatial_service.py
from typing import Protocol
from domain.dto.routes import RouteCandidates
from domain.dto.geospatial import ContextDescription


class IGeoService(Protocol):
    """
    Interface for geospatial context generator (GE).
    Implemented by Geospatial Engine to generate a context description of each route.
    """

    def get_routes_context(self, routes: RouteCandidates) -> ContextDescription:
        """
        Generate a context representation for multiple route candidates
        (e.g., weather and urban features).

        - routes: Set of candidate routes to generate the context
        - returns: ContextDescription with information relative to weather and urban data
        """
        ...