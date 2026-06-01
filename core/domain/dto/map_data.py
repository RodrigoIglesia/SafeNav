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
from typing import List, Dict
from datetime import datetime
from .common import GeoPoint, Polygon


# === Graph structures ===

class Edge(BaseModel):
    """Directed weighted edge in the road graph."""
    from_node: GeoPoint = Field(..., description="Start node of the edge")
    to_node: GeoPoint = Field(..., description="End node of the edge")
    weight_d: float = Field(..., ge=0, description="Traversal cost (distance) in meters")
    weight_t: float = Field(..., ge=0, description="Traversal cost (time) in seconds")


class GraphData(BaseModel):
    """
    Minimal navigable graph used by the Routing Engine.
    """
    nodes: List[GeoPoint] = Field(..., description="Graph nodes (road intersections, junctions)")
    edges: List[Edge] = Field(..., description="Directed edges connecting graph nodes")
    adjacency: Dict[int, List[Edge]] = Field(
        default_factory=dict,
        description="Adjacency list: node_id → outgoing edges"
    )

    def build_adjacency(self):
        """
        Builds adjacency list from edges.
        Must be called after graph creation.
        """
        self.adjacency = {}
        for edge in self.edges:
            node_id = edge.from_node.id
            self.adjacency.setdefault(node_id, []).append(edge)
