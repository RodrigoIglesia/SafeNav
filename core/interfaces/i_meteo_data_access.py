from typing import Protocol
from domain.dto.weather_data import WeatherData
from domain.dto.common import Area
from datetime import datetime


class IMeteoDataAccess(Protocol):
    """
    Interface for accessing external meteorological data (E2).
    Implemented by Data Management to communicate with MeteoAPI.
    """

    def fetch_weather_data(self, area: Area, time: datetime) -> WeatherData:
        """
        Retrieves current or forecast weather data for a given area and time.
        - area: Geographic area of interest
        - time: Timestamp for which data is requested
        - returns: WeatherData with temperature, UV index, and alerts
        """
        ...
