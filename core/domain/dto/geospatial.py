"""
geospatial.py
-------------
Defines internal data structures related to geospatial contextual data:
- Spatial data requests
- Weather data and route weather context
- Urban data and route urban context
- Context descriptions for route candidates
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .common import Area, Point, Polygon


# === Generic spatial request ===

class SpatialDataRequest(BaseModel):
    """Base request for contextual data covering a geographic area."""

    covered_area: Area = Field(
        ...,
        description="Geographic area for which contextual data is requested",
    )


# === Weather context ===

class WeatherDataRequest(SpatialDataRequest):
    """Request sent by GE to DM for weather data."""

    start_time: Optional[datetime] = Field(
        None,
        description="Beginning of the requested time interval",
    )
    end_time: Optional[datetime] = Field(
        None,
        description="End of the requested time interval",
    )
    time_step_minutes: int = Field(
        60,
        gt=0,
        description="Time resolution between requested weather observations",
    )


class WeatherObservation(BaseModel):
    """Weather observation at a geographic location and timestamp."""

    location: Point = Field(
        ...,
        description="Geographic location of the weather observation",
    )
    temperature: float = Field(
        ...,
        description="Temperature in degrees Celsius",
    )
    uv_index: float = Field(
        ...,
        ge=0,
        description="Ultraviolet index (UVI)",
    )
    precipitation: float = Field(
        ...,
        ge=0,
        description="Precipitation measured for the observation",
    )
    wind_speed: float = Field(
        ...,
        ge=0,
        description="Wind speed in km/h",
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of the weather observation",
    )


class WeatherData(BaseModel):
    """Weather data for a geographic area, returned by DM."""

    weather_points: list[WeatherObservation] = Field(
        default_factory=list,
        description="Weather observations available in the requested area",
    )
    covered_area: Area = Field(
        ...,
        description="Area covered by the returned weather data",
    )


class WeatherContext(BaseModel):
    """Weather observations associated by GE with a route."""

    observations: list[WeatherObservation] = Field(
        default_factory=list,
        description="Weather observations relevant to the route",
    )
    alert_level: Optional[str] = Field(
        None,
        description="Weather alert associated with the route, if any",
    )


# === Urban context ===

class UrbanDataRequest(SpatialDataRequest):
    """Request sent by GE to DM for urban contextual data."""

    include_shadow_zones: bool = True
    include_water_points: bool = True
    include_police_offices: bool = True
    include_parks: bool = True
    include_benches: bool = True

    max_distance_m: int = Field(
        100,
        gt=0,
        description="Maximum relevant distance from the route or requested area",
    )


class ShadowZone(BaseModel):
    """Urban area providing shade."""

    id: str
    geometry: Polygon
    source: str


class WaterPoint(BaseModel):
    """Public water point."""

    id: str
    location: Point
    potable: Optional[bool] = None


class PoliceOffice(BaseModel):
    """Police office relevant to route context."""

    id: str
    location: Point
    open_now: Optional[bool] = None
    is_24h: Optional[bool] = None


class Park(BaseModel):
    """Urban park."""

    id: str
    geometry: Polygon
    area_m2: Optional[float] = Field(None, ge=0)


class Bench(BaseModel):
    """Public bench."""

    id: str
    location: Point
    covered: Optional[bool] = None


class UrbanData(BaseModel):
    """Urban contextual data for an area, returned by DM."""

    shadow_zones: list[ShadowZone] = Field(default_factory=list)
    water_points: list[WaterPoint] = Field(default_factory=list)
    police_offices: list[PoliceOffice] = Field(default_factory=list)
    parks: list[Park] = Field(default_factory=list)
    benches: list[Bench] = Field(default_factory=list)

    covered_area: Area = Field(
        ...,
        description="Area covered by the returned urban data",
    )


class UrbanContext(BaseModel):
    """Urban data associated by GE with a specific route."""

    shadow_zones: list[ShadowZone] = Field(default_factory=list)
    water_points: list[WaterPoint] = Field(default_factory=list)
    police_offices: list[PoliceOffice] = Field(default_factory=list)
    parks: list[Park] = Field(default_factory=list)
    benches: list[Bench] = Field(default_factory=list)


# === Context description ===

class RouteContext(BaseModel):
    """Weather and urban context associated with a route candidate."""

    route_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the associated route candidate",
    )
    weather: WeatherContext
    urban: UrbanContext


class ContextDescription(BaseModel):
    """Contextual description of a collection of route candidates."""

    items: list[RouteContext] = Field(
        default_factory=list,
        description="Contextual description for each route candidate",
    )