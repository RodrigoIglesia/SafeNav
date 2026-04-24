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


def build_area_from_points(origin: Point, destination: Point) -> Area:
        # Compute the center as the midpoint
        center_lat = (origin.lat + destination.lat) / 2
        center_lon = (origin.lon + destination.lon) / 2
        center = Point(lat=center_lat, lon=center_lon)

        # Compute radius as half the distance between points
        radius_m = haversine_distance_m(origin, destination) / 2

        return Area(center=center, radius_m=radius_m)


def search_nearest_point(nodes: List[GeoPoint], point: Point) -> GeoPoint:
        """Return the GeoPoint in nodes closest to the input Point."""
        nearest = min(nodes, key=lambda node: haversine_distance_m(point, node))

        return nearest

def convert_networkx_to_graphdata(G) -> GraphData:
        """
        Convert NetworkX graph (OSMnx) to SafeNav GraphData.
        """

        nodes = []
        edges = []

        # Map node_id → GeoPoint
        node_map = {}

        for node_id, data in G.nodes(data=True):
            point = GeoPoint(
                id=str(node_id),
                lat=data["y"],
                lon=data["x"]
            )
            nodes.append(point)
            node_map[node_id] = point

        for u, v, data in G.edges(data=True):
            edge = Edge(
                from_node=node_map[u],
                to_node=node_map[v],
                weight=data.get("length", 1.0)  # meters
            )
            edges.append(edge)

        return GraphData(
            nodes=nodes,
            edges=edges
        )