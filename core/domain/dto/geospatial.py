"""
geospatial.py
------------
Defines internal data structures related to geospatial representations of an area
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .common import GeoPoint, Polygon


#=== Weather context ===

class WeatherObservation(BaseModel):
    location: GeoPoint = Field(..., description="Geospatial location of a metereological observation")
    temperature: float = Field(..., description="Temperature in celsius at the observation location and time")
    uv_index: float = Field(..., description= "Ultraviolet Index (UVI) at the observation location and time. From 0 (minimal risk) to 11+ (extreme risk).")
    precipitation: float = Field(..., description="Volume of precipitation in m3 at the observation location and time. 0 if no precipitation.")
    wind_speed: float = Field(..., description="Wind speed in km/h at the observation location and time.")
    timestamp: datetime = Field(..., description="Timestamp in EPOCH format of the observation")

class WeatherContext(BaseModel):
    observations: List[WeatherObservation] = Field(...)
    alert_level: Optional[str] = Field(None, description="Possible raised alerts in a zone")

#=== Urban context ===

class ShadowZone(BaseModel):
    id: str
    geometry: Polygon
    source: str

class WaterPoint(BaseModel):
    id: str
    location: GeoPoint
    potable: bool

class PoliceOffice(BaseModel):
    id: str
    location: GeoPoint
    open_now: bool
    is_24h: bool

class Park(BaseModel):
    id: str
    geometry: Polygon
    area_m2: float

class Bench(BaseModel):
    id: str
    location: GeoPoint
    covered: bool

class UrbanContext(BaseModel):
    shadow_zones: List[ShadowZone]
    water_points: List[WaterPoint]
    police_offices: List[PoliceOffice]
    parks: List[Park]
    benches: List[Bench]

#=== Context Description ===

class RouteContext(BaseModel):
    route_id: str = Field(..., description="Unique identifier for the candidate route")
    weather: WeatherContext
    urban: UrbanContext

class ContextDescription(BaseModel):
    items: List[RouteContext] = Field(..., description="List of contextual descriptions of each route candidate")


