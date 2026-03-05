"""
SafeNav Core - Data Management Service
-------------------------------------------------------------
"""
#TODO: This module provides a mock implementation of Data Management. It simulates access to map and graph data without connecting to external services. Replace _mock_graph with real data retrieval logic in production.

from datetime import datetime
from typing import List

from interfaces.i_road_graph_access import I_RoadGraphAccess
from domain.dto.map_data import GraphData, Edge
from domain.dto.common import GeoPoint


class DataManagement(I_RoadGraphAccess):

    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area):
        """
        Returns mock graph data for routing.
        """

        return self._build_mock_graph()


    def _build_mock_graph(self) -> GraphData:
        """
        Creates a small mock graph with two connected nodes.
        """

        node_a = GeoPoint(lat=40.4168, lon=-3.7038)
        node_b = GeoPoint(lat=40.4379, lon=-3.6793)

        edge = Edge(
            from_node=node_a,
            to_node=node_b,
            weight=1.0,
        )

        graph = GraphData(
            nodes=[node_a, node_b],
            edges=[edge],
        )

        return graph
