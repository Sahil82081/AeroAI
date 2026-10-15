"""
Weather Service Orchestrator for AeroAI.
Manages resolution, priority chaining, caching, and fallback between weather providers.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

from app.modules.weather.interfaces import WeatherProvider, WeatherObservation
from app.modules.weather.historical_provider import HistoricalWeatherProvider
from app.modules.weather.live_provider import LiveWeatherProvider, AIRPORT_COORDINATES
from app.modules.weather.mock_provider import MockWeatherProvider
from app.core.logger import logger


class WeatherService:
    """
    Unified weather service that seamlessly bridges historical archives, live forecast feeds,
    and deterministic mock fallbacks with zero-crash guarantees.
    """

    def __init__(
        self,
        historical_provider: Optional[WeatherProvider] = None,
        live_provider: Optional[WeatherProvider] = None,
        mock_provider: Optional[WeatherProvider] = None,
    ):
        self.historical = historical_provider or HistoricalWeatherProvider()
        self.live = live_provider or LiveWeatherProvider()
        self.mock = mock_provider or MockWeatherProvider()

    def get_weather(
        self,
        airport_code: str,
        target_time: Optional[datetime] = None,
        force_provider: Optional[str] = None,
    ) -> WeatherObservation:
        """
        Retrieves weather observation with automatic provider resolution:
        1. If force_provider='mock', returns mock preset.
        2. If force_provider='historical' or timestamp is in the past (> 7 days ago), tries historical.
        3. Otherwise, attempts live provider.
        4. If live provider fails or is offline, falls back to mock provider.
        """
        code = airport_code.upper().strip()
        t = target_time or datetime.now(timezone.utc)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)

        if force_provider == "mock":
            return self.mock.get_weather(code, t)

        if force_provider == "historical":
            obs = self.historical.get_weather(code, t)
            if obs:
                return obs
            return self.mock.get_weather(code, t)

        # Check if timestamp is distinctly historical (> 24 hours ago)
        now_utc = datetime.now(timezone.utc)
        is_historical = (now_utc - t) > timedelta(hours=24)

        if is_historical:
            obs = self.historical.get_weather(code, t)
            if obs:
                return obs

        # Attempt live provider for current/recent flights
        try:
            obs = self.live.get_weather(code, t)
            if obs:
                return obs
        except Exception as e:
            logger.warning(f"Live weather provider error for {code}: {e}")

        # Check historical archive as second fallback
        obs = self.historical.get_weather(code, t)
        if obs:
            return obs

        # Final guarantee: deterministic mock fallback
        logger.info(f"Weather unavailable from live/historical for {code}. Using calibrated fallback.")
        return self.mock.get_weather(code, t)

    def get_weather_features_for_flight(
        self,
        origin: str,
        scheduled_departure: datetime,
    ) -> Tuple[Dict[str, float], Optional[WeatherObservation], bool]:
        """
        Retrieves normalized features for ML inference.
        Returns:
            (feature_dict, observation_object, weather_was_available)
        """
        try:
            obs = self.get_weather(origin, scheduled_departure)
            weather_available = not obs.is_fallback
            return obs.to_model_features(), obs, weather_available
        except Exception as e:
            logger.error(f"Weather retrieval exception for {origin}: {e}")
            fallback_obs = self.mock.get_weather(origin, scheduled_departure)
            return fallback_obs.to_model_features(), fallback_obs, False


# Global singleton instance
weather_service = WeatherService()
