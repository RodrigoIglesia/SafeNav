# FIXME: De momento, I_MapDataAccess (externo) devuelve un objeto MapData como IMapView, en un futuro se puede adaptar a la fuente externa.
# core/interfaces/i_data_access.py
from typing import Protocol
from domain.dto.common import Area
from domain.dto.map_data import MapData


class IMapDataAccess(Protocol):
    """
    Internal data access interface.
    Implemented by DataManagement to provide unified access
    to maps external data.
    """

    def fetch_map_data(self, area: Area) -> MapData:
        """
        Returns preprocessed map data for a given area.

        - area: Geographic area of interest
        - returns: MapData (tiles, metadata)
        """
        ...
