"""
SafeNav Core - Data Management Service
-------------------------------------------------------------
"""
# TODO: Improve cache management. Check if area is contained in a cached one.
# TODO: Think better solution for caching areas and using them >> IOU of areas?? >> Check SOA
# TODO: Search a better and more efficent way of caching graphs (DB)
# TODO: Interfaces shall be updated to adapted the access to cached graphs


from interfaces.i_road_graph_access import I_RoadGraphAccess
from domain.dto.map_data import GraphData
from domain.dto.common import Point, Area

from common.utils import haversine_distance_m, convert_networkx_to_graphdata

import osmnx as ox
from osmnx._errors import GraphSimplificationError

from pathlib import Path
import hashlib
import re


class DataManagement(I_RoadGraphAccess):

    cache_dir = Path("./graph_cache")
    cache_dir.mkdir(exist_ok=True)

    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area: Area, city="Madrid") -> GraphData:
        """
        Returns mock graph data for routing.
        """
        print(f"DM: Retrieving graph data for city {city}") #TODO: Change to logging

        eps = 1e-6 # TODO: Add to configuration

        return self._fetch_road_graph_data(area, city, eps)


    def _fetch_road_graph_data(self, area: Area, city: str, eps: float) -> GraphData:
        """
        _fetch_graph_data
        """
       
        # Check if area has been cached before > Try to reuse an existing graph
        cached = self._find_best_cached_graph(area, city, eps)

        if cached:
            print(f"DM: Loading REUSED cached graph for {city}: {cached['file'].name}")
            G = ox.load_graphml(str(cached["file"]))

        else:
            # fallback to exact match (optional but keeps your logic)
            path = self._get_graph_cache_file_path(area, city)

            if path.exists():
                print(f"DM: Loading cached graph for {city}")
                G = ox.load_graphml(str(path))

            else:
                # Download new graph
                print(f"DM: Downloading new graph for city {city}")

                center_point = (area.center.lat, area.center.lon)

                G = ox.graph_from_point(
                    center_point,
                    dist=area.radius_m,
                    network_type="walk"
                )
                print(f"DM: Caching new graph for city {city}")

                ox.save_graphml(G, str(path))
        
        # # Project graph to metric coordinates (meters)
        # G = ox.project_graph(G)

        ##########################################################################
        ##TODO: Remove debug code
        ##########################################################################
        # self._generate_graph_html(G)

        print(f"DM: Retrieved {len(G.nodes)} nodes and {len(G.edges)} edges")

        # Convert to GraphData format
        graph = convert_networkx_to_graphdata(G)

        return graph

    def _find_best_cached_graph(self, area: Area, city: str, eps: float):
        cached_graphs = self._scan_cached_graphs(city)

        fully_contained = []

        for entry in cached_graphs:
            cached_center = Point(
                lat=entry["center"]["lat"],
                lon=entry["center"]["lon"]
            )

            dist = haversine_distance_m(area.center, cached_center)

            cached_radius = entry["radius"]
            requested_radius = area.radius_m

            # Case 1: FULL containment
            if dist + requested_radius <= cached_radius + eps:
                print(f"DM: graph contained in chached")
                fully_contained.append(entry)

            # Case 2: PARTIAL overlap (optional explicit detection)
            elif dist < (cached_radius + requested_radius):
                # Overlapping → DO NOT reuse
                print(f"DM: graph overlapping chached")
                continue

            # Case 3: No overlap → ignore
            else:
                print(f"DM: graph not overlapping chached")
                continue

        if not fully_contained:
            return None

        return min(fully_contained, key=lambda x: x["radius"])

    def _scan_cached_graphs(self, city: str):
        safe_city = city.replace(" ", "_").lower()
        cached = []

        pattern = re.compile(
            rf"{safe_city}_(?P<lat>-?\d+\.\d+)_(?P<lon>-?\d+\.\d+)_(?P<radius>\d+)m_.*\.graphml"
        )

        for file in self.cache_dir.glob(f"{safe_city}_*.graphml"):
            match = pattern.match(file.name)
            if not match:
                continue

            cached.append({
                "file": file,
                "center": {
                    "lat": float(match.group("lat")),
                    "lon": float(match.group("lon"))
                },
                "radius": float(match.group("radius"))
            })

        return cached

    def _area_to_hash(self, area: Area) -> str:
        # Convert area to a stable, sorted representation for saving cache files
        lat = round(area.center.lat, 6)
        lon = round(area.center.lon, 6)
        radius = round(area.radius_m, 1)  # 0.1m precision is more than enough

        area_str = f"{lat}_{lon}_{radius}"

        return hashlib.md5(area_str.encode()).hexdigest()
    
    def _get_graph_cache_file_path(self, area: Area, city: str):
        safe_city = city.replace(" ", "_").lower()
        area_hash = self._area_to_hash(area)
        lat = round(area.center.lat, 4)
        lon = round(area.center.lon, 4)
        radius = int(area.radius_m)

        return self.cache_dir / f"{safe_city}_{lat}_{lon}_{radius}m_{area_hash}.graphml"

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