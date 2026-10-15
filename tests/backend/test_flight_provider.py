"""
Tests for AeroAI Stage 6: Flight Provider Abstraction & Intelligence.

Covers:
- MockFlightProvider (deterministic simulated status & inventory)
- RealFlightProvider (OpenSky Network & Aviationstack integrations)
- Real provider live ADS-B parsing (telemetry, velocity, altitude)
- Provider failure handling (HTTP 500, 429 rate limit)
- Missing API key graceful handling
- API timeout handling
- FlightService orchestration & seamless fallback hierarchy (auto, real, mock)
- Provenance enforcement: LIVE vs MOCK vs PREDICTED
- Prediction integration with ML FlightDelayPredictor & SHAP explainability
- FastAPI endpoints (/api/v1/flights/status, /prediction, /search, /provider-info)
"""

import pytest
import httpx
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.flights.interfaces import FlightStatusRecord, FlightPosition
from app.modules.flights.mock_provider import MockFlightProvider
from app.modules.flights.real_provider import RealFlightProvider
from app.modules.flights.service import FlightService

client = TestClient(app)


# =========================================================================
# 1. MOCK FLIGHT PROVIDER TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_mock_provider_benchmark_flight_ai202():
    """Verifies that MockFlightProvider returns deterministic AI202 delay status."""
    provider = MockFlightProvider()
    record = await provider.get_flight_status("AI202")

    assert record is not None
    assert record.flight_number == "AI202"
    assert record.carrier_code == "AI"
    assert record.origin == "BOM"
    assert record.destination == "DEL"
    assert record.status == "DELAYED"
    assert record.delay_minutes == 240
    assert record.data_source == "MOCK"
    assert record.provider_name == "Mock Flight Provider"
    assert record.is_fallback is False


@pytest.mark.asyncio
async def test_mock_provider_airborne_telemetry():
    """Verifies that MockFlightProvider provides coordinates for airborne flights."""
    provider = MockFlightProvider()
    record = await provider.get_flight_status("UK981")

    assert record is not None
    assert record.status == "AIRBORNE"
    assert record.position is not None
    assert record.position.altitude_ft > 30000.0
    assert record.position.velocity_kts > 400.0
    assert record.data_source == "MOCK"


@pytest.mark.asyncio
async def test_mock_provider_flight_search():
    """Verifies that MockFlightProvider returns inventory options with MOCK provenance."""
    provider = MockFlightProvider()
    results = await provider.search_flights(origin="DEL", destination="BOM", min_seats=2)

    assert len(results) > 0
    for item in results:
        assert item.origin == "DEL"
        assert item.destination == "BOM"
        assert item.available_seats >= 2
        assert item.data_source == "MOCK"
        assert item.provider_name == "Mock Flight Provider"


# =========================================================================
# 2. REAL FLIGHT PROVIDER TESTS (OPENSKY & AVIATIONSTACK)
# =========================================================================

def test_real_provider_callsign_normalization():
    """Verifies that commercial IATA flight numbers normalize to ICAO ATC callsigns."""
    provider = RealFlightProvider()
    assert provider._normalize_callsign("AI202") == "AIC202"
    assert provider._normalize_callsign("6E205") == "IGO205"
    assert provider._normalize_callsign("BA142") == "BAW142"
    assert provider._normalize_callsign("DL450") == "DAL450"


@pytest.mark.asyncio
async def test_real_provider_opensky_live_telemetry_parsing():
    """Tests that RealFlightProvider parses OpenSky ADS-B state vector into LIVE record."""
    # Simulated OpenSky API response for AIC202
    mock_opensky_payload = {
        "time": 1712345678,
        "states": [
            [
                "8003a2", "AIC202  ", "India", 1712345670, 1712345675,
                77.1000, 28.5500, 10668.0, False, 231.5,
                195.0, 1.5, None, 10800.0, None, False, 0
            ]
        ]
    }

    provider = RealFlightProvider(timeout_seconds=2.0)

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_opensky_payload
        mock_get.return_value = mock_resp

        record = await provider.get_flight_status("AI202")

        assert record is not None
        assert record.flight_number == "AI202"
        assert record.status == "AIRBORNE"
        assert record.data_source == "LIVE"
        assert record.provider_name == "OpenSky Network"
        assert record.is_fallback is False
        assert record.position is not None
        assert record.position.latitude == 28.5500
        assert record.position.longitude == 77.1000
        assert record.position.altitude_ft == 35000.0  # 10668m * 3.28084
        assert record.position.velocity_kts == 450.0   # 231.5 m/s * 1.94384


@pytest.mark.asyncio
async def test_real_provider_aviationstack_integration():
    """Tests Aviationstack API response parsing when API key is provided."""
    mock_aviationstack_payload = {
        "data": [
            {
                "flight_date": "2026-10-15",
                "flight_status": "active",
                "departure": {
                    "airport": "Indira Gandhi International",
                    "timezone": "Asia/Kolkata",
                    "iata": "DEL",
                    "delay": 20
                },
                "arrival": {
                    "airport": "Chhatrapati Shivaji",
                    "timezone": "Asia/Kolkata",
                    "iata": "BOM",
                    "delay": 15
                },
                "airline": {
                    "name": "Air India",
                    "iata": "AI"
                },
                "flight": {
                    "iata": "AI202",
                    "icao": "AIC202"
                },
                "live": {
                    "latitude": 24.1,
                    "longitude": 75.3,
                    "altitude": 10000.0,
                    "direction": 190.0,
                    "speed_horizontal": 850.0,
                    "is_ground": False
                }
            }
        ]
    }

    provider = RealFlightProvider(aviationstack_api_key="test-api-key")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_aviationstack_payload
        mock_get.return_value = mock_resp

        record = await provider.get_flight_status("AI202")

        assert record is not None
        assert record.data_source == "LIVE"
        assert record.provider_name == "Aviationstack"
        assert record.origin == "DEL"
        assert record.destination == "BOM"
        assert record.delay_minutes == 20


