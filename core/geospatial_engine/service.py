# core/geospatial_engine/service.py
"""
Geospatial Engine
------------------------------------
Implements the IGeospatialService interface.

Correlation of contextual data with routes only relies on SafeNav DTOs,
never on provider-specific characteristics:

- Weather: each observation is valid from its timestamp until the next
  observation at the same location (time step inferred from the data).
  Observations whose validity overlaps the trip are selected. When weather
  is sampled at several locations, the location closest to the route is used.
- Urban: distances are computed between feature geometries and the full
  route polyline (point-to-segment, polygon-to-line) in a local metric
  projection, not only to route vertices.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from statistics import median
import math

import numpy as np
import shapely
from shapely.geometry import (
    LineString as ShapelyLineString,
    Point as ShapelyPoint,
    Polygon as ShapelyPolygon,
)

from domain.dto.common import Point, Area
from domain.dto.routes import RouteCandidates, RouteCandidate
from domain.dto.geospatial import (
    WeatherDataRequest,
    WeatherContext,
    UrbanDataRequest,
    WeatherData,
    UrbanData,
    UrbanContext,
    ContextDescription,
    RouteContext,
)
from interfaces.i_geospatial_service import IGeospatialService
from interfaces.i_context_data_access import IContextDataAccess

from common.utils import haversine_distance_m, build_area_from_points


EARTH_RADIUS_M = 6371008.8


class _LocalMetricProjection:
    """
    Equirectangular projection centered on an origin point.

    Converts lat/lon to planar meters. Distortion is negligible at city
    scale (< 0.1% within ~20 km of the origin), which is enough for
    "is this feature within N meters of the route" checks.
    """

    def __init__(self, origin: Point):
        self.lat0 = math.radians(origin.lat)
        self.lon0 = math.radians(origin.lon)
        self.cos_lat0 = math.cos(self.lat0)

    def to_xy(self, points) -> np.ndarray:
        """
        Projects an iterable of objects with .lat/.lon into an (n, 2) array.
        """
        coords = np.array([(p.lat, p.lon) for p in points], dtype=float).reshape(-1, 2)

        lat = np.radians(coords[:, 0])
        lon = np.radians(coords[:, 1])

        x = EARTH_RADIUS_M * (lon - self.lon0) * self.cos_lat0
        y = EARTH_RADIUS_M * (lat - self.lat0)

        return np.column_stack((x, y))


@dataclass
class _PreparedFeatures:
    """
    Features with a valid geometry and their projected shapely geometries,
    aligned by index.
    """
    features: list
    geometries: np.ndarray

    @classmethod
    def empty(cls):
        return cls(features=[], geometries=np.array([], dtype=object))


class GeospatialEngine(IGeospatialService):
    """
    Implements IGeospatialService.

    Responsible for:
    - Analyzing route candidate geometries.
    - Building a shared contextual acquisition area.
    - Requesting contextual data through Data Management.
    - Correlating contextual data with each route candidate.
    - Building the ContextDescription.
    """

    # TODO: Move to GE/application configuration.
    DEFAULT_MAX_DISTANCE_M = 100.0
    DEFAULT_WEATHER_STEP = timedelta(minutes=60)

    # If no observation overlaps the trip, the closest one in time is used
    # as long as it is not further away than this.
    MAX_WEATHER_TIME_GAP = timedelta(hours=3)

    def __init__(self, context_data_access: IContextDataAccess):
        self.context_data_access = context_data_access

    def get_routes_context(self, candidates: RouteCandidates) -> ContextDescription:
        """
        Build contextual descriptions for a set of route candidates.

        Contextual data is retrieved once for a shared area covering
        all route candidates. The retrieved data is then correlated
        individually with each route.
        """

        if not candidates.items:
            return ContextDescription(items=[])

        # 1. Analyze route candidates and build shared context area.
        context_area = self._build_candidates_context_area(candidates)

        print(f"GE: Shared covered area: {context_area}")

        # 2. Derive contextual data requests.
        #
        # TODO:
        # Configuration parameters should come from application/backoffice
        # configuration and, where appropriate, from the route request.
        weather_request = WeatherDataRequest(
            covered_area=context_area,
            start_time=None,
            end_time=None,
            time_step_minutes=60,
        )
        print(f"GE: Weather request: {weather_request}")

        urban_request = UrbanDataRequest(
            covered_area=context_area,
            include_shadow_zones=True,
            include_water_points=True,
            include_police_offices=True,
            include_parks=True,
            include_benches=True,
            max_distance_m=100,
        )
        print(f"GE: Urban request: {urban_request}")

        # 3. Retrieve shared contextual data through Data Management.
        # Weather and urban data are independent and can be fetched in parallel.
        with ThreadPoolExecutor(max_workers=2) as executor:
            weather_future = executor.submit(
                self.context_data_access.get_weather_data,
                weather_request,
            )

            urban_future = executor.submit(
                self.context_data_access.get_urban_data,
                urban_request,
            )

            weather_data = weather_future.result()
            urban_data = urban_future.result()

        print(
            f"GE: Received {len(weather_data.weather_points)} weather observations, "
            f"{len(urban_data.water_points)} water points, {len(urban_data.benches)} benches, "
            f"{len(urban_data.parks)} parks, {len(urban_data.police_offices)} police offices, "
            f"{len(urban_data.shadow_zones)} shadow zones"
        )

        # 4. Prepare shared data once (projection + geometries) for all routes.
        projection = _LocalMetricProjection(context_area.center)

        max_distance_m = (
            urban_request.max_distance_m
            if urban_request.max_distance_m is not None
            else self.DEFAULT_MAX_DISTANCE_M
        )

        default_weather_step = (
            timedelta(minutes=weather_request.time_step_minutes)
            if weather_request.time_step_minutes
            else self.DEFAULT_WEATHER_STEP
        )

        prepared_urban = {
            "water_points": self._prepare_point_features(urban_data.water_points, projection),
            "police_offices": self._prepare_point_features(urban_data.police_offices, projection),
            "benches": self._prepare_point_features(urban_data.benches, projection),
            "parks": self._prepare_area_features(urban_data.parks, projection),
            "shadow_zones": self._prepare_area_features(urban_data.shadow_zones, projection),
        }

        # 5. Correlate the shared contextual data with each route.
        contexts = []

        for route in candidates.items:
            route_geometry = self._route_to_geometry(route, projection)

            contexts.append(
                self._build_route_context(
                    route,
                    route_geometry,
                    weather_data,
                    prepared_urban,
                    projection,
                    max_distance_m,
                    default_weather_step,
                )
            )

        # 6. Build the final contextual description.
        return ContextDescription(items=contexts)

    # ----------------------------
    # CONTEXT AREA BUILDING
    # ----------------------------

    def _build_candidates_context_area(self, candidates: RouteCandidates) -> Area:
        """
        Build a shared contextual area covering all route candidates.

        Route geometries are sampled to reduce the number of points used
        when calculating the shared area.

        TODO:
        Replace the circular area with a buffered route corridor / union
        when more precise spatial queries are required.
        """

        context_points: list[Point] = []

        for route in candidates.items:
            sampled_points = self._sample_route_points(route)

            context_points.extend(
                Point(lat=point.lat, lon=point.lon)
                for point in sampled_points
            )

        if not context_points:
            raise ValueError(
                "Cannot build context area from empty route geometries."
            )

        return build_area_from_points(context_points)

    def _sample_route_points(self, route: RouteCandidate) -> list[Point]:
        """
        Sample route geometry at approximately fixed distance intervals.

        The first and last route points are always included.
        """

        coordinates = route.geometry.coordinates

        if not coordinates:
            raise ValueError(
                f"Route {route.id} geometry contains no coordinates."
            )

        sample_distance_m = 100.0  # TODO: Move to configuration.

        sampled_points = [coordinates[0]]
        accumulated_distance = 0.0

        for previous, current in zip(
            coordinates[:-1],
            coordinates[1:]
        ):
            segment_length = haversine_distance_m(
                previous,
                current
            )

            accumulated_distance += segment_length

            if accumulated_distance >= sample_distance_m:
                sampled_points.append(current)
                accumulated_distance = 0.0

        # Ensure destination is always included.
        if sampled_points[-1] != coordinates[-1]:
            sampled_points.append(coordinates[-1])

        return sampled_points

    # ----------------------------
    # ROUTE CONTEXT BUILDING
    # ----------------------------

    def _build_route_context(
        self,
        route: RouteCandidate,
        route_geometry,
        weather_data: WeatherData,
        prepared_urban: dict,
        projection: _LocalMetricProjection,
        max_distance_m: float,
        default_weather_step: timedelta,
    ) -> RouteContext:
        """
        Correlate shared contextual data with a specific route.
        """

        weather_context = self._build_weather_context(
            route,
            route_geometry,
            weather_data,
            projection,
            default_weather_step,
        )
        print(
            f"GE: Route {route.id} weather context: "
            f"{len(weather_context.observations)} observations"
        )

        urban_context = self._build_urban_context(
            route_geometry,
            prepared_urban,
            max_distance_m,
        )
        print(
            f"GE: Route {route.id} urban context: "
            f"{len(urban_context.water_points)} water points, "
            f"{len(urban_context.benches)} benches, "
            f"{len(urban_context.parks)} parks, "
            f"{len(urban_context.police_offices)} police offices, "
            f"{len(urban_context.shadow_zones)} shadow zones"
        )

        return RouteContext(
            route_id=route.id,
            weather=weather_context,
            urban=urban_context,
        )

    # ----------------------------
    # WEATHER CORRELATION
    # ----------------------------

    def _build_weather_context(
        self,
        route: RouteCandidate,
        route_geometry,
        weather_data: WeatherData,
        projection: _LocalMetricProjection,
        default_step: timedelta,
    ) -> WeatherContext:
        """
        Associate weather observations relevant to the route.

        1. Spatial: if observations come from several locations, use the
           location closest to the route.
        2. Temporal: each observation is valid during
           [timestamp, next timestamp). Observations whose validity overlaps
           the trip [start, start + eta] are selected.
        3. Fallback: if none overlaps, the observation closest in time is used
           when it is within MAX_WEATHER_TIME_GAP.

        TODO:
        - Use request/departure time instead of datetime.now().
        - Interpolate along the route when several locations are relevant.
        """

        observations = [
            observation
            for observation in weather_data.weather_points
            if observation.timestamp is not None
        ]

        if not observations:
            return WeatherContext(observations=[], alert_level=None)

        observations = self._select_closest_weather_location(
            observations,
            route_geometry,
            projection,
        )

        start_time = datetime.now(timezone.utc)

        # route.eta currently represents travel duration in seconds.
        end_time = start_time + timedelta(seconds=max(route.eta or 0, 0))

        intervals = self._weather_validity_intervals(observations, default_step)

        relevant_observations = [
            observation
            for observation, valid_from, valid_to in intervals
            if valid_from <= end_time and valid_to > start_time
        ]

        if not relevant_observations:
            closest = self._closest_weather_in_time(intervals, start_time, end_time)

            if closest is not None:
                relevant_observations = [closest]
            else:
                print(
                    f"GE: No weather observations near trip window "
                    f"{start_time.isoformat()} - {end_time.isoformat()}"
                )

        return WeatherContext(
            observations=relevant_observations,
            alert_level=None,
        )

    def _select_closest_weather_location(self, observations: list, route_geometry, projection):
        """
        Groups observations by location and keeps the group closest to the route.
        Observations without location are kept only if no located group exists.
        """
        groups: dict = {}

        for observation in observations:
            location = getattr(observation, "location", None)

            key = (
                (round(location.lat, 5), round(location.lon, 5))
                if location is not None
                else None
            )

            groups.setdefault(key, []).append(observation)

        located_keys = [key for key in groups if key is not None]

        if len(located_keys) <= 1:
            return groups[located_keys[0]] if located_keys else groups[None]

        def distance_to_route(key):
            lat, lon = key
            xy = projection.to_xy([Point(lat=lat, lon=lon)])[0]
            return route_geometry.distance(ShapelyPoint(xy))

        closest_key = min(located_keys, key=distance_to_route)

        return groups[closest_key]

    def _weather_validity_intervals(self, observations: list, default_step: timedelta):
        """
        Returns [(observation, valid_from, valid_to)] sorted by time.

        Each observation is valid until the next one. The last one uses the
        typical (median) step of the series, or default_step for a single
        observation.
        """
        normalized = sorted(
            ((self._as_utc(observation.timestamp), observation) for observation in observations),
            key=lambda item: item[0],
        )

        timestamps = [timestamp for timestamp, _ in normalized]

        gaps = [
            later - earlier
            for earlier, later in zip(timestamps[:-1], timestamps[1:])
            if later > earlier
        ]

        typical_step = median(gaps) if gaps else default_step

        intervals = []

        for index, (timestamp, observation) in enumerate(normalized):
            next_timestamp = None

            for candidate in timestamps[index + 1:]:
                if candidate > timestamp:
                    next_timestamp = candidate
                    break

            valid_to = next_timestamp if next_timestamp is not None else timestamp + typical_step

            # Guard against large holes in the series: never extend validity
            # beyond the typical step.
            valid_to = min(valid_to, timestamp + typical_step)

            intervals.append((observation, timestamp, valid_to))

        return intervals

    def _closest_weather_in_time(self, intervals, start_time: datetime, end_time: datetime):
        best = None
        best_gap = None

        for observation, valid_from, valid_to in intervals:
            if valid_to <= start_time:
                gap = start_time - valid_to
            elif valid_from > end_time:
                gap = valid_from - end_time
            else:
                gap = timedelta(0)

            if best_gap is None or gap < best_gap:
                best, best_gap = observation, gap

        if best_gap is not None and best_gap <= self.MAX_WEATHER_TIME_GAP:
            return best

        return None

    def _as_utc(self, timestamp: datetime) -> datetime:
        """
        Normalizes a timestamp to timezone-aware UTC.

        Data Management must provide timezone-aware timestamps; naive values
        are interpreted as UTC as a last resort.
        """
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            return timestamp.replace(tzinfo=timezone.utc)

        return timestamp.astimezone(timezone.utc)

    # ----------------------------
    # URBAN CORRELATION
    # ----------------------------

    def _build_urban_context(
        self,
        route_geometry,
        prepared_urban: dict,
        max_distance_m: float,
    ) -> UrbanContext:
        """
        Associate urban features with a route according to their
        distance to the route geometry (full polyline, not only vertices).

        - Point features: point-to-polyline distance.
        - Area features (parks, shadow zones): polygon-to-polyline distance,
          0 when the route crosses the area.
        """

        return UrbanContext(
            water_points=self._features_within(prepared_urban["water_points"], route_geometry, max_distance_m),
            police_offices=self._features_within(prepared_urban["police_offices"], route_geometry, max_distance_m),
            benches=self._features_within(prepared_urban["benches"], route_geometry, max_distance_m),
            parks=self._features_within(prepared_urban["parks"], route_geometry, max_distance_m),
            shadow_zones=self._features_within(prepared_urban["shadow_zones"], route_geometry, max_distance_m),
        )

    def _features_within(self, prepared: _PreparedFeatures, route_geometry, max_distance_m: float) -> list:
        if not prepared.features:
            return []

        mask = shapely.dwithin(prepared.geometries, route_geometry, max_distance_m)

        return [
            feature
            for feature, keep in zip(prepared.features, mask)
            if keep
        ]

    # ----------------------------
    # GEOMETRY PREPARATION
    # ----------------------------

    def _route_to_geometry(self, route: RouteCandidate, projection: _LocalMetricProjection):
        """
        Builds the projected route geometry (LineString, or Point for a
        degenerate single-coordinate route).
        """
        coordinates = route.geometry.coordinates

        if not coordinates:
            raise ValueError(
                f"Route {route.id} geometry contains no coordinates."
            )

        xy = self._drop_consecutive_duplicates(projection.to_xy(coordinates))

        if len(xy) == 1:
            return ShapelyPoint(xy[0])

        return ShapelyLineString(xy)

    def _prepare_point_features(self, features, projection: _LocalMetricProjection) -> _PreparedFeatures:
        """
        Projects point features (with a `.location`) into shapely points.
        Features without a usable location are skipped.
        """
        valid = [
            feature
            for feature in features or []
            if self._is_valid_point(getattr(feature, "location", None))
        ]

        if not valid:
            return _PreparedFeatures.empty()

        xy = projection.to_xy([feature.location for feature in valid])

        return _PreparedFeatures(
            features=valid,
            geometries=shapely.points(xy),
        )

    def _prepare_area_features(self, features, projection: _LocalMetricProjection) -> _PreparedFeatures:
        """
        Projects area features (with a `.geometry` Polygon DTO, or a
        `.location` as fallback) into shapely geometries.

        Robust to imperfect provider geometries:
        - >= 3 distinct points: polygon, repaired if invalid.
        - 2 points: line. 1 point: point.
        - Features without usable geometry are skipped.
        """
        valid_features = []
        geometries = []

        for feature in features or []:
            geometry = self._area_feature_to_geometry(feature, projection)

            if geometry is None or geometry.is_empty:
                continue

            valid_features.append(feature)
            geometries.append(geometry)

        skipped = len(features or []) - len(valid_features)
        if skipped:
            print(f"GE: Skipped {skipped} area features without usable geometry")

        if not valid_features:
            return _PreparedFeatures.empty()

        return _PreparedFeatures(
            features=valid_features,
            geometries=np.array(geometries, dtype=object),
        )

    def _area_feature_to_geometry(self, feature, projection: _LocalMetricProjection):
        polygon_dto = getattr(feature, "geometry", None)
        coordinates = getattr(polygon_dto, "coordinates", None) if polygon_dto is not None else None

        if coordinates:
            points = [point for point in coordinates if self._is_valid_point(point)]

            if points:
                xy = self._drop_consecutive_duplicates(projection.to_xy(points))

                # Remove closing point to count distinct vertices
                if len(xy) > 1 and np.allclose(xy[0], xy[-1]):
                    xy = xy[:-1]

                if len(xy) >= 3:
                    polygon = ShapelyPolygon(xy)

                    if not polygon.is_valid:
                        polygon = shapely.make_valid(polygon)

                    return polygon

                if len(xy) == 2:
                    return ShapelyLineString(xy)

                return ShapelyPoint(xy[0])

        location = getattr(feature, "location", None)

        if self._is_valid_point(location):
            return ShapelyPoint(projection.to_xy([location])[0])

        return None

    def _is_valid_point(self, point) -> bool:
        if point is None:
            return False

        lat = getattr(point, "lat", None)
        lon = getattr(point, "lon", None)

        if lat is None or lon is None:
            return False

        return (
            math.isfinite(lat) and math.isfinite(lon)
            and -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
        )

    def _drop_consecutive_duplicates(self, xy: np.ndarray) -> np.ndarray:
        if len(xy) <= 1:
            return xy

        keep = np.ones(len(xy), dtype=bool)
        keep[1:] = np.any(np.abs(np.diff(xy, axis=0)) > 1e-6, axis=1)

        return xy[keep]

    # ----------------------------
    # SPATIAL CORRELATION
    # ----------------------------

    def _distance_to_route_m(
        self,
        point: Point,
        route: RouteCandidate,
    ) -> float:
        """
        Return the minimum distance in meters between a point and the
        route polyline (point-to-segment).
        """
        projection = _LocalMetricProjection(point)
        route_geometry = self._route_to_geometry(route, projection)

        return route_geometry.distance(ShapelyPoint(0.0, 0.0))