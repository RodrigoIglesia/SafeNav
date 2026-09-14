"""
SafeNav Core - Data Management Service
-------------------------------------------------------------

Data-access boundary between SafeNav Core and external or
persisted data sources.

Responsibilities:
- Retrieve routing graph data.
- Retrieve weather data.
- Retrieve urban/open data.
- Normalize external data into SafeNav DTOs.
- Manage caching of external data.

Data Management does not perform route contextualization
or route safety/comfort evaluation.
"""

# Graph management
# TODO: Improve graph cache management.
# TODO: Support multi-city graph selection and caching.
# TODO: Evaluate a more efficient graph persistence/cache strategy.
# TODO: Update IRoadGraphAccess for the final multi-city design.
# TODO: Replace print statements with structured logging.

# Contextual data
# TODO: Implement weather provider integration.
# TODO: Implement weather provider response -> WeatherData conversion.
# TODO: Implement urban/open-data provider integration.
# TODO: Implement urban provider response -> UrbanData conversion.
# TODO: Define caching/TTL policies for contextual data.
# TODO: Evaluate spatial sampling for weather requests over large route areas.

# Architecture
# TODO: Evaluate splitting external provider access into dedicated adapters
#       if DataManagement grows significantly.



from interfaces.i_road_graph_access import IRoadGraphAccess
from interfaces.i_context_data_access import IContextDataAccess
from domain.dto.common import Point, Area, Polygon
from domain.dto.geospatial import (
    WeatherObservation,
    WeatherDataRequest,
    WeatherData,
    UrbanDataRequest,
    UrbanData,
    WaterPoint,
    PoliceOffice,
    Bench,
    Park,
)
from domain.dto.map_data import GraphData

from common.utils import haversine_distance_m, convert_networkx_to_graphdata

import osmnx as ox
from osmnx._errors import GraphSimplificationError
import httpx
from datetime import datetime

from pathlib import Path
import hashlib
import re