# =========================================================================
# 3. FAILURE, MISSING KEY, AND TIMEOUT TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_real_provider_rate_limit_429():
    """Verifies that HTTP 429 rate limiting returns None gracefully without unhandled exception."""
    provider = RealFlightProvider()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        record = await provider.get_flight_status("AI202")
        assert record is None


@pytest.mark.asyncio
async def test_real_provider_http_500_failure():
    """Verifies that HTTP 500 server error returns None gracefully."""
    provider = RealFlightProvider()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        record = await provider.get_flight_status("AI202")
        assert record is None


@pytest.mark.asyncio
async def test_real_provider_timeout_handling():
    """Verifies that API timeout returns None gracefully without crashing."""
    provider = RealFlightProvider(timeout_seconds=0.01)
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        record = await provider.get_flight_status("AI202")
        assert record is None


@pytest.mark.asyncio
async def test_missing_api_key_handling():
    """Verifies that missing Aviationstack API key falls back to OpenSky or returns None without crash."""
    provider = RealFlightProvider(aviationstack_api_key=None)
    with patch.object(provider, "_query_opensky_network", return_value=None):
        record = await provider.get_flight_status("AI202")
        assert record is None


# =========================================================================
# 4. FLIGHT SERVICE ORCHESTRATION & FALLBACK TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_service_auto_mode_fallback_when_live_fails():
    """Verifies that FlightService in 'auto' mode falls back to Mock provider when Real provider fails."""
    mock_p = MockFlightProvider()
    real_p = RealFlightProvider()

    # Simulate real provider failure
    with patch.object(real_p, "get_flight_status", return_value=None):
        service = FlightService(real_provider=real_p, mock_provider=mock_p, mode="auto")
        record = await service.get_flight_status("AI202")

        assert record is not None
        assert record.data_source == "MOCK"
        assert record.is_fallback is True
        assert "Fallback from Live Provider" in (record.notes or "")


@pytest.mark.asyncio
async def test_service_auto_mode_uses_live_when_available():
    """Verifies that FlightService in 'auto' mode returns LIVE data when real provider succeeds."""
    mock_p = MockFlightProvider()
    real_p = RealFlightProvider()

    dummy_live = FlightStatusRecord(
        flight_number="AI202",
        carrier_code="AI",
        carrier_name="Air India",
        origin="BOM",
        destination="DEL",
        status="AIRBORNE",
        data_source="LIVE",
        provider_name="OpenSky Network",
        is_fallback=False
    )

    with patch.object(real_p, "get_flight_status", return_value=dummy_live):
        service = FlightService(real_provider=real_p, mock_provider=mock_p, mode="auto")
        record = await service.get_flight_status("AI202")

        assert record.data_source == "LIVE"
        assert record.is_fallback is False
        assert record.provider_name == "OpenSky Network"


@pytest.mark.asyncio
async def test_service_flight_status_with_prediction_provenance():
    """Verifies that prediction endpoint returns status (MOCK/LIVE) and prediction (PREDICTED)."""
    service = FlightService(mode="mock")
    payload = await service.get_flight_status_with_prediction("AI202")

    assert payload["flight_number"] == "AI202"
    assert payload["status_data_source"] == "MOCK"
    assert "prediction" in payload
    assert payload["prediction"]["data_source"] == "PREDICTED"
    assert "delay_probability" in payload["prediction"]
    assert "explanation" in payload["prediction"]


# =========================================================================
# 5. FASTAPI ENDPOINT TESTS
# =========================================================================

def test_api_flight_status_endpoint():
    """Tests GET /api/v1/flights/status/{flight_number}."""
    resp = client.get("/api/v1/flights/status/AI202")
    assert resp.status_code == 200
    data = resp.json()
    assert data["flight_number"] == "AI202"
    assert data["data_source"] in ["LIVE", "MOCK"]


def test_api_flight_status_prediction_endpoint():
    """Tests GET /api/v1/flights/status/{flight_number}/prediction."""
    resp = client.get("/api/v1/flights/status/AI202/prediction")
    assert resp.status_code == 200
    data = resp.json()
    assert "prediction" in data
    assert data["prediction"]["data_source"] == "PREDICTED"


def test_api_flight_search_endpoint():
    """Tests GET /api/v1/flights/inventory."""
    resp = client.get("/api/v1/flights/inventory?origin=DEL&destination=BOM&min_seats=1")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert results[0]["data_source"] in ["LIVE", "MOCK"]


def test_api_flight_provider_info_endpoint():
    """Tests GET /api/v1/flights/provider-info."""
    resp = client.get("/api/v1/flights/provider-info")
    assert resp.status_code == 200
    info = resp.json()
    assert "mode" in info
    assert "real_provider" in info
    assert "mock_provider" in info
    assert "provenance_contract" in info
