from typing import Protocol

from domain.dto.map_data import GraphData


class IRoadGraphAccess(Protocol):
    """
    Provides access to the road graph used by the Routing Engine.

    Implemented by Data Management.
    """

    def get_graph_data(self) -> GraphData:
        """
        Retrieve the navigable road graph currently configured for SafeNav.

        Returns:
            Complete GraphData used by the Routing Engine.
        """
        ...