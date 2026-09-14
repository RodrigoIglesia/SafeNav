"""
graph_data.py
-------------
Defines the internal road graph representation used by the Routing Engine.
"""

from pydantic import BaseModel, Field

from .common import GeoPoint


class Edge(BaseModel):
    """Directed weighted edge in the road graph."""

    from_node: GeoPoint = Field(
        ...,
        description="Start node of the directed edge",
    )
    to_node: GeoPoint = Field(
        ...,
        description="End node of the directed edge",
    )
    weight_d: float = Field(
        ...,
        ge=0,
        description="Traversal distance in meters",
    )
    weight_t: float = Field(
        ...,
        ge=0,
        description="Traversal time in seconds",
    )


class GraphData(BaseModel):
    """Navigable road graph used by the Routing Engine."""

    nodes: list[GeoPoint] = Field(
        ...,
        description="Road graph nodes",
    )
    edges: list[Edge] = Field(
        ...,
        description="Directed road graph edges",
    )
    adjacency: dict[str, list[Edge]] = Field(
        default_factory=dict,
        description="Adjacency list mapping node IDs to outgoing edges",
    )

    def build_adjacency(self) -> None:
        """Build the adjacency list from the graph edges."""

        adjacency: dict[str, list[Edge]] = {}

        for edge in self.edges:
            adjacency.setdefault(edge.from_node.id, []).append(edge)

        self.adjacency = adjacency