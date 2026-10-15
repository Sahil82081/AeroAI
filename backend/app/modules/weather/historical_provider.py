"""
Historical Weather Provider for AeroAI.
Reads synchronized NOAA/ASOS weather observations from data/flights/weather.csv.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime, timezone
import pandas as pd

from app.modules.weather.interfaces import WeatherProvider, WeatherObservation
from app.core.logger import logger

# Paths
MODULE_PATH = Path(__file__).resolve()
REPO_ROOT = MODULE_PATH.parents[4]
WEATHER_CSV_PATH = REPO_ROOT / "data" / "flights" / "weather.csv"


class HistoricalWeatherProvider(WeatherProvider):
    """
    Retrieves historical surface weather observations from NOAA ASOS station archives.
    Indexes observations by (airport_code, year, month, day, hour) for O(1) lookup.
    """

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or WEATHER_CSV_PATH
        self.lookup: Dict[Tuple[str, int, int, int, int], Dict[str, float]] = {}
        self.is_loaded = False
        self._load_data()

    def _load_data(self):
        if not self.csv_path.exists():
            logger.warning(f"Historical weather archive not found at {self.csv_path}")
            return

        try:
            df = pd.read_csv(self.csv_path)
            # Fill missing numericals with column median
            for col in ["temp", "dewp", "humid", "wind_speed", "wind_gust", "precip", "pressure", "visib"]:
                if col in df.columns:
                    df[col] = df[col].fillna(df[col].median())

            for _, row in df.iterrows():
                key = (
                    str(row["origin"]).upper().strip(),
                    int(row["year"]),
                    int(row["month"]),
                    int(row["day"]),
                    int(row["hour"]),
                )
                self.lookup[key] = {
                    "temp": float(row.get("temp", 55.0)),
                    "dewp": float(row.get("dewp", 40.0)),
                    "humid": float(row.get("humid", 60.0)),
                    "wind_speed": float(row.get("wind_speed", 8.0)),
                    "wind_gust": float(row.get("wind_gust", 0.0)),
                    "precip": float(row.get("precip", 0.0)),
                    "pressure": float(row.get("pressure", 1013.25)),
                    "visib": float(row.get("visib", 10.0)),
                }

            self.is_loaded = True
            logger.info(f"Loaded HistoricalWeatherProvider ({len(self.lookup):,} hourly station records).")
        except Exception as e:
            logger.error(f"Failed to load historical weather data: {e}")

    def get_weather(self, airport_code: str, target_time: datetime) -> Optional[WeatherObservation]:
        """Looks up historical weather record matching airport and timestamp."""
        if not self.is_loaded:
            return None

        # Convert to UTC
        if target_time.tzinfo is None:
            t = target_time.replace(tzinfo=timezone.utc)
        else:
            t = target_time.astimezone(timezone.utc)

        key = (airport_code.upper().strip(), t.year, t.month, t.day, t.hour)
        record = self.lookup.get(key)
        if not record:
            return None

        temp = record["temp"]
        dewp = record["dewp"]
        humid = record["humid"]
        wind_speed = record["wind_speed"]
        wind_gust = record["wind_gust"]
        precip = record["precip"]
        pressure = record["pressure"]
        visib = record["visib"]

        # Determine condition category
        if precip > 0.1 and temp <= 32:
            condition = "SNOW"
        elif precip > 0.1:
            condition = "RAIN"
        elif visib < 3.0:
            condition = "FOG"
        elif wind_speed >= 25.0:
            condition = "HIGH_WIND"
        elif humid > 85:
            condition = "OVERCAST"
        else:
            condition = "CLEAR"

        return WeatherObservation(
            airport_code=airport_code.upper().strip(),
            timestamp=t,
            temp_f=round(temp, 1),
            dewp_f=round(dewp, 1),
            humid_pct=round(humid, 1),
            wind_speed_mph=round(wind_speed, 1),
            wind_gust_mph=round(wind_gust, 1),
            precip_in=round(precip, 3),
            pressure_mb=round(pressure, 1),
            visib_miles=round(visib, 1),
            condition=condition,
            is_fog=bool(visib < 3.0),
            is_high_wind=bool(wind_speed >= 25.0 or wind_gust >= 30.0),
            is_freezing=bool(temp <= 32.0),
            has_precip=bool(precip > 0.0),
            source="NOAA_ASOS_HISTORICAL",
            is_fallback=False,
        )
