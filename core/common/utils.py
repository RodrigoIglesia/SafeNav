from domain.dto.common import Point, Area, GeoPoint
from domain.dto.map_data import GraphData, Edge
from typing import List
from math import radians, cos, sin, asin, sqrt

def haversine_distance_m(p1: Point, p2: Point) -> float:
        """
        Calculate the great-circle distance in meters between two points.
        The function must accept both Point and GeoPoint
        """
        lat1, lon1, lat2, lon2 = map(
        radians,
        [p1.lat, p1.lon, p2.lat, p2.lon]
        )
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        R = 6371000 # Radius of the Earth in meters
        return R * c


def build_area_from_points(points: List[Point]) -> Area:
    """
    Builds a circular area covering a set of geospatial points.

    Strategy:
    - Compute centroid of all points
    - Compute maximum distance from centroid
    - Use that as radius
    """

    if not points:
        raise ValueError("Cannot build Area from empty point list")

    # 1. Centroid
    center_lat = sum(p.lat for p in points) / len(points)
    center_lon = sum(p.lon for p in points) / len(points)
    center = Point(lat=center_lat, lon=center_lon)

    # 2. Max distance to centroid
    radius_m = max(
        haversine_distance_m(center, p)
        for p in points
    )

    # Optional safety margin (important for routing)
    radius_m *= 1.1  # +10% buffer

    return Area(
        center=center,
        radius_m=radius_m
    )


def search_nearest_point(nodes: List[GeoPoint], point: Point) -> GeoPoint:
        """Return the GeoPoint in nodes closest to the input Point."""
        nearest = min(nodes, key=lambda node: haversine_distance_m(point, node))

        return nearest

def convert_networkx_to_graphdata(G) -> GraphData:
    """
    Convert NetworkX graph (OSMnx) to SafeNav GraphData with adjacency.
    """

    nodes = []
    edges = []
    node_map = {}

    # -------------------------
    # Build nodes
    # -------------------------
    for node_id, data in G.nodes(data=True):
        point = GeoPoint(
            id=str(node_id),
            lat=data["y"],
            lon=data["x"]
        )
        nodes.append(point)
        node_map[node_id] = point

    # -------------------------
    # Build edges
    # -------------------------
    adjacency = {}

    for u, v, data in G.edges(data=True):

        # ---- distance ----
        length = float(data.get("length", 1.0))  # meters

        speed_ms = 1.4 # Human walking avg m/s
        travel_time = length / speed_ms

        # ---- edge creation ----
        edge = Edge(
            from_node=node_map[u],
            to_node=node_map[v],
            weight_d=length,
            weight_t=travel_time
        )

        edges.append(edge)

        # ---- adjacency build (IMPORTANT) ----
        adjacency.setdefault(str(u), []).append(edge)

    # -------------------------
    # return full graph
    # -------------------------
    return GraphData(
        nodes=nodes,
        edges=edges,
        adjacency=adjacency
    )