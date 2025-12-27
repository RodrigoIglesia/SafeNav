#TODO: Reformular y crear interfaces de IMapDataAccess e IGraphDataAccess

# core/interfaces/i_data_access.py
from typing import Protocol
from datetime import datetime
from domain.dto.common import Area
from domain.dto.map_data import MapData
from domain.dto.weather_data import WeatherData
from domain.dto.urban_data import UrbanData


class IDataAccess(Protocol):
    """
    Internal data access interface.
    Implemented by DataManagement to provide unified access
    to preprocessed and cached external data.
    """

    def get_map_data(self, area: Area) -> MapData:
        """
        Returns preprocessed map data for a given area.

        - area: Geographic area of interest
        - returns: MapData (road graph, tiles, metadata)
        """
        ...

    def get_weather_data(self, time: datetime) -> WeatherData:
        """
        Returns processed weather data for a specific time.

        - time: Timestamp for which data is needed
        - returns: WeatherData (temperature, UV index, alerts)
        """
        ...

    def get_urban_data(self, area: Area) -> UrbanData:
        """
        Returns urban context data such as shadow zones and POIs.

        - area: Geographic area of interest
        - returns: UrbanData (shade, water points, POIs)
        """
        ...
