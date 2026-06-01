# core/routing_engine/modules/router.py
"""
Router Class
------------------------------------
Implements the path planning algorithms of the router
This version only implements dijkstra algorithm for distance optimization
"""

# TODO: Review and document algorithms -- investigate further optimization parameters and how to compute them
from domain.dto.common import GeoPoint
from domain.dto.map_data import GraphData

from common.utils import haversine_distance_m

from typing import List
import heapq

class Router:
    def __init__(self, graph: GraphData, start: GeoPoint, goal: GeoPoint):
        self.graph = graph
        self.start = start
        self.goal = goal
        
    def _dijkstra(self, optimize="distance") -> List[GeoPoint]:
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
                # Check optimization method (distance or travel time)
                if optimize == "distance":
                    weight = edge.weight_d
                elif optimize == "eta":
                    weight = edge.weight_t
                else:
                    print("RE: No valid optimization parameter")
                
                if edge.from_node.id == current_id:
                    neighbor_id = edge.to_node.id
                    alt_distance = current_dist + weight

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

        distance, eta = self._estimate_dist_eta(self.graph, path_ids)

        return path, distance, eta

        
    
    def _astar(self, optimize="distance") -> List[GeoPoint]:
        """
        Routing Model: A*
        Faster than Dijkstra using spatial heuristic
        using harvesine distance as heuristic (weight = distance)
        """
        node_map = {node.id: node for node in self.graph.nodes}

        # g(n): cost from start to node
        g_score = {node.id: float("inf") for node in self.graph.nodes}
        g_score[self.start.id] = 0

        # f(n) = g(n) + h(n)
        f_score = {node.id: float("inf") for node in self.graph.nodes}
        f_score[self.start.id] = haversine_distance_m(self.start, self.goal)

        previous = {node.id: None for node in self.graph.nodes}

        pq = [(f_score[self.start.id], self.start.id)]

        while pq:
            _, current_id = heapq.heappop(pq)
            current_node = node_map[current_id]

            if current_id == self.goal.id:
                break

            for edge in self.graph.edges:
                # Check optimization method (distance or travel time)
                if optimize == "distance":
                    weight = edge.weight_d
                elif optimize == "eta":
                    weight = edge.weight_t
                else:
                    print("RE: No valid optimization parameter")
                
                if edge.from_node.id == current_id:
                    neighbor_id = edge.to_node.id
                    neighbor_node = node_map[neighbor_id]

                    tentative_g = g_score[current_id] + edge.weight_t

                    if tentative_g < g_score[neighbor_id]:
                        previous[neighbor_id] = current_id
                        g_score[neighbor_id] = tentative_g

                        f_score[neighbor_id] = tentative_g + haversine_distance_m(neighbor_node, self.goal)

                        heapq.heappush(pq, (f_score[neighbor_id], neighbor_id))

        # Reconstruct path
        path_ids = []
        node_id = self.goal.id

        if previous[node_id] is None and node_id != self.start.id:
            return []  # no path found

        while node_id is not None:
            path_ids.insert(0, node_id)
            node_id = previous[node_id]

        path = [node_map[nid] for nid in path_ids]
        distance, eta = self._estimate_dist_eta(self.graph, path_ids)

        return path, distance, eta
    

    def _estimate_dist_eta(self, graph, path_ids):
        """
        Auxiliary function to compute the estimated time arrival of a calculated route
        """
        # -------------------------
        # Compute total distance & ETA
        # -------------------------

        total_distance = 0
        total_eta = 0

        for i in range(len(path_ids) - 1):

            from_id = path_ids[i]
            to_id = path_ids[i + 1]

            # Find corresponding edge
            for edge in graph.edges:
                if (edge.from_node.id == from_id and edge.to_node.id == to_id):
                    total_distance += edge.weight_d
                    total_eta += edge.weight_t
                    break

        return total_distance, total_eta