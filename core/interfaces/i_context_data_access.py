from typing import Protocol

from domain.dto.geospatial import (
    UrbanData,
    UrbanDataRequest,
    WeatherData,
    WeatherDataRequest,
)


class IContextDataAccess(Protocol):
    """
    Provides access to contextual data required by the Geospatial Engine.

    Implemented by Data Management.
    """

    def get_weather_data(
        self,
        request: WeatherDataRequest,
    ) -> WeatherData:
        """
        Retrieve weather data for the requested geographic area and
        temporal interval.
        """
        ...

    def get_urban_data(
        self,
        request: UrbanDataRequest,
    ) -> UrbanData:
        """
        Retrieve urban data for the requested geographic area and
        requested feature types.
        """
        ...