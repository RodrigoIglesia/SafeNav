# interfaces/road_graph_access.py

from typing import Protocol
from domain.dto.map_data import GraphData

class I_RoadGraphAccess(Protocol):
    """
    Interface for accessing road graph data used by the Routing Engine.

    Implemented by Data Management.
    """

    def get_graph_data(self, city) -> GraphData:
        """
        Retrieve a navigable road graph for a given geographic area.

        :param: city from which the graph will be retrieved - By default Madrid
        :return: GraphData containing nodes and edges
        """
        ...
