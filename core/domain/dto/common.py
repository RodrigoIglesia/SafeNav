"""
common.py
---------
Defines shared data structures used across multiple SafeNav DTOs:
- Spatial primitives (GeoPoint, Point, Polyline, Polygon, Area)
- Route preferences and metadata models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# === Spatial primitives ===

class Point(BaseModel):
    """Represent a geographic coordinate (WGS84) alone"""
    lat: float = Field(..., description="Latitude in decimal degrees (WGS84)")
    lon: float = Field(..., description="Longitude in decimal degrees (WGS84)")


class GeoPoint(Point):
    """Represents a geographic coordinate (WGS84) in a graph."""
    id: str = Field(..., description="Identifier of a certain geographical point")

# class GeoPoint(BaseModel):
#     """Represents a geographic coordinate (WGS84) in a graph."""
#     id: str = Field(..., description="Identifier of a certain geographical point")
#     lat: float = Field(..., description="Latitude in decimal degrees (WGS84)")
#     lon: float = Field(..., description="Longitude in decimal degrees (WGS84)")


class Path(BaseModel):
    """List of ordered geographic points forming a route path."""
    coordinates: List[GeoPoint] = Field(..., description="Ordered list of geographic points representing a line")

class Polyline(BaseModel):
    """List of ordered points."""
    coordinates: List[Point] = Field(..., description="Ordered list of points representing a line")


class Polygon(BaseModel):
    """Represents a closed polygonal area."""
    coordinates: List[Point] = Field(..., description="Vertices of the polygon in order")


class Area(BaseModel):
    """Represents a circular area of interest around a central point."""
    center: Point = Field(..., description="Central point of the area")
    radius_m: float = Field(..., gt=0, description="Radius in meters")


# === User and route preferences ===

class RoutePreferences(BaseModel):
    """User-defined routing preferences."""
    minimize_sun: bool = Field(False, description="Avoid areas with direct sunlight if possible")
    avoid_hazard_zones: bool = Field(False, description="Avoid dangerous or restricted zones")
    prioritize_speed: bool = Field(True, description="Prioritize shortest ETA over comfort")
    comfort_weight: float = Field(0.5, ge=0, le=1, description="Relative weight between comfort and speed (0–1)")


# === Metadata ===

class ResponseMetadata(BaseModel):
    """Metadata attached to system responses."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the response")
    request_id: str = Field(..., description="Unique identifier for the route request")
    source: Optional[str] = Field(None, description="Origin system or component that generated the response")
