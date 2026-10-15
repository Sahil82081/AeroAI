"""
REST Endpoints for Aviation Weather Intelligence.
Provides surface weather observations and forecasts for airports across the network.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.modules.weather.service import weather_service
from app.modules.weather.interfaces import WeatherObservation
from app.modules.weather.live_provider import AIRPORT_COORDINATES

router = APIRouter(prefix="/weather", tags=["Aviation Weather Intelligence"])


@router.get(
    "/observation",
    response_model=WeatherObservation,
    summary="Get Airport Surface Weather Observation",
    description="Retrieves current or historical surface weather for a given airport (temperature, wind, visibility, precipitation, pressure)."
)
def get_airport_weather(
    airport: str = Query(..., example="JFK", description="Three-letter IATA airport code"),
    timestamp: Optional[datetime] = Query(None, description="Target observation timestamp in ISO 8601 (defaults to current time)"),
    force_provider: Optional[str] = Query(None, description="Optional override provider: 'live', 'historical', or 'mock'")
) -> WeatherObservation:
    try:
        t = timestamp or datetime.now(timezone.utc)
        obs = weather_service.get_weather(
            airport_code=airport,
            target_time=t,
            force_provider=force_provider,
        )
        return obs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather retrieval error: {str(e)}")


@router.get(
    "/supported-airports",
    summary="List Supported Airports for Live Meteorological Tracking",
    description="Returns geographical coordinates and metadata for supported hub airports."
)
def get_supported_airports() -> Dict[str, Any]:
    return {
        "count": len(AIRPORT_COORDINATES),
        "airports": AIRPORT_COORDINATES,
    }
