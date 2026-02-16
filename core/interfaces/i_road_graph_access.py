# interfaces/road_graph_access.py

from typing import Protocol
from domain.dto.map_data import GraphData
from domain.dto.common import Polygon


class I_RoadGraphAccess(Protocol):
    """
    Interface for accessing road graph data used by the Routing Engine.

    Implemented by Data Management.
    """

    def get_graph_data(self, area: Polygon) -> GraphData:
        """
        Retrieve a navigable road graph for a given geographic area.

        :param area: Geographic area of interest
        :return: GraphData containing nodes and edges
        """
        ...
