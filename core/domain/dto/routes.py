"""
routes.py
----------
Defines core data transfer objects related to routing operations in SafeNav:
- RouteRequest (input from user)
- RouteResponse (output to UI)
- RouteCandidate (internal route representation)
- RouteScores & SegmentScore (comfort/safety evaluation)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from .common import Point, Path, RoutePreferences, ResponseMetadata


# === Route Request ===

class RouteRequest(BaseModel):
    """Represents a route request made by the user through the API."""
    origin: Point = Field(..., description="Starting point of the route")
    destination: Point = Field(..., description="Ending point of the route")
    preferences: Optional[RoutePreferences] = Field(
        None, description="User-defined routing preferences (comfort, time, sun exposure)"
    )


# === Route Candidates ===

class RouteCandidate(BaseModel):
    """Represents a possible route option computed by the Routing Engine."""
    id: str = Field(..., description="Unique identifier for the candidate route")
    geometry: Path = Field(..., description="Ordered set of coordinates forming the route path")
    eta: float = Field(..., gt=0, description="Estimated time of arrival (in seconds)")
    distance: float = Field(..., gt=0, description="Route distance (in meters)")


class RouteCandidates(BaseModel):
    """Wrapper for multiple route candidates generated for a request."""
    request_id: str = Field(..., description="Identifier for the route request")
    items: List[RouteCandidate] = Field(..., description="List of route candidate objects")


# === Route Scores ===

class SegmentScore(BaseModel):
    """Represents safety and comfort scores for a route segment."""
    segment_id: str = Field(..., description="Segment identifier within the route")
    comfort: float = Field(..., ge=0, le=1, description="Comfort score (0–1)")
    safety: float = Field(..., ge=0, le=1, description="Safety score (0–1)")


class RouteScore(BaseModel):
    """Aggregated safety and comfort scores for an entire route."""
    id: str = Field(..., description="Identifier of the route being scored")
    comfort_score: float = Field(..., ge=0, le=1, description="Global comfort score for the route")
    safety_score: float = Field(..., ge=0, le=1, description="Global safety score for the route")
    segment_scores: Optional[List[SegmentScore]] = Field(
        None, description="Optional detailed per-segment scores"
    )

class RouteScores(BaseModel):
    """Wrapper for route scores associated with a route request."""
    scores: List[RouteScore] = Field(..., description="List of route scores for each candidate")


# === Route Response ===

class RouteResponse(BaseModel):
    """Response object returned by the API to the user interface."""
    routes: RouteCandidates = Field(..., description="List of route options available to the user")
    scores: Optional[RouteScores] = Field(
        None, description="Optional list of comfort/safety scores per route"
    )
    metadata: ResponseMetadata = Field(
        default_factory=lambda: ResponseMetadata(
            timestamp=datetime.now(timezone.utc), request_id="N/A", source="SafeNavCore"
        ),
        description="Response metadata (timestamp, source, request_id)",
    )
