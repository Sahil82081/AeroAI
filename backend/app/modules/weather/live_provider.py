"""
Live Weather Provider for AeroAI.
Fetches real-time surface observations via Open-Meteo free aviation/meteorology API with TTL caching.
"""

import time
import math
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx

from app.modules.weather.interfaces import WeatherProvider, WeatherObservation
from app.core.logger import logger

# Major Airport Coordinates (IATA -> Latitude, Longitude)
AIRPORT_COORDINATES: Dict[str, Dict[str, float]] = {
    # New York Metro Hubs
    "EWR": {"lat": 40.6895, "lon": -74.1745, "name": "Newark Liberty International"},
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "John F. Kennedy International"},
    "LGA": {"lat": 40.7769, "lon": -73.8740, "name": "LaGuardia Airport"},
    # Major US Hubs
    "ORD": {"lat": 41.9742, "lon": -87.9073, "name": "Chicago O'Hare"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "name": "Los Angeles International"},
    "SFO": {"lat": 37.6213, "lon": -122.3790, "name": "San Francisco International"},
    "ATL": {"lat": 33.6407, "lon": -84.4277, "name": "Hartsfield-Jackson Atlanta"},
    "DFW": {"lat": 32.8998, "lon": -97.0403, "name": "Dallas/Fort Worth International"},
    "DEN": {"lat": 39.8561, "lon": -104.6737, "name": "Denver International"},
    "BOS": {"lat": 42.3656, "lon": -71.0096, "name": "Boston Logan"},
    "MIA": {"lat": 25.7959, "lon": -80.2870, "name": "Miami International"},
    "SEA": {"lat": 47.4502, "lon": -122.3088, "name": "Seattle-Tacoma"},
    "DCA": {"lat": 38.8512, "lon": -77.0402, "name": "Ronald Reagan Washington National"},
    # Indian Aviation Corridors (Supports Golden Triangle Demo)
    "BOM": {"lat": 19.0896, "lon": 72.8656, "name": "Chhatrapati Shivaji Maharaj Mumbai"},
    "DEL": {"lat": 28.5562, "lon": 77.1000, "name": "Indira Gandhi International Delhi"},
    "JAI": {"lat": 26.8242, "lon": 75.8122, "name": "Jaipur International"},
    "BLR": {"lat": 13.1986, "lon": 77.7066, "name": "Kempegowda Bengaluru"},
}


class LiveWeatherProvider(WeatherProvider):
    """
    Live meteorological observation provider backed by the free Open-Meteo REST API.
    Includes in-memory TTL caching (10 minutes) and strict timeout budgets.
    """

    CACHE_TTL_SECONDS = 600  # 10 minutes

    def __init__(self, timeout: float = 4.0):
        self.timeout = timeout
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get_weather(self, airport_code: str, target_time: datetime) -> Optional[WeatherObservation]:
        code = airport_code.upper().strip()
        coords = AIRPORT_COORDINATES.get(code)
        if not coords:
            return None

        # Check Cache
        now_ts = time.time()
        cached = self.cache.get(code)
        if cached and (now_ts - cached["timestamp"] < self.CACHE_TTL_SECONDS):
            return cached["observation"]

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,wind_gusts_10m,visibility",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, params=params)
                if res.status_code != 200:
                    logger.warning(f"Live weather API returned status {res.status_code} for {code}")
                    return None

                data = res.json()
                current = data.get("current", {})

                # Conversions to standard aviation units (Fahrenheit, mph, inches, mb, miles)
                temp_c = float(current.get("temperature_2m", 15.0))
                temp_f = temp_c * 9.0 / 5.0 + 32.0

                humid = float(current.get("relative_humidity_2m", 60.0))

                # Approximate dewpoint via Magnus-Tetens formula
                a = 17.27
                b = 237.7
                alpha = ((a * temp_c) / (b + temp_c)) + math.log(max(0.01, humid / 100.0))
                dewp_c = (b * alpha) / (a - alpha)
                dewp_f = dewp_c * 9.0 / 5.0 + 32.0

                wind_kmh = float(current.get("wind_speed_10m", 10.0))
                wind_mph = wind_kmh * 0.621371

                gust_kmh = float(current.get("wind_gusts_10m", wind_kmh))
                gust_mph = gust_kmh * 0.621371

                precip_mm = float(current.get("precipitation", 0.0))
                precip_in = precip_mm / 25.4

                pressure_hpa = float(current.get("surface_pressure", 1013.25))

                visib_m = float(current.get("visibility", 10000.0))
                visib_miles = min(10.0, visib_m / 1609.34)

                # Determine operational condition
                if precip_in > 0.1 and temp_f <= 32:
                    condition = "SNOW"
                elif precip_in > 0.05:
                    condition = "RAIN"
                elif visib_miles < 3.0:
                    condition = "FOG"
                elif wind_mph >= 25.0:
                    condition = "HIGH_WIND"
                elif humid > 85.0:
                    condition = "CLOUDY"
                else:
                    condition = "CLEAR"

                obs = WeatherObservation(
                    airport_code=code,
                    timestamp=datetime.now(timezone.utc),
                    temp_f=round(temp_f, 1),
                    dewp_f=round(dewp_f, 1),
                    humid_pct=round(humid, 1),
                    wind_speed_mph=round(wind_mph, 1),
                    wind_gust_mph=round(gust_mph, 1),
                    precip_in=round(precip_in, 3),
                    pressure_mb=round(pressure_hpa, 1),
                    visib_miles=round(visib_miles, 1),
                    condition=condition,
                    is_fog=bool(visib_miles < 3.0),
                    is_high_wind=bool(wind_mph >= 25.0 or gust_mph >= 30.0),
                    is_freezing=bool(temp_f <= 32.0),
                    has_precip=bool(precip_in > 0.0),
                    source="OPEN_METEO_LIVE",
                    is_fallback=False,
                )

                self.cache[code] = {"timestamp": now_ts, "observation": obs}
                return obs

        except Exception as e:
            logger.warning(f"Live weather fetch failed for {code}: {e}")
            return None
