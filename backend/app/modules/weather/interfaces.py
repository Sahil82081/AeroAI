"""
Weather Provider Interfaces & Domain Schemas for AeroAI.
Defines abstract contracts for weather retrieval and meteorological observations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class WeatherObservation(BaseModel):
    """Normalized meteorological observation for aviation risk intelligence."""

    airport_code: str = Field(..., description="Three-letter IATA airport code (e.g. EWR, JFK, LGA, BOM, DEL)")
    timestamp: datetime = Field(..., description="Timestamp of meteorological observation in UTC")
    temp_f: float = Field(..., description="Ambient temperature in Fahrenheit")
    dewp_f: float = Field(..., description="Dew point temperature in Fahrenheit")
    humid_pct: float = Field(..., description="Relative humidity percentage (0-100)")
    wind_speed_mph: float = Field(..., description="Surface wind speed in statute miles per hour")
    wind_gust_mph: float = Field(0.0, description="Peak wind gust speed in miles per hour")
    precip_in: float = Field(0.0, description="Precipitation accumulation in inches")
    pressure_mb: float = Field(..., description="Sea level barometric pressure in millibars (hPa)")
    visib_miles: float = Field(..., description="Surface horizontal visibility in statute miles")
    condition: str = Field("CLEAR", description="High-level meteorological condition category")

    # Severe operational indicators (FAA IFR / ground de-icing thresholds)
    is_fog: bool = Field(False, description="Horizontal visibility < 3 statute miles (FAA Instrument Flight Rules)")
    is_high_wind: bool = Field(False, description="Sustained wind >= 25 mph or gusts >= 30 mph")
    is_freezing: bool = Field(False, description="Temperature <= 32 deg F (ground de-icing delays)")
    has_precip: bool = Field(False, description="Measurable liquid or frozen precipitation > 0.0 in")

    # Provenance
    source: str = Field(..., description="Data provider provenance (e.g. NOAA_ASOS_HISTORICAL, OPEN_METEO_LIVE, MOCK_FALLBACK)")
    is_fallback: bool = Field(False, description="Whether observation was generated via fallback due to provider unavailability")

    def to_model_features(self) -> Dict[str, float]:
        """Converts observation into standardized numeric features for the ML pipeline."""
        return {
            "temp": float(self.temp_f),
            "dewp": float(self.dewp_f),
            "humid": float(self.humid_pct),
            "wind_speed": float(self.wind_speed_mph),
            "precip": float(self.precip_in),
            "pressure": float(self.pressure_mb),
            "visib": float(self.visib_miles),
            "is_fog": 1.0 if self.is_fog else 0.0,
            "is_high_wind": 1.0 if self.is_high_wind else 0.0,
            "is_freezing": 1.0 if self.is_freezing else 0.0,
            "has_precip": 1.0 if self.has_precip else 0.0,
        }


class WeatherProvider(ABC):
    """Abstract interface for weather intelligence providers."""

    @abstractmethod
    def get_weather(self, airport_code: str, target_time: datetime) -> Optional[WeatherObservation]:
        """Retrieves meteorological observation for a given airport and time."""
        pass
