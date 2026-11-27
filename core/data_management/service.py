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
# Strategy:
#   1. One walking graph per city is downloaded ONCE (city boundary + buffer)
#      and stored as a pickle in ./graph_cache.
#   2. Loaded city graphs are kept in memory for the lifetime of the process.
#   3. Each request crops the requested circular area out of the in-memory
#      city graph (vectorized, milliseconds).
#   4. If the requested area is not covered by the city graph, a per-area
#      graph is downloaded and cached as a fallback.
# TODO: Support multi-city graph selection (e.g. city detection from Area).
# TODO: Evaluate building city graphs offline from Geofabrik .osm.pbf extracts.
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

from common.utils import convert_networkx_to_graphdata

import osmnx as ox
import networkx as nx
import numpy as np
from shapely.geometry import Polygon as ShapelyPolygon, LineString as ShapelyLineString
from shapely.ops import polygonize
import httpx
from datetime import datetime, timezone, timedelta
import time

from pathlib import Path
import math
import os
import pickle
import threading
import hashlib
import json
import random


class _OverpassRetryableError(Exception):
    """Transient Overpass failure that should be retried on another endpoint."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class DataManagement(IRoadGraphAccess, IContextDataAccess):

    cache_dir = Path("./graph_cache")
    cache_dir.mkdir(exist_ok=True)

    # ----------------------------------------------------------
    # Graph configuration
    # TODO: Move to configuration
    # ----------------------------------------------------------
    GRAPH_CACHE_VERSION = 1
    NETWORK_TYPE = "walk"

    # Geocoding queries used to download a whole city graph.
    # Cities not listed here are geocoded using the city name directly.
    CITY_PLACE_QUERIES = {
        "madrid": "Madrid, Spain",
    }

    # Extra distance around the city boundary included in the city graph,
    # so routes near the municipal border are not cut.
    CITY_BOUNDARY_BUFFER_M = 1000

    # Extra distance around the requested area kept when cropping,
    # so edges near the border of the area are not cut.
    CROP_MARGIN_M = 100

    # Keep only the largest weakly connected component of the cropped graph.
    KEEP_LARGEST_COMPONENT = True

    # In-memory city graph cache shared by all instances in the process.
    # city_key -> {"graph", "boundary", "node_ids", "lat_rad", "lon_rad"}
    _city_graphs: dict = {}
    _city_graphs_lock = threading.Lock()
    _city_locks: dict = {}

    # ----------------------------------------------------------
    # Urban data (Overpass) configuration
    # TODO: Move to configuration
    # ----------------------------------------------------------
    # Public Overpass instances with global coverage, tried in rotation.
    # See https://wiki.openstreetmap.org/wiki/Overpass_API#Public_Overpass_API_instances
    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]
    OVERPASS_SERVER_TIMEOUT_S = 25          # [timeout:...] sent in the query
    OVERPASS_HTTP_TIMEOUT = httpx.Timeout(45.0, connect=10.0)
    OVERPASS_MAX_ATTEMPTS = 6               # total, across all endpoints
    OVERPASS_MAX_BACKOFF_S = 8.0
    OVERPASS_ENDPOINT_COOLDOWN_S = 60.0     # skip an endpoint after it failed
    OVERPASS_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

    urban_cache_dir = Path("./urban_cache")
    urban_cache_dir.mkdir(exist_ok=True)
    URBAN_CACHE_TTL_S = 24 * 3600           # urban features change slowly

    # endpoint -> monotonic time until which it should be avoided
    _overpass_cooldown_until: dict = {}
    _overpass_lock = threading.Lock()

    # ==========================================================
    # I_RoadGraphAccess implementation
    # ==========================================================
    def get_graph_data(self, area: Area, city="Madrid") -> GraphData:
        """
        Gets graph data from ext data source and transform it to SafeNav data model
        """
        print(f"DM: Retrieving graph data for city {city}") #TODO: Change to logging

        return self._fetch_road_graph_data(area, city)

    def preload_graph(self, city="Madrid", background=True):
        """
        Loads (and downloads if needed) the city graph ahead of the first request.

        Call this at application startup so the first user does not wait.
        With background=True the load runs in a daemon thread and this
        method returns immediately.
        """
        if background:
            thread = threading.Thread(
                target=self._load_city_graph,
                args=(city,),
                name=f"graph-preload-{city}",
                daemon=True,
            )
            thread.start()
            return thread

        self._load_city_graph(city)
        return None

    def get_weather_data(self, weather_request: WeatherDataRequest) -> WeatherData:
        """
        Gets weather data from ext data source and transform it to SafeNav data model
        """
        # TODO: Current implementation retrieves weather using the center of the
        # requested area. Evaluate spatial sampling for long/large route areas.
        raw_data = self._fetch_weather_data(weather_request)

        print("DM: Raw weather data: ", raw_data)

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

        # Open-Meteo returns local times without offset when timezone="auto";
        # the offset is provided separately in utc_offset_seconds.
        # SafeNav DTOs always carry timezone-aware timestamps.
        provider_tz = timezone(timedelta(seconds=raw_data.get("utc_offset_seconds", 0)))

        location = Point(
            lat=raw_data.get("latitude", request.covered_area.center.lat),
            lon=raw_data.get("longitude", request.covered_area.center.lon),
        )

        observations = []

        for (timestamp, temperature, uv_index, precipitation, wind_speed) in zip(hourly["time"], hourly["temperature_2m"], hourly["uv_index"], hourly["precipitation"], hourly["wind_speed_10m"]):
            ts = datetime.fromisoformat(timestamp)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=provider_tz)

            observations.append(
                WeatherObservation(
                    location=location,
                    timestamp=ts,
                    temperature=temperature,
                    uv_index=uv_index,
                    precipitation=precipitation,
                    wind_speed=wind_speed,
                )
            )

        print(f"DM: Processed {len(observations)} weather observations")

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

    def _fetch_urban_data(self, request: UrbanDataRequest) -> dict:
        """
        Fetches urban features from Overpass.

        - Fresh cached responses are returned without any network call.
        - Requests rotate across several Overpass instances, skipping
          instances that failed recently.
        - Retries 429/5xx, timeouts, connection errors and Overpass
          runtime errors (HTTP 200 with a "remark"), with backoff + jitter.
        - If every attempt fails, a stale cached response is returned
          when available.
        """
        query = self._build_overpass_query(request)
        print("DM: Overpass query: ", query)

        cache_path = self._get_urban_cache_path(query)
        cached, cache_age = self._read_urban_cache(cache_path)

        if cached is not None and cache_age <= self.URBAN_CACHE_TTL_S:
            print(f"DM: Using cached urban data ({cache_age / 60:.0f} min old)")
            return cached

        headers = {
            "User-Agent": "SafeNav/0.1",
            "Accept": "application/json",
        }

        last_error = None

        with httpx.Client(timeout=self.OVERPASS_HTTP_TIMEOUT, headers=headers) as client:
            for attempt in range(1, self.OVERPASS_MAX_ATTEMPTS + 1):
                url = self._pick_overpass_endpoint(attempt)

                try:
                    t0 = time.perf_counter()
                    response = client.post(url, data={"data": query})

                    if response.status_code in self.OVERPASS_RETRYABLE_STATUS:
                        retry_after = self._parse_retry_after(response)
                        raise _OverpassRetryableError(
                            f"HTTP {response.status_code}", retry_after
                        )

                    response.raise_for_status()

                    data = response.json()

                    # Overpass reports server-side timeouts/out-of-memory as
                    # HTTP 200 with a "remark" and a truncated result.
                    remark = data.get("remark", "")
                    if "runtime error" in remark.lower():
                        raise _OverpassRetryableError(f"runtime error: {remark}")

                    print(
                        f"DM: Overpass OK from {url} in {time.perf_counter() - t0:.1f}s "
                        f"({len(data.get('elements', []))} elements)"
                    )

                    self._write_urban_cache(cache_path, data)
                    return data

                except (_OverpassRetryableError, httpx.TransportError, ValueError) as exc:
                    # TransportError covers timeouts and connection errors.
                    # ValueError covers an HTML error page instead of JSON.
                    last_error = exc
                    retry_after = getattr(exc, "retry_after", None)
                    self._mark_overpass_endpoint_failed(url, retry_after)

                    if attempt >= self.OVERPASS_MAX_ATTEMPTS:
                        break

                    wait_seconds = min(
                        self.OVERPASS_MAX_BACKOFF_S,
                        0.5 * 2 ** (attempt - 1),
                    ) + random.uniform(0, 0.5)

                    print(
                        f"DM: Overpass {url} failed ({type(exc).__name__}: {exc}). "
                        f"Retrying with next endpoint in {wait_seconds:.1f}s "
                        f"({attempt}/{self.OVERPASS_MAX_ATTEMPTS})"
                    )

                    time.sleep(wait_seconds)

        if cached is not None:
            print(
                f"DM: All Overpass attempts failed, using STALE cached urban data "
                f"({cache_age / 3600:.1f} h old)"
            )
            return cached

        raise RuntimeError(
            f"Overpass request failed after {self.OVERPASS_MAX_ATTEMPTS} attempts "
            f"across {len(self.OVERPASS_URLS)} endpoints: {last_error}"
        ) from last_error

    def _pick_overpass_endpoint(self, attempt: int) -> str:
        """
        Rotates through endpoints, preferring those not in cooldown.
        """
        now = time.monotonic()
        n = len(self.OVERPASS_URLS)

        with self._overpass_lock:
            for offset in range(n):
                url = self.OVERPASS_URLS[(attempt - 1 + offset) % n]
                if self._overpass_cooldown_until.get(url, 0.0) <= now:
                    return url

            # All endpoints in cooldown: use the one that recovers first
            return min(
                self.OVERPASS_URLS,
                key=lambda u: self._overpass_cooldown_until.get(u, 0.0),
            )

    def _mark_overpass_endpoint_failed(self, url: str, retry_after: float | None = None):
        cooldown = max(self.OVERPASS_ENDPOINT_COOLDOWN_S, retry_after or 0.0)

        with self._overpass_lock:
            self._overpass_cooldown_until[url] = time.monotonic() + cooldown

    def _parse_retry_after(self, response) -> float | None:
        value = response.headers.get("Retry-After")

        try:
            return float(value) if value is not None else None
        except ValueError:
            return None

    def _get_urban_cache_path(self, query: str) -> Path:
        key = hashlib.md5(" ".join(query.split()).encode()).hexdigest()
        return self.urban_cache_dir / f"overpass_{key}.json"

    def _read_urban_cache(self, path: Path):
        """
        Returns (data, age_seconds), or (None, None) if there is no usable cache.
        """
        if not path.exists():
            return None, None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"DM: Ignoring unreadable urban cache {path.name}: {exc}")
            return None, None

        return data, time.time() - path.stat().st_mtime

    def _write_urban_cache(self, path: Path, data: dict):
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        os.replace(tmp_path, path)

    def _build_overpass_query(self, request: UrbanDataRequest) -> str:
        """
        Builds the Overpass query.

        - Uses a bounding box instead of `around`: much cheaper for the server,
          especially for ways/relations (parks). The bbox covers the circle.
        - Coordinates are rounded so near-identical requests share the cache.
        - Each feature type gets only the output it needs: nodes need no
          geometry, police needs a center, only parks need full geometry.
        """
        south, west, north, east = self._area_to_overpass_bbox(request.covered_area)
        bbox = f"({south:.5f},{west:.5f},{north:.5f},{east:.5f})"

        statements = []

        if request.include_water_points:
            statements.append(f'node["amenity"="drinking_water"]{bbox};\nout;')

        if request.include_benches:
            statements.append(f'node["amenity"="bench"]{bbox};\nout;')

        if request.include_parks:
            statements.append(f'(way["leisure"="park"]{bbox};relation["leisure"="park"]{bbox};);\nout geom;')

        if request.include_police_offices:
            statements.append(f'nwr["amenity"="police"]{bbox};\nout center;')

        body = "\n".join(statements)

        return (
            f"[out:json][timeout:{self.OVERPASS_SERVER_TIMEOUT_S}];\n"
            f"{body}\n"
        )

    def _area_to_overpass_bbox(self, area: Area):
        """
        Returns (south, west, north, east) of the square enclosing the circular area.
        """
        lat = area.center.lat
        lon = area.center.lon

        dlat = area.radius_m / 111_320.0
        dlon = area.radius_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))

        return lat - dlat, lon - dlon, lat + dlat, lon + dlon


    def _convert_urban_data(self, raw_data, request: UrbanDataRequest) -> UrbanData:
        """
        Convert an Overpass API response into the SafeNav UrbanData model.

        Provider-specific OSM data is normalized here so that the
        Geospatial Engine only receives SafeNav domain DTOs.
        """

        water_points = []
        police_offices = []
        benches = []
        parks = []

        for element in raw_data.get("elements", []):
            tags = element.get("tags", {})

            element_id = str(element["id"])

            # ------------------------------------------------------
            # Drinking water
            # ------------------------------------------------------
            if tags.get("amenity") == "drinking_water":
                location = self._extract_osm_location(element)

                if location is not None:
                    # amenity=drinking_water already identifies the feature
                    # as intended for drinking.
                    potable = self._parse_osm_bool(
                        tags.get("drinking_water")
                    )

                    if potable is None:
                        potable = True

                    water_points.append(
                        WaterPoint(
                            id=element_id,
                            location=location,
                            potable=potable,
                        )
                    )

            # ------------------------------------------------------
            # Bench
            # ------------------------------------------------------
            elif tags.get("amenity") == "bench":
                location = self._extract_osm_location(element)

                if location is not None:
                    benches.append(
                        Bench(
                            id=element_id,
                            location=location,
                            covered=self._parse_osm_bool(
                                tags.get("covered")
                            ),
                        )
                    )

            # ------------------------------------------------------
            # Police office
            # ------------------------------------------------------
            elif tags.get("amenity") == "police":
                location = self._extract_osm_location(element)

                if location is not None:
                    police_offices.append(
                        PoliceOffice(
                            id=element_id,
                            location=location,

                            # TODO:
                            # Derive from opening_hours when implemented.
                            open_now=None,

                            # TODO:
                            # Parse opening_hours=24/7.
                            is_24h=self._is_24h(tags),
                        )
                    )

            # ------------------------------------------------------
            # Park
            # ------------------------------------------------------
            elif tags.get("leisure") == "park":
                geometry = self._extract_osm_polygon(element)

                if geometry is not None:
                    parks.append(
                        Park(
                            id=element_id,
                            geometry=geometry,

                            # TODO:
                            # Calculate polygon area from geometry.
                            area_m2=None,
                        )
                    )

        print(
            f"DM: Urban data: {len(water_points)} water points, {len(benches)} benches, "
            f"{len(parks)} parks, {len(police_offices)} police offices"
        )

        return UrbanData(
            water_points=water_points,
            police_offices=police_offices,
            benches=benches,
            parks=parks,

            # TODO:
            # Implement dedicated shadow data source/computation.
            shadow_zones=[],

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
        Extract polygon geometry from an OSM way/relation element.

        - Ways (`out geom`) carry their ring in element["geometry"].
        - Multipolygon relations carry geometry per member; the outer member
          ways are stitched into rings with shapely. The SafeNav Polygon has a
          single ring, so the largest outer ring is used.

        Returns None when the element does not contain enough geometry
        to construct a polygon.
        """

        ring = None

        geometry = element.get("geometry")

        if geometry:
            ring = [(c["lon"], c["lat"]) for c in geometry if "lat" in c and "lon" in c]

        elif element.get("type") == "relation":
            lines = []

            for member in element.get("members", []):
                if member.get("type") != "way" or member.get("role") not in ("outer", ""):
                    continue

                member_coords = [
                    (c["lon"], c["lat"])
                    for c in member.get("geometry") or []
                    if c and "lat" in c and "lon" in c
                ]

                if len(member_coords) >= 2:
                    lines.append(ShapelyLineString(member_coords))

            if lines:
                rings = list(polygonize(lines))

                if rings:
                    largest = max(rings, key=lambda poly: poly.area)
                    ring = list(largest.exterior.coords)

        if not ring or len(ring) < 3:
            return None

        return Polygon(
            coordinates=[Point(lat=lat, lon=lon) for lon, lat in ring]
        )

    def _parse_osm_bool(self, value: str | None) -> bool | None:
        """
        Convert common OSM boolean tag values into SafeNav booleans.

        Returns None when the value is missing or cannot be interpreted.
        """

        if value is None:
            return None

        normalized = value.strip().lower()

        if normalized in {"yes", "true", "1"}:
            return True

        if normalized in {"no", "false", "0"}:
            return False

        return None

    def _is_24h(self, tags: dict) -> bool | None:
        opening_hours = tags.get("opening_hours")

        if opening_hours is None:
            return None

        return opening_hours.strip().lower() == "24/7"

    # ==========================================================
    # Road graph: retrieval, caching and cropping
    # ==========================================================
    def _fetch_road_graph_data(self, area: Area, city: str) -> GraphData:
        """
        Returns the walking graph covering `area`.

        The area is cropped from the in-memory city graph. If the city graph
        does not cover the area, a per-area graph is downloaded instead.
        """
        print("DM: Loading maps...")
        # TODO: add signal to send to UI and change loading screen

        t_start = time.perf_counter()

        G = None
        city_entry = None

        try:
            city_entry = self._load_city_graph(city)
        except Exception as exc:
            print(f"DM: Could not load city graph for {city}: {exc}")

        if city_entry is not None and self._city_covers_area(city_entry, area):
            G = self._crop_graph(city_entry, area)

            if len(G.nodes) == 0:
                print("DM: Cropped graph is empty, using area fallback")
                G = None
        elif city_entry is not None:
            print(f"DM: Requested area is outside the {city} graph, using area fallback")

        if G is None:
            G = self._load_area_graph(area, city)

        t_graph = time.perf_counter()

        ##########################################################################
        ##TODO: Remove debug code
        ##########################################################################
        # self._generate_graph_html(G)

        print(f"DM: Retrieved {len(G.nodes)} nodes and {len(G.edges)} edges")

        # Convert to GraphData format
        graph = convert_networkx_to_graphdata(G)

        t_end = time.perf_counter()
        print(
            f"DM: Graph ready in {t_end - t_start:.2f}s "
            f"(graph: {t_graph - t_start:.2f}s, conversion: {t_end - t_graph:.2f}s)"
        )

        return graph

    # ----------------------------------------------------------
    # City graph (download once, keep in memory)
    # ----------------------------------------------------------
    def _load_city_graph(self, city: str) -> dict:
        """
        Returns the city graph entry, loading it in this order:
        memory -> pickle on disk -> download (once per city).

        Thread-safe: concurrent callers for the same city wait for a single load.
        """
        city_key = self._safe_city(city)

        with self._city_graphs_lock:
            entry = self._city_graphs.get(city_key)
            if entry is not None:
                return entry
            city_lock = self._city_locks.setdefault(city_key, threading.Lock())

        with city_lock:
            # Another thread may have loaded it while we were waiting
            entry = self._city_graphs.get(city_key)
            if entry is not None:
                return entry

            path = self._get_city_graph_cache_path(city)
            data = None

            if path.exists():
                t0 = time.perf_counter()
                data = self._read_pickle(path)

                if data is not None:
                    print(
                        f"DM: Loaded cached city graph for {city} "
                        f"in {time.perf_counter() - t0:.2f}s"
                    )

            if data is None:
                data = self._download_city_graph(city)
                self._write_pickle(path, data)

            entry = self._build_city_entry(data)

            with self._city_graphs_lock:
                self._city_graphs[city_key] = entry

            return entry

    def _download_city_graph(self, city: str) -> dict:
        """
        Downloads the walking graph of the whole city (boundary + buffer).
        """
        query = self.CITY_PLACE_QUERIES.get(self._safe_city(city), city)

        print(f"DM: Downloading city graph for {city} ('{query}'). This only happens once...")
        t0 = time.perf_counter()

        boundary_gdf = ox.geocode_to_gdf(query)

        # Buffer the boundary in meters (projected CRS), then back to WGS84
        boundary_proj = ox.projection.project_gdf(boundary_gdf)
        boundary_proj["geometry"] = boundary_proj.geometry.buffer(self.CITY_BOUNDARY_BUFFER_M)
        boundary = boundary_proj.to_crs("EPSG:4326").geometry.iloc[0]

        G = ox.graph_from_polygon(boundary, network_type=self.NETWORK_TYPE)

        print(
            f"DM: Downloaded city graph for {city}: {len(G.nodes)} nodes, "
            f"{len(G.edges)} edges in {time.perf_counter() - t0:.1f}s"
        )

        return {
            "version": self.GRAPH_CACHE_VERSION,
            "network_type": self.NETWORK_TYPE,
            "graph": G,
            "boundary": boundary,
        }

    def _build_city_entry(self, data: dict) -> dict:
        """
        Precomputes node coordinate arrays so cropping is a vectorized operation.
        """
        G = data["graph"]

        node_ids = list(G.nodes)
        lats = np.fromiter((G.nodes[n]["y"] for n in node_ids), dtype=float, count=len(node_ids))
        lons = np.fromiter((G.nodes[n]["x"] for n in node_ids), dtype=float, count=len(node_ids))

        return {
            "graph": G,
            "boundary": data.get("boundary"),
            "node_ids": np.array(node_ids, dtype=object),
            "lat_rad": np.radians(lats),
            "lon_rad": np.radians(lons),
        }

    def _city_covers_area(self, entry: dict, area: Area) -> bool:
        """
        Checks whether the requested circular area lies inside the city graph boundary.
        """
        boundary = entry.get("boundary")

        if boundary is None:
            return True

        circle = self._area_to_shapely_circle(area, self.CROP_MARGIN_M)

        return boundary.covers(circle)

    def _crop_graph(self, entry: dict, area: Area) -> nx.MultiDiGraph:
        """
        Extracts the nodes within area.radius_m (+ margin) of area.center
        using a vectorized haversine distance.
        """
        earth_radius_m = 6371008.8

        lat0 = math.radians(area.center.lat)
        lon0 = math.radians(area.center.lon)

        dlat = entry["lat_rad"] - lat0
        dlon = entry["lon_rad"] - lon0

        a = (
            np.sin(dlat / 2.0) ** 2
            + math.cos(lat0) * np.cos(entry["lat_rad"]) * np.sin(dlon / 2.0) ** 2
        )
        distances = 2.0 * earth_radius_m * np.arcsin(np.sqrt(a))

        mask = distances <= (area.radius_m + self.CROP_MARGIN_M)
        selected_nodes = entry["node_ids"][mask].tolist()

        sub = entry["graph"].subgraph(selected_nodes).copy()

        if self.KEEP_LARGEST_COMPONENT and len(sub.nodes) > 0:
            largest = max(nx.weakly_connected_components(sub), key=len)
            if len(largest) < len(sub.nodes):
                sub = sub.subgraph(largest).copy()

        return sub

    # ----------------------------------------------------------
    # Area graph (fallback when the city graph does not cover the area)
    # ----------------------------------------------------------
    def _load_area_graph(self, area: Area, city: str) -> nx.MultiDiGraph:
        path = self._get_area_graph_cache_path(area, city)

        if path.exists():
            data = self._read_pickle(path)
            if data is not None:
                print(f"DM: Loading cached area graph: {path.name}")
                return data["graph"]

        print(f"DM: Downloading area graph for city {city}")
        t0 = time.perf_counter()

        G = ox.graph_from_point(
            (area.center.lat, area.center.lon),
            dist=area.radius_m + self.CROP_MARGIN_M,
            network_type=self.NETWORK_TYPE,
        )

        print(f"DM: Downloaded area graph in {time.perf_counter() - t0:.1f}s")

        self._write_pickle(path, {
            "version": self.GRAPH_CACHE_VERSION,
            "network_type": self.NETWORK_TYPE,
            "graph": G,
            "boundary": None,
        })

        return G

    # ----------------------------------------------------------
    # Cache helpers
    # ----------------------------------------------------------
    def _safe_city(self, city: str) -> str:
        return city.strip().replace(" ", "_").lower()

    def _get_city_graph_cache_path(self, city: str) -> Path:
        return self.cache_dir / f"{self._safe_city(city)}_{self.NETWORK_TYPE}_city.pkl"

    def _get_area_graph_cache_path(self, area: Area, city: str) -> Path:
        lat = round(area.center.lat, 5)
        lon = round(area.center.lon, 5)
        radius = int(round(area.radius_m))

        return (
            self.cache_dir
            / f"{self._safe_city(city)}_{self.NETWORK_TYPE}_{lat}_{lon}_{radius}m_area.pkl"
        )

    def _read_pickle(self, path: Path) -> dict | None:
        """
        Reads a graph cache file. Returns None if it is unreadable or outdated.
        Only files written by this service are expected in cache_dir.
        """
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
        except Exception as exc:
            print(f"DM: Ignoring unreadable graph cache {path.name}: {exc}")
            return None

        if (
            not isinstance(data, dict)
            or data.get("version") != self.GRAPH_CACHE_VERSION
            or data.get("network_type") != self.NETWORK_TYPE
            or "graph" not in data
        ):
            print(f"DM: Ignoring outdated graph cache {path.name}")
            return None

        return data

    def _write_pickle(self, path: Path, data: dict):
        """
        Writes atomically so a crash never leaves a half-written cache file.
        """
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        with open(tmp_path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        os.replace(tmp_path, path)
        print(f"DM: Cached graph to {path.name}")

    def _area_to_shapely_circle(self, area: Area, margin_m: float = 0.0, segments: int = 32):
        """
        Approximates the circular area as a lon/lat shapely polygon.
        """
        radius = area.radius_m + margin_m
        lat = area.center.lat
        lon = area.center.lon

        dlat = radius / 111_320.0
        dlon = radius / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))

        coords = [
            (
                lon + dlon * math.cos(2 * math.pi * i / segments),
                lat + dlat * math.sin(2 * math.pi * i / segments),
            )
            for i in range(segments)
        ]

        return ShapelyPolygon(coords)

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