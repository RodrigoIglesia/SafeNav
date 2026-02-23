"""
SafeNav Core - Data Management Service
-------------------------------------------------------------
"""
#TODO: This module provides a mock implementation of Data Management. It simulates access to map and graph data without connecting to external services. Replace _mock_graph with real data retrieval logic in production.

from datetime import datetime
from typing import List

from interfaces.i_map_view import I_MapView
from interfaces.i_road_graph_access import I_RoadGraphAccess
from domain.dto.map_data import (
    MapData,
    MapMetadata,
    GraphData,
    Edge,
    Tile
)
from domain.dto.common import GeoPoint, Polygon


class DataManagement(I_MapView, I_RoadGraphAccess):
    """
    Mock implementation of Data Management.
    Provides fake map and graph data for development and testing.
    """

    # ==========================================================
    # I_MapView implementation
    # ==========================================================
    def get_map_view(self, map_request):
        metadata = MapMetadata(
            source="MockMapProvider",
            date=datetime.utcnow(),
            zoom_level=map_request.zoom_level,
        )

        map_data = MapData(
            tiles=self._build_mock_tiles(map_request), # TODO: Replace with get_graph_data() for real tile data retrieval
            metadata=metadata,
        )

        return map_data


    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area):
        """
        Returns mock graph data for routing.
        """

        return self._build_mock_graph()

    # ==========================================================
    # Internal helper: build a tiny mock graph and tiles
    # ==========================================================
    def _build_mock_tiles(self, map_request) -> List[Tile]:

        tile_1 = Tile(
            id="tile_1",
            bounds=Polygon(
                coordinates=[
                    GeoPoint(lat=40.40, lon=-3.72),
                    GeoPoint(lat=40.40, lon=-3.70),
                    GeoPoint(lat=40.42, lon=-3.70),
                    GeoPoint(lat=40.42, lon=-3.72),
                    GeoPoint(lat=40.40, lon=-3.72),  # close polygon
                ]
            )
        )

        tile_2 = Tile(
            id="tile_2",
            bounds=Polygon(
                coordinates=[
                    GeoPoint(lat=40.42, lon=-3.70),
                    GeoPoint(lat=40.42, lon=-3.68),
                    GeoPoint(lat=40.44, lon=-3.68),
                    GeoPoint(lat=40.44, lon=-3.70),
                    GeoPoint(lat=40.42, lon=-3.70),
                ]
            )
        )

        return [tile_1, tile_2]

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
