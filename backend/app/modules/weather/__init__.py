"""
Weather Intelligence Module for AeroAI.
Provides historical, live, and fallback meteorological intelligence for flight operations.
"""

from app.modules.weather.interfaces import WeatherProvider, WeatherObservation
from app.modules.weather.historical_provider import HistoricalWeatherProvider
from app.modules.weather.live_provider import LiveWeatherProvider, AIRPORT_COORDINATES
from app.modules.weather.mock_provider import MockWeatherProvider
from app.modules.weather.service import WeatherService, weather_service

__all__ = [
    "WeatherProvider",
    "WeatherObservation",
    "HistoricalWeatherProvider",
    "LiveWeatherProvider",
    "AIRPORT_COORDINATES",
    "MockWeatherProvider",
    "WeatherService",
    "weather_service",
]
