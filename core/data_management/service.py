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
from osmnx._errors import GraphSimplificationError

from pathlib import Path


class DataManagement(I_RoadGraphAccess):

    cache_dir = Path("./graph_cache")
    cache_dir.mkdir(exist_ok=True)

    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area, city="Madrid") -> GraphData:
        """
        Returns mock graph data for routing.
        """
        print(f"DM: Retrieving graph data for city {city}") #TODO: Change to logging

        return self._fetch_road_graph_data(area, city)


    def _fetch_road_graph_data(self, area, city: str) -> GraphData:
        """
        _fetch_graph_data
        """
        #TODO: buscar una forma más eficiente de cachear grafos (DB)
       
        path = self._get_graph_file_path(city)

        if path.exists():
            # Load from disk (fast)
            print(f"Loading cached graph for {city}")
            G = ox.load_graphml(str(path))
        else:
            # Download graph once
            print(f"DM: Downloading graph for city {city}")
            center_point = (area.center.lat, area.center.lon)
            G = ox.graph_from_point(
                center_point, 
                dist=area.radius_m,  # distance in meters
                network_type="walk"
            )

            ox.save_graphml(G, str(path))
        
        # # Project graph to metric coordinates (meters)
        # G = ox.project_graph(G)

        ##########################################################################
        ##TODO: Remove debug code
        ##########################################################################
        # self._generate_graph_html(G)

        print(f"DM: Retrieved {len(G.nodes)} nodes and {len(G.edges)} edges")

        # Convert to GraphData format
        graph = self._convert_networkx_to_graphdata(G)

        return graph

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

    def _get_graph_file_path(self, city: str):
        safe_city = city.replace(" ", "_").lower()
        return self.cache_dir / f"{safe_city}.graphml"

    def _generate_graph_html(self, G):
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
        print("DM: DEBUG: Saved graph_interactive.html") #TODO: Cange to logging