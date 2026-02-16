"""
urban_data.py
--------------
Defines internal data transfer objects for urban context information:
- UrbanData: main container for contextual urban data (shade, water, POIs)
- POI: point of interest such as a fountain, bench, or park
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from .common import GeoPoint, Polygon


class POI(BaseModel):
    """Represents a Point of Interest (POI) in the urban environment."""
    id: str = Field(..., description="Unique identifier of the POI")
    name: Optional[str] = Field(None, description="Descriptive name of the POI")
    type: str = Field(..., description="Type of POI (e.g., fountain, tree, bench, park)")
    location: GeoPoint = Field(..., description="Geographic location of the POI")


class UrbanData(BaseModel):
    """Contains urban environmental data relevant for route comfort and safety."""
    shadow_zones: List[Polygon] = Field(
        default_factory=list,
        description="Polygons representing areas with shade (e.g., trees, buildings)"
    )
    water_points: List[GeoPoint] = Field(
        default_factory=list,
        description="List of fountains or public water access points"
    )
    pois: List[POI] = Field(
        default_factory=list,
        description="List of points of interest (parks, benches, shaded areas, etc.)"
    )
