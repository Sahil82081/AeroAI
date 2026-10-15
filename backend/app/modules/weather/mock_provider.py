"""
Mock Weather Provider for AeroAI.
Provides deterministic, zero-network fallback meteorological scenarios.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.modules.weather.interfaces import WeatherProvider, WeatherObservation

PRESET_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "CLEAR": {
        "temp_f": 65.0,
        "dewp_f": 45.0,
        "humid_pct": 50.0,
        "wind_speed_mph": 7.5,
        "wind_gust_mph": 10.0,
        "precip_in": 0.0,
        "pressure_mb": 1014.2,
        "visib_miles": 10.0,
        "condition": "CLEAR",
    },
    "FOG": {
        "temp_f": 48.0,
        "dewp_f": 47.0,
        "humid_pct": 96.0,
        "wind_speed_mph": 3.0,
        "wind_gust_mph": 5.0,
        "precip_in": 0.0,
        "pressure_mb": 1018.0,
        "visib_miles": 1.2,
        "condition": "FOG",
    },
    "THUNDERSTORM": {
        "temp_f": 74.0,
        "dewp_f": 68.0,
        "humid_pct": 85.0,
        "wind_speed_mph": 28.0,
        "wind_gust_mph": 39.0,
        "precip_in": 0.45,
        "pressure_mb": 1002.5,
        "visib_miles": 2.5,
        "condition": "THUNDERSTORM",
    },
    "WINTER_STORM": {
        "temp_f": 26.0,
        "dewp_f": 22.0,
        "humid_pct": 88.0,
        "wind_speed_mph": 26.0,
        "wind_gust_mph": 36.0,
        "precip_in": 0.25,
        "pressure_mb": 1005.0,
        "visib_miles": 1.5,
        "condition": "SNOW",
    },
}


class MockWeatherProvider(WeatherProvider):
    """
    Deterministic zero-network fallback provider.
    Ensures predictions and testing never fail if live or historical archives are inaccessible.
    """

    def __init__(self, default_preset: str = "CLEAR"):
        self.default_preset = default_preset

    def get_weather(
        self,
        airport_code: str,
        target_time: Optional[datetime] = None,
        preset: Optional[str] = None,
    ) -> WeatherObservation:
        p = preset or self.default_preset
        data = PRESET_SCENARIOS.get(p.upper(), PRESET_SCENARIOS["CLEAR"])

        t = target_time or datetime.now(timezone.utc)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)

        temp = data["temp_f"]
        wind = data["wind_speed_mph"]
        gust = data["wind_gust_mph"]
        visib = data["visib_miles"]
        precip = data["precip_in"]

        return WeatherObservation(
            airport_code=airport_code.upper().strip(),
            timestamp=t,
            temp_f=temp,
            dewp_f=data["dewp_f"],
            humid_pct=data["humid_pct"],
            wind_speed_mph=wind,
            wind_gust_mph=gust,
            precip_in=precip,
            pressure_mb=data["pressure_mb"],
            visib_miles=visib,
            condition=data["condition"],
            is_fog=bool(visib < 3.0),
            is_high_wind=bool(wind >= 25.0 or gust >= 30.0),
            is_freezing=bool(temp <= 32.0),
            has_precip=bool(precip > 0.0),
            source="MOCK_FALLBACK",
            is_fallback=True,
        )
