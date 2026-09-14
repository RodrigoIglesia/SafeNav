# core/geospatial_engine/service.py
"""
Geospatial Engine
------------------------------------
Implements the IGeospatialService interface.
"""

from domain.dto.common import Point, Area
from domain.dto.routes import RouteCandidates, RouteCandidate
from domain.dto.geospatial import \
    WeatherDataRequest,\
    WeatherContext, UrbanDataRequest, WeatherData, UrbanData, UrbanContext,\
    ContextDescription, RouteContext
from interfaces.i_geospatial_service import IGeospatialService
from interfaces.i_context_data_access import IContextDataAccess

from common.utils import haversine_distance_m, build_area_from_points

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta


class GeospatialEngine(IGeospatialService):
    """
    Implements IGeospatialService.
    Responsible for:
    - Route sampling
    - Building spatial queries
    - Calling Data Management (DM)
    - Transforming raw data into RouteContext
    """

    def __init__(self, context_data_access: IContextDataAccess):
        self.context_data_access =  context_data_access


    def get_routes_context(self, candidates: RouteCandidates) -> ContextDescription:

        contexts = []

        for route in candidates.items:

            # Build spatial query (shared geometry)
            area = self._build_context_area(route)
            print(f"GE: Covered area: {area}")

            # Build DM requests for IContextDataAccess
            # TODO: Config parameters should come from the API request and be selected in the UI configuration (backoffice)
            weather_request = WeatherDataRequest(
                covered_area=area,
                start_time=None,
                end_time=None,
                time_step_minutes=60
            )
            urban_request = UrbanDataRequest(
                covered_area=area,

                include_shadow_zones=True,
                include_water_points=True,
                include_police_offices=True,
                include_parks=True,
                include_benches=True,

                # buffer around route influence area
                max_distance_m=100
            )

            # IContextDataAccess -> Fetch raw data from DM (parallelized)
            # TODO:
            # Optimize contextual data retrieval across route candidates.
            # Candidate routes may overlap significantly, so weather/urban
            # data could potentially be requested once for their combined area.
            with ThreadPoolExecutor(max_workers=2) as executor:
                weather_future = executor.submit(
                    self.context_data_access.get_weather_data,
                    weather_request
                )

                urban_future = executor.submit(
                    self.context_data_access.get_urban_data,
                    urban_request
                )

                weather_data = weather_future.result()
                urban_data = urban_future.result()

            # Build route context
            route_context = self._build_route_context(
                route,
                weather_data,
                urban_data
            )

            contexts.append(route_context)

        return ContextDescription(items=contexts)

    # ----------------------------
    # QUERY BUILDING
    # ----------------------------
    def _build_context_area(self, route: RouteCandidate) -> Area:
        """
        Builds a spatial query from a route.

        Selects route points at approximately `sample_distance_m`
        intervals along the route and derives a covered area from them.
        """

        coordinates = route.geometry.coordinates

        if not coordinates:
            raise ValueError("Route geometry contains no coordinates.")

        sample_distance_m = 100.0  # TODO: configurable

        sampled_points = [coordinates[0]]

        accumulated_distance = 0.0

        for previous, current in zip(coordinates[:-1], coordinates[1:]):

            segment_length = haversine_distance_m(previous, current)
            accumulated_distance += segment_length

            if accumulated_distance >= sample_distance_m:
                sampled_points.append(current)
                accumulated_distance = 0.0

        # Ensure destination is always included
        if sampled_points[-1] != coordinates[-1]:
            sampled_points.append(coordinates[-1])


        return build_area_from_points(sampled_points)


    # ----------------------------
    # CONTEXT BUILDING
    # ----------------------------
    def _build_route_context(self, route: RouteCandidate, weather_data: WeatherData, urban_data: UrbanData) -> RouteContext:
        """
        Transform raw DM data into route-aware context.
        """

        weather_context = self._build_weather_context(route, weather_data)
        urban_context = self._build_urban_context(route, urban_data)

        return RouteContext(
            route_id=route.id,
            weather=weather_context,
            urban=urban_context
        )


    def _build_weather_context(self, route: RouteCandidate, weather_data: WeatherData) -> WeatherContext:
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

        # Assuming route.eta represents travel duration in seconds.
        end_time = start_time + timedelta(seconds=route.eta)

        relevant_observations = []

        for observation in weather_data.weather_points:
            timestamp = observation.timestamp

            # Normalize naive timestamps if necessary.
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            if start_time <= timestamp <= end_time:
                relevant_observations.append(observation)

        return WeatherContext(
            observations=relevant_observations,
            alert_level=None,
        )

    def _build_urban_context(self, route: RouteCandidate, urban_data: UrbanData) -> UrbanContext:
        """
        Associate urban features relevant to the route based on
        proximity and/or spatial intersection.

        TODO:
        - Calculate point-to-segment distance instead of point-to-vertex.
        - Implement polygon/route intersection for parks.
        - Implement shadow-zone correlation.
        """

        max_distance_m = 100.0  # TODO: Move to configuration.

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

    def _distance_to_route_m(self, point: Point, route: RouteCandidate)-> float:
        """
        Returns the approximate minimum distance between a point and
        the route using the route geometry vertices.

        TODO:
        Calculate distance to route segments instead of only vertices.
        """

        coordinates = route.geometry.coordinates

        if not coordinates:
            raise ValueError("Route geometry contains no coordinates.")

        return min(
            haversine_distance_m(point, route_point)
            for route_point in coordinates
        )