from domain.dto.common import Point
from math import radians, cos, sin, asin, sqrt

def haversine_distance_m(p1: Point, p2: Point) -> float:
        """
        Calculate the great-circle distance in meters between two points.
        The function must accept both Point and GeoPoint
        """
        lat1, lon1, lat2, lon2 = map(
        radians,
        [p1.lat, p1.lon, p2.lat, p2.lon]
        )
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        R = 6371000 # Radius of the Earth in meters
        return R * c