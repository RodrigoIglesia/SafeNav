from typing import Protocol
from domain.dto.map_data import MapData
from domain.dto.common import Area


class IMapDataAccess(Protocol):
    """
    Interface for accessing external map services (E1).
    Implemented by Data Management to communicate with MapAPI.
    """

    def fetch_map_data(self, area: Area) -> MapData:
        """
        Retrieves road network and map layers for a given area.
        - area: Geographic area of interest
        - returns: MapData with road graph, tiles, and metadata
        """
        ...
