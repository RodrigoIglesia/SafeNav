"""
Benchmark script to test router algorithms and graph decoding
"""

from routing_engine.modules.router import Router
from common.utils import search_nearest_point, convert_networkx_to_graphdata

from domain.dto.common import Point

import networkx as nx
import matplotlib.pyplot as plt
import math, random

def random_point_in_radius(center_lat, center_lon, radius_m):
    """
    Generate a random point within a circle (in meters)
    """
    # Earth radius in meters
    R = 6371000

    # Random distance and angle
    d = radius_m * math.sqrt(random.random())  # uniform distribution
    theta = random.uniform(0, 2 * math.pi)

    # Offsets in radians
    delta_lat = (d * math.cos(theta)) / R
    delta_lon = (d * math.sin(theta)) / (R * math.cos(math.radians(center_lat)))

    # Convert to degrees
    new_lat = center_lat + math.degrees(delta_lat)
    new_lon = center_lon + math.degrees(delta_lon)

    return Point(new_lat, new_lon)

# Load cached graph
path = "graph_cache/madrid_40.446_-3.6909_2252m_80222b62c7ffbdf46d7b7fc9f2b997ae.graphml"
G = nx.read_graphml(path)


# graph = convert_networkx_to_graphdata(G)

# # Route estimation
# # Center and radius
# center_lat = 40.446
# center_lon = -3.6909
# radius_m = 2252

# # Generate points
# origin = random_point_in_radius(center_lat, center_lon, radius_m)
# destination = random_point_in_radius(center_lat, center_lon, radius_m)

# # Search the origin and destination points in the graph
# graph_origin = search_nearest_point(graph.nodes, origin)

# graph_destination = search_nearest_point(graph.nodes, destination)

# # Calculate route
# router = Router(graph, graph_origin, graph_destination)

# # Apply Dijkstra path planner
# path = router._dijkstra()