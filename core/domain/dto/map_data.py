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
    """Represents a connection (edge) between two points in the road graph."""
    start: GeoPoint = Field(..., description="Start coordinate of the edge")
    end: GeoPoint = Field(..., description="End coordinate of the edge")
    weight: float = Field(..., ge=0, description="Edge weight (e.g., distance or travel cost)")


class Graph(BaseModel):
    """Simplified topological graph of the road network."""
    nodes: List[GeoPoint] = Field(..., description="List of graph nodes (intersections, points)")
    edges: List[Edge] = Field(..., description="List of graph edges connecting nodes")


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
    """Container for all map and topological data required by the Routing Engine."""
    road_graph: Graph = Field(..., description="Topological graph of the road network")
    tiles: List[Tile] = Field(..., description="List of map tiles that compose the area of interest")
    metadata: MapMetadata = Field(..., description="Metadata about the map dataset")
