# core/geospatial_engine/service.py
"""
Geospatial Engine
------------------------------------
Implements the IGeospatialService interface.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

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

    def __init__(self, context_data_access: IContextDataAccess):
        self.context_data_access = context_data_access

    def get_routes_context(
        self,
        candidates: RouteCandidates
    ) -> ContextDescription:
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

        urban_request = UrbanDataRequest(
            covered_area=context_area,
            include_shadow_zones=True,
            include_water_points=True,
            include_police_offices=True,
            include_parks=True,
            include_benches=True,
            max_distance_m=100,
        )

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

        # 4. Correlate the shared contextual data with each route.
        contexts = [
            self._build_route_context(
                route,
                weather_data,
                urban_data,
            )
            for route in candidates.items
        ]

        # 5. Build the final contextual description.
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
        weather_data: WeatherData,
        urban_data: UrbanData,
    ) -> RouteContext:
        """
        Correlate shared contextual data with a specific route.
        """

        weather_context = self._build_weather_context(
            route,
            weather_data,
        )

        urban_context = self._build_urban_context(
            route,
            urban_data,
        )

        return RouteContext(
            route_id=route.id,
            weather=weather_context,
            urban=urban_context,
        )

    def _build_weather_context(
        self,
        route: RouteCandidate,
        weather_data: WeatherData,
    ) -> WeatherContext:
        """
        Associate weather observations relevant to the route.

        Current implementation filters observations according to the
        expected route travel time.

        TODO:
        - Use request/departure time instead of datetime.now().
        - Add spatial filtering when weather is sampled at multiple locations.
        - Define handling of missing weather observations.
        """

        if not weather_data.weather_points:
            return WeatherContext(
                observations=[],
                alert_level=None,
            )

        start_time = datetime.now(timezone.utc)

        # route.eta currently represents travel duration in seconds.
        end_time = start_time + timedelta(seconds=route.eta)

        relevant_observations = []

        for observation in weather_data.weather_points:
            timestamp = observation.timestamp

            # TODO:
            # Prefer normalizing timestamps at the DM/provider boundary.
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            if start_time <= timestamp <= end_time:
                relevant_observations.append(observation)

        return WeatherContext(
            observations=relevant_observations,
            alert_level=None,
        )

    def _build_urban_context(
        self,
        route: RouteCandidate,
        urban_data: UrbanData,
    ) -> UrbanContext:
        """
        Associate urban features with a route according to their
        spatial relationship with the route geometry.

        TODO:
        - Calculate point-to-segment distance instead of point-to-vertex.
        - Implement polygon/route intersection for parks.
        - Implement shadow-zone correlation.
        """

        # Route relevance threshold.
        # TODO: Move to GE/application configuration.
        max_distance_m = 100.0

        water_points = [
            water_point
            for water_point in urban_data.water_points
            if self._distance_to_route_m(
                water_point.location,
                route,
            ) <= max_distance_m
        ]

        police_offices = [
            police_office
            for police_office in urban_data.police_offices
            if self._distance_to_route_m(
                police_office.location,
                route,
            ) <= max_distance_m
        ]

        benches = [
            bench
            for bench in urban_data.benches
            if self._distance_to_route_m(
                bench.location,
                route,
            ) <= max_distance_m
        ]

        return UrbanContext(
            water_points=water_points,
            police_offices=police_offices,
            benches=benches,

            # TODO: Implement route/polygon spatial correlation.
            parks=[],

            # TODO: Implement shadow-zone spatial correlation.
            shadow_zones=[],
        )

    # ----------------------------
    # SPATIAL CORRELATION
    # ----------------------------

    def _distance_to_route_m(
        self,
        point: Point,
        route: RouteCandidate,
    ) -> float:
        """
        Return the approximate minimum distance between a point and
        the route using route geometry vertices.

        TODO:
        Calculate point-to-segment distance instead of only
        point-to-vertex distance.
        """

        coordinates = route.geometry.coordinates

        if not coordinates:
            raise ValueError(
                f"Route {route.id} geometry contains no coordinates."
            )

        return min(
            haversine_distance_m(point, route_point)
            for route_point in coordinates
        )