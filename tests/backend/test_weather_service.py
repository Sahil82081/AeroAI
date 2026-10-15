"""
Unit & Integration Tests for Stage 3: Weather Intelligence.
Verifies weather provider abstractions, historical NOAA retrieval, live Open-Meteo fetching,
mock fallbacks, feature pipeline integration, zero-crash missing weather handling,
and weather REST endpoints.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.modules.weather.interfaces import WeatherObservation
from app.modules.weather.historical_provider import HistoricalWeatherProvider
from app.modules.weather.live_provider import LiveWeatherProvider, AIRPORT_COORDINATES
from app.modules.weather.mock_provider import MockWeatherProvider
from app.modules.weather.service import WeatherService, weather_service
from app.ml.feature_pipeline import FlightFeatureTransformer
from app.ml.predictor import FlightDelayPredictor

client = TestClient(app)


def test_historical_weather_provider_retrieval():
    """Verifies that HistoricalWeatherProvider accurately queries NOAA/ASOS records by airport & hour."""
    provider = HistoricalWeatherProvider()
    assert provider.is_loaded, "Historical weather provider failed to load archive"

    # Query Jan 1, 2013 at 06:00 UTC at EWR
    t = datetime(2013, 1, 1, 6, 0, tzinfo=timezone.utc)
    obs = provider.get_weather("EWR", t)

    assert obs is not None, "Failed to retrieve historical observation for EWR 2013-01-01 06:00"
    assert obs.airport_code == "EWR"
    assert obs.source == "NOAA_ASOS_HISTORICAL"
    assert obs.is_fallback is False
    assert 20.0 <= obs.temp_f <= 60.0
    assert obs.pressure_mb > 950.0

    # Non-existent airport returns None
    missing = provider.get_weather("NON_EXISTENT", t)
    assert missing is None


def test_mock_weather_provider_scenarios():
    """Verifies deterministic fallback weather scenarios."""
    provider = MockWeatherProvider()

    # Clear
    clear_obs = provider.get_weather("EWR", preset="CLEAR")
    assert clear_obs.is_fallback is True
    assert clear_obs.is_fog is False
    assert clear_obs.condition == "CLEAR"

    # Fog
    fog_obs = provider.get_weather("JFK", preset="FOG")
    assert fog_obs.is_fog is True
    assert fog_obs.visib_miles < 3.0
    assert fog_obs.condition == "FOG"

    # Thunderstorm
    storm_obs = provider.get_weather("ORD", preset="THUNDERSTORM")
    assert storm_obs.is_high_wind is True
    assert storm_obs.has_precip is True
    assert storm_obs.wind_speed_mph >= 25.0


def test_live_weather_supported_airports():
    """Verifies airport coordinate registry covers key US and Indian hubs."""
    expected_airports = ["EWR", "JFK", "LGA", "ORD", "LAX", "BOM", "DEL"]
    for code in expected_airports:
        assert code in AIRPORT_COORDINATES
        assert "lat" in AIRPORT_COORDINATES[code]
        assert "lon" in AIRPORT_COORDINATES[code]


def test_weather_service_fallback_orchestration():
    """Verifies that WeatherService automatically routes and guarantees fallback without crashing."""
    service = weather_service

    # Historical query routes to NOAA
    t_hist = datetime(2013, 5, 10, 14, 0, tzinfo=timezone.utc)
    obs_hist = service.get_weather("JFK", t_hist)
    assert obs_hist is not None
    assert obs_hist.airport_code == "JFK"

    # Unknown airport gracefully falls back to Mock without throwing an exception
    obs_fallback = service.get_weather("XYZ_UNKNOWN")
    assert obs_fallback is not None
    assert obs_fallback.is_fallback is True

    # Feature extraction for flight
    features, obs_flight, available = service.get_weather_features_for_flight("EWR", t_hist)
    assert isinstance(features, dict)
    assert "temp" in features
    assert "wind_speed" in features
    assert "visib" in features
    assert "is_fog" in features


def test_feature_pipeline_missing_weather_graceful_handling():
    """Verifies FlightFeatureTransformer handles missing weather without errors."""
    import pandas as pd

    # Flight without ANY weather columns
    df_no_weather = pd.DataFrame([{
        "year": 2013, "month": 5, "day": 12, "carrier": "UA", "origin": "EWR", "dest": "ORD",
        "sched_dep_hour": 15, "sched_dep_min": 30, "distance": 719.0, "sched_elapsed_min": 140.0
    }])

    transformer = FlightFeatureTransformer()
    # Fit with minimal mock target
    transformer.fit(df_no_weather, pd.Series([0]))

    # Transform without weather
    X_proc = transformer.transform(df_no_weather)
    assert X_proc.shape[0] == 1
    assert not pd.isna(X_proc).any(), "NaN values detected when transforming missing weather"


def test_flight_delay_predictor_weather_impact():
    """Verifies that adverse weather (e.g. dense fog) increases predicted delay risk."""
    predictor = FlightDelayPredictor()
    assert predictor.is_loaded

    # Prediction in clear weather
    clear_weather = {
        "temp": 68.0, "dewp": 45.0, "humid": 45.0, "wind_speed": 6.0,
        "precip": 0.0, "pressure": 1016.0, "visib": 10.0,
        "is_fog": 0.0, "is_high_wind": 0.0, "is_freezing": 0.0, "has_precip": 0.0
    }
    res_clear = predictor.predict(
        carrier="UA", origin="EWR", dest="ORD",
        scheduled_departure="2026-10-20T18:00:00Z",
        weather_override=clear_weather
    )

    # Prediction in severe fog + freezing rain
    severe_weather = {
        "temp": 30.0, "dewp": 29.0, "humid": 98.0, "wind_speed": 28.0,
        "precip": 0.35, "pressure": 998.0, "visib": 0.8,
        "is_fog": 1.0, "is_high_wind": 1.0, "is_freezing": 1.0, "has_precip": 1.0
    }
    res_severe = predictor.predict(
        carrier="UA", origin="EWR", dest="ORD",
        scheduled_departure="2026-10-20T18:00:00Z",
        weather_override=severe_weather
    )

    prob_clear = res_clear["delay_probability"]
    prob_severe = res_severe["delay_probability"]

    assert prob_severe > prob_clear, f"Adverse weather probability ({prob_severe}) should exceed clear ({prob_clear})"
    assert res_clear["weather_intelligence"]["weather_available"] is True
    assert res_severe["weather_intelligence"]["is_fog"] is True


def test_weather_api_observation_endpoint():
    """Tests GET /api/v1/weather/observation endpoint."""
    res = client.get("/api/v1/weather/observation?airport=JFK&force_provider=mock")
    assert res.status_code == 200

    data = res.json()
    assert data["airport_code"] == "JFK"
    assert "temp_f" in data
    assert "wind_speed_mph" in data
    assert "visib_miles" in data
    assert "condition" in data


def test_weather_api_supported_airports_endpoint():
    """Tests GET /api/v1/weather/supported-airports endpoint."""
    res = client.get("/api/v1/weather/supported-airports")
    assert res.status_code == 200

    data = res.json()
    assert data["count"] > 0
    assert "EWR" in data["airports"]
    assert "BOM" in data["airports"]


def test_predict_endpoint_returns_weather_intelligence():
    """Tests POST /api/v1/predict/flight-delay exposes weather context."""
    payload = {
        "carrier": "UA",
        "origin": "EWR",
        "dest": "BOS",
        "scheduled_departure": "2026-10-20T14:30:00Z",
    }
    res = client.post("/api/v1/predict/flight-delay", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert "weather_intelligence" in data
    weather_info = data["weather_intelligence"]
    assert "temp_f" in weather_info
    assert "condition" in weather_info
    assert "weather_available" in weather_info
