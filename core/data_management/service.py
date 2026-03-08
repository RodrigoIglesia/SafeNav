"""
SafeNav Core - Data Management Service
-------------------------------------------------------------
"""
# TODO: Data Management must implement a Graph Repository with cache.
# TODO: In each request, Routing Engine will send the selected city.
# TODO: Data management must knowif the city has been already loaded, and only load a graph if it has not been loaded before. This can be done with a simple in-memory cache of loaded cities, or with a more sophisticated graph repository that can store and retrieve graphs from disk or a database.

from interfaces.i_road_graph_access import I_RoadGraphAccess
from domain.dto.map_data import GraphData, Edge
from domain.dto.common import GeoPoint

import osmnx as ox


class DataManagement(I_RoadGraphAccess):

    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area) -> GraphData:
        """
        Returns mock graph data for routing.
        """
        print(f"DM: Retrieving graph data for area {area}") #TODO: Change to logging

        return self._fetch_road_graph_data(area)


    def _fetch_road_graph_data(self, area) -> GraphData:
        # Calculate bounding box from area
        north = max(p.lat for p in area.coordinates)
        south = min(p.lat for p in area.coordinates)
        east = max(p.lon for p in area.coordinates)
        west = min(p.lon for p in area.coordinates)

        print(f"DM: Downloading graph for bbox N{north}, S{south}, E{east}, W{west}")

        # Download graph from OSM
        G = ox.graph_from_bbox(
            north=north,
            south=south,
            east=east,
            west=west,
            network_type="walk"  # TODO: Move to config file
        )

        ##########################################################################
        ##TODO: Remove debug code
        import folium
        m = ox.plot_graph_folium(G)

        # Añadir popups personalizados
        for u, v, data in G.edges(data=True):
            if "length" in data:
                popup_text = f"""
                Length: {data.get('length', 0):.2f} m<br>
                Highway: {data.get('highway', '')}<br>
                Maxspeed: {data.get('maxspeed', '')}
                """

                folium.PolyLine(
                    locations=[
                        (G.nodes[u]["y"], G.nodes[u]["x"]),
                        (G.nodes[v]["y"], G.nodes[v]["x"])
                    ],
                    popup=popup_text,
                    color="blue",
                    weight=2
                ).add_to(m)

        m.save("graph_interactive.html")
        print("Saved graph_interactive.html") #TODO: Cange to logging
        ##########################################################################

        print(f"DM: Retrieved {len(G.nodes)} nodes and {len(G.edges)} edges")

        # Convert to GraphData format
        graph = self._convert_networkx_to_graphdata(G)

        return G

    def _convert_networkx_to_graphdata(self, G) -> GraphData:
        """
        Convert NetworkX graph (OSMnx) to SafeNav GraphData.
        """

        nodes = []
        edges = []

        # Map node_id → GeoPoint
        node_map = {}

        for node_id, data in G.nodes(data=True):
            point = GeoPoint(
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


    def _build_mock_graph(self) -> GraphData:
        """
        Creates a small mock graph with two connected nodes.
        """
        #TODO: Remove

        node_a = GeoPoint(lat=40.4168, lon=-3.7038)
        node_b = GeoPoint(lat=40.4379, lon=-3.6793)

        edge = Edge(
            from_node=node_a,
            to_node=node_b,
            weight=1.0,
        )

        graph = GraphData(
            nodes=[node_a, node_b],
            edges=[edge],
        )

        return graph
