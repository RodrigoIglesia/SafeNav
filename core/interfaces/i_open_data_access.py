from typing import Protocol
from domain.dto.urban_data import UrbanData
from domain.dto.common import Area


class IOpenDataAccess(Protocol):
    """
    Interface for accessing external open urban data (E3).
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
