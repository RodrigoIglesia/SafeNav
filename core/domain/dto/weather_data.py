"""
weather_data.py
----------------
Defines internal data transfer objects related to meteorological and environmental conditions.
These structures are used by Data Management (DM) and Context Analyzer (CA)
to evaluate comfort and safety levels for pedestrian routes.
"""

from pydantic import BaseModel, Field
from typing import Optional


class WeatherData(BaseModel):
    """Represents processed weather information relevant for route evaluation."""
    temperature: float = Field(
        ..., description="Current temperature in degrees Celsius"
    )
    uv_index: float = Field(
        ..., ge=0, le=12, description="Current UV radiation index (0–12)"
    )
    alert_level: Optional[str] = Field(
        None, description="Weather alert level (e.g., none, heat_warning, storm_warning)"
    )

    class Config:
        schema_extra = {
            "example": {
                "temperature": 33.5,
                "uv_index": 8.3,
                "alert_level": "heat_warning"
            }
        }