class DataManagement(IRoadGraphAccess, IContextDataAccess):

    cache_dir = Path("./graph_cache")
    cache_dir.mkdir(exist_ok=True)

    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area: Area, city="Madrid") -> GraphData:
        """
        Gets graph data from ext data source and transform it to SafeNav data model
        """
        print(f"DM: Retrieving graph data for city {city}") #TODO: Change to logging

        eps = 1e-6 # TODO: Add to configuration

        return self._fetch_road_graph_data(area, city, eps)
    
    def get_weather_data(self, weather_request: WeatherDataRequest) -> WeatherData:
        """
        Gets weather data from ext data source and transform it to SafeNav data model
        """
        # TODO: Current implementation retrieves weather using the center of the
        # requested area. Evaluate spatial sampling for long/large route areas.
        raw_data = self._fetch_weather_data(weather_request)

        return self._convert_weather_data(
            raw_data,
            weather_request
        )

    def _fetch_weather_data(self, request: WeatherDataRequest) -> dict:
        OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
        center = request.covered_area.center

        params = {
            "latitude": center.lat,
            "longitude": center.lon,
            "hourly": [
                "temperature_2m",
                "uv_index",
                "precipitation",
                "wind_speed_10m",
            ],
            "wind_speed_unit": "ms",
            "timezone": "auto",
        }

        response = httpx.get(
            OPEN_METEO_URL,
            params=params,
            timeout=10.0,
        )

        response.raise_for_status()

        return response.json()


    def _convert_weather_data(self, raw_data, request: WeatherDataRequest) -> WeatherData:
        """
        Converts an Open-Meteo response into the SafeNav WeatherData model.
        """

        hourly = raw_data.get("hourly")

        if not hourly:
            raise ValueError("Open-Meteo response does not contain hourly weather data.")

        required_fields = (
            "time",
            "temperature_2m",
            "uv_index",
            "precipitation",
            "wind_speed_10m",
        )

        for field in required_fields:
            if field not in hourly:
                raise ValueError(
                    f"Open-Meteo response is missing required field: {field}"
                )

        location = Point(
            lat=raw_data.get("latitude", request.covered_area.center.lat),
            lon=raw_data.get("longitude", request.covered_area.center.lon),
        )

        observations = []

        for (
            timestamp,
            temperature,
            uv_index,
            precipitation,
            wind_speed,
        ) in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["uv_index"],
            hourly["precipitation"],
            hourly["wind_speed_10m"],
        ):
            observations.append(
                WeatherObservation(
                    location=location,
                    timestamp=datetime.fromisoformat(timestamp),
                    temperature=temperature,
                    uv_index=uv_index,
                    precipitation=precipitation,
                    wind_speed=wind_speed,
                )
            )

        return WeatherData(
            weather_points=observations,
            covered_area=request.covered_area,
        )

    def get_urban_data(self, urban_request: UrbanDataRequest) -> UrbanData:
        """
        Gets urban data from ext data source and transform it to SafeNav data model
        """
        raw_data = self._fetch_urban_data(urban_request)

        return self._convert_urban_data(
            raw_data,
            urban_request
        )

    def _fetch_urban_data(self, request: UrbanDataRequest):
        OVERPASS_URL = "https://overpass-api.de/api/interpreter"

        query = self._build_overpass_query(request)

        response = httpx.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=30.0,
        )

        response.raise_for_status()

        return response.json()

    def _build_overpass_query(
        self,
        request: UrbanDataRequest,
    ) -> str:

        center = request.covered_area.center
        radius = request.covered_area.radius_m

        filters = []

        if request.include_water_points:
            filters.append(
                f'node["amenity"="drinking_water"]'
                f'(around:{radius},{center.lat},{center.lon});'
            )

        if request.include_benches:
            filters.append(
                f'node["amenity"="bench"]'
                f'(around:{radius},{center.lat},{center.lon});'
            )

        if request.include_parks:
            filters.append(
                f'nwr["leisure"="park"]'
                f'(around:{radius},{center.lat},{center.lon});'
            )

        if request.include_police_offices:
            filters.append(
                f'nwr["amenity"="police"]'
                f'(around:{radius},{center.lat},{center.lon});'
            )

        filters_query = "\n".join(filters)

        return f"""
        [out:json][timeout:25];
        (
            {filters_query}
        );
        out center geom;
        """

    def _convert_urban_data(self, raw_data, request: UrbanDataRequest) -> UrbanData:
        """
        Converts an Overpass API response into the SafeNav UrbanData model.
        """

        water_points = []
        police_offices = []
        benches = []
        parks = []

        for element in raw_data.get("elements", []):
            tags = element.get("tags", {})

            # ------------------------------------------------------
            # Drinking water
            # ------------------------------------------------------
            if tags.get("amenity") == "drinking_water":
                location = self._extract_osm_location(element)

                if location is not None:
                    water_points.append(
                        WaterPoint(location=location)
                    )

            # ------------------------------------------------------
            # Bench
            # ------------------------------------------------------
            elif tags.get("amenity") == "bench":
                location = self._extract_osm_location(element)

                if location is not None:
                    benches.append(
                        Bench(location=location)
                    )

            # ------------------------------------------------------
            # Police office
            # ------------------------------------------------------
            elif tags.get("amenity") == "police":
                location = self._extract_osm_location(element)

                if location is not None:
                    police_offices.append(
                        PoliceOffice(location=location)
                    )

            # ------------------------------------------------------
            # Park
            # ------------------------------------------------------
            elif tags.get("leisure") == "park":
                geometry = self._extract_osm_polygon(element)

                if geometry is not None:
                    parks.append(
                        Park(geometry=geometry)
                    )

        return UrbanData(
            water_points=water_points,
            police_offices=police_offices,
            benches=benches,
            parks=parks,
            shadow_zones=[],  # TODO: Implement shadow data source/computation.
            covered_area=request.covered_area,
        )


    def _extract_osm_location(self, element: dict) -> Point | None:
        """
        Extracts a representative location from an OSM element.

        Nodes provide lat/lon directly.
        Ways and relations may provide a center.
        """

        # OSM node
        if "lat" in element and "lon" in element:
            return Point(
                lat=element["lat"],
                lon=element["lon"],
            )

        # OSM way/relation returned with `out center`
        center = element.get("center")

        if center is not None:
            return Point(
                lat=center["lat"],
                lon=center["lon"],
            )

        return None

    def _extract_osm_polygon(self, element: dict) -> Polygon | None:
        """
        Extracts polygon geometry from an OSM way/relation.
        """

        geometry = element.get("geometry")

        if not geometry:
            return None

        points = [
            Point(
                lat=coordinate["lat"],
                lon=coordinate["lon"],
            )
            for coordinate in geometry
        ]

        if len(points) < 3:
            return None

        return Polygon(
            points=points
        )

    def _fetch_road_graph_data(self, area: Area, city: str, eps: float) -> GraphData:
        """
        _fetch_graph_data
        """
        print("DM: Loading maps...")
        # TODO: add signal to send to UI and change loading screen
       
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