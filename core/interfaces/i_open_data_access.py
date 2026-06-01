from domain.dto.urban_data import UrbanData
from domain.dto.weather_data import WeatherData
from domain.dto.common import Area

from datetime import datetime
from typing import Protocol


class IOpenDataAccess(Protocol):
    """
    Interface for accessing external open data (E3).
    Implemented by Data Management to communicate with OpenDataAPI.
    """

    def fetch_urban_data(self, area: Area, data_type: str) -> UrbanData:
        """
        Retrieves urban features such as shade zones, water points, or POIs.
        - area: Geographic area of interest
        - data_type: Type of requested data (e.g., "shade", "water", "poi")
        - returns: UrbanData object with the requested elements
        """
        ...

    def fetch_weather_data(self, area: Area, time: datetime) -> WeatherData:
        """
        Retrieves current or forecast weather data for a given area and time.
        - area: Geographic area of interest
        - time: Timestamp for which data is requested
        - returns: WeatherData with temperature, UV index, and alerts
        """
        ...
