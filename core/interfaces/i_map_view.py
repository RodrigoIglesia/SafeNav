# interfaces/map_view.py

from typing import Protocol
from domain.dto.map_data import MapData
from domain.dto.map_data import MapRequest


class I_MapView(Protocol):
    """
    Interface for map visualization data retrieval.

    Provides map data optimized for GUI rendering.
    Implemented by Data Management.
    """

    def get_map_view(self, request: MapRequest) -> MapData:
        """
        Retrieve map data for visualization purposes.

        :param request: MapRequest describing area and zoom level
        :return: MapData prepared for GUI rendering
        """
        ...
