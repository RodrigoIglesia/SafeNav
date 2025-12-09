from abc import ABC, abstractmethod
from core.domain.dto.routes import RouteRequest
from core.domain.dto.route_response import RouteResponse

class I_HTTP_Routes(ABC):
    """Defines the HTTP contract for route requests/responses."""

    @abstractmethod
    def route_request(self, request: RouteRequest) -> RouteResponse:
        """Handles a route request from the user interface."""
        pass

    @abstractmethod
    def get_route_results(self, request_id: str) -> RouteResponse:
        """Returns the results of a previously submitted route request."""
        pass