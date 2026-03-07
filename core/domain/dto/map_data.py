"""
map_data.py
------------
Defines internal data structures related to map and topological data:
- MapData: full container for processed spatial data
- Graph / Edge: simplified topological road network
- Tile: map area representation
- MapMetadata: information about data source and zoom level
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .common import GeoPoint, Polygon


# === Graph structures ===

class Edge(BaseModel):
    """Directed weighted edge in the road graph."""
    from_node: GeoPoint = Field(..., description="Start node of the edge")
    to_node: GeoPoint = Field(..., description="End node of the edge")
    weight: float = Field(..., ge=0, description="Traversal cost (distance, time, etc.)")


class GraphData(BaseModel):
    """
    Minimal navigable graph used by the Routing Engine.
    No tiles, no zoom, no visual metadata.
    """
    nodes: List[GeoPoint] = Field(..., description="Graph nodes (road intersections, junctions)")
    edges: List[Edge] = Field(..., description="Directed edges connecting graph nodes")


#TODO: Tile, MapMetadata, MapData, MapRequest and MapDataResponse are not currently used >> To be removed
# === Tile data ===

class Tile(BaseModel):
    """Represents a map tile containing a portion of the geographic area."""
    id: str = Field(..., description="Tile identifier or index (e.g., XYZ scheme)")
    bounds: Polygon = Field(..., description="Polygon representing the tile boundaries")


# === Metadata ===

class MapMetadata(BaseModel):
    """Metadata associated with a particular map dataset."""
    source: str = Field(..., description="Origin or data source (e.g., OpenStreetMap)")
    date: datetime = Field(..., description="Date of data acquisition or processing")
    zoom_level: int = Field(..., ge=0, le=24, description="Zoom level or resolution of the map data")


# === Main map data container ===

class MapData(BaseModel):
    """Container for map visualization data."""
    tiles: List[Tile] = Field(..., description="List of map tiles that compose the area of interest")
    metadata: MapMetadata = Field(..., description="Metadata about the map dataset")


# === Map HTTP request/response ===

class MapRequest(BaseModel):
    """
    Request object for map visualization.
    Sent by the UI to the API.
    """
    area: Polygon = Field(..., description="Geographic area requested for map rendering")
    zoom_level: int = Field(..., ge=0, le=24, description="Zoom level requested by the UI")
    include_tiles: bool = Field(True, description="Whether map tiles should be included in the response")
    include_metadata: bool = Field(True, description="Whether metadata should be included in the response")


class MapDataResponse(BaseModel):
    """
    HTTP response object for map visualization requests.
    """
    map: MapData = Field(..., description="Map data for rendering on the client")