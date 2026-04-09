
# core/routing_engine/modules/router.py
"""
Router Class
------------------------------------
Implements the path planning algorithms of the router
This version only implements dijkstra algorithm for distance optimization
"""

# TODO: Improve Dijkstra algorithmm, takes too long with large graphs
# TODO: Add more algorithms
from domain.dto.common import GeoPoint
from domain.dto.map_data import GraphData

from typing import List
import heapq

class Router:
    def __init__(self, graph: GraphData, start: GeoPoint, goal: GeoPoint):
        self.graph = graph
        self.start = start
        self.goal = goal
        
    def _dijkstra(self) -> List[GeoPoint]:
        """
        Routing Model: Dijkstra
        Applies Dijkstra algorithm to a graph, using the start and end GeoPoint in the graph.
        """
        # Map node.id → GeoPoint for easy lookup
        node_map = {node.id: node for node in self.graph.nodes}

        # Initialize distances and previous nodes using IDs
        distances = {node.id: float("inf") for node in self.graph.nodes}
        previous = {node.id: None for node in self.graph.nodes}

        distances[self.start.id] = 0
        pq = [(0, self.start.id)]  # priority queue of (distance, node_id)

        while pq:
            current_dist, current_id = heapq.heappop(pq)
            current_node = node_map[current_id]

            if current_id == self.goal.id:
                break

            # Iterate only over edges starting from current node
            for edge in self.graph.edges:
                if edge.from_node.id == current_id:
                    neighbor_id = edge.to_node.id
                    alt_distance = current_dist + edge.weight

                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current_id
                        heapq.heappush(pq, (alt_distance, neighbor_id))

        # Reconstruct path as list of GeoPoint
        path_ids = []
        node_id = self.goal.id
        while node_id is not None:
            path_ids.insert(0, node_id)
            node_id = previous[node_id]

        path = [node_map[node_id] for node_id in path_ids]
        return path