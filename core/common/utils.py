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

        # ---- maxspeed normalization ----
        maxspeed = data.get("maxspeed", 30)

        if isinstance(maxspeed, list):
            maxspeed = maxspeed[0]

        if isinstance(maxspeed, str):
            maxspeed = ''.join(c for c in maxspeed if c.isdigit() or c == '.')

        try:
            maxspeed = float(maxspeed)
        except:
            maxspeed = 30.0  # fallback km/h

        # avoid invalid speeds
        maxspeed = max(maxspeed, 1.0)

        speed_ms = maxspeed / 3.6
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
        adjacency.setdefault(u, []).append(edge)

    # -------------------------
    # return full graph
    # -------------------------
    return GraphData(
        nodes=nodes,
        edges=edges,
        adjacency=adjacency
    )