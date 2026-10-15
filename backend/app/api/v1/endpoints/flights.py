"""
Flight Status & Inventory API Endpoints for AeroAI.

Exposes endpoints for querying live/mock flight telemetry, ML delay prediction,
and alternative flight inventory with strict provenance labels (LIVE, MOCK, PREDICTED).
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.modules.flights.service import flight_service
from app.modules.flights.interfaces import FlightStatusRecord, FlightInventoryItem

router = APIRouter(prefix="/flights", tags=["Flight Intelligence & Status"])


@router.get("/status/{flight_number}", response_model=FlightStatusRecord, summary="Get Flight Operational Status")
async def get_flight_status_endpoint(
    flight_number: str = Path(..., description="Commercial flight number (e.g. AI202, 6E205, BA142)"),
    date: Optional[str] = Query(None, description="Optional flight departure date (YYYY-MM-DD)")
):
    """
    Retrieves operational status, delay information, and live coordinates for a flight.
    Uses OpenSky Network / Aviationstack when available, cleanly falling back to Mock GDS.
    Information is explicitly labeled with data_source (LIVE or MOCK).
    """
    try:
        record = await flight_service.get_flight_status(flight_number, target_date=date)
        return record
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Flight status lookup failed: {str(e)}")


@router.get("/status/{flight_number}/prediction", summary="Get Flight Status with ML Delay Prediction")
async def get_flight_status_prediction_endpoint(
    flight_number: str = Path(..., description="Commercial flight number (e.g. AI202, 6E205)"),
    date: Optional[str] = Query(None, description="Optional flight departure date (YYYY-MM-DD)")
):
    """
    Combines live/mock flight telemetry with Stage 4 Random Forest delay predictions
    and SHAP explainability. Explicitly labels prediction with data_source='PREDICTED'.
    """
    try:
        payload = await flight_service.get_flight_status_with_prediction(flight_number, target_date=date)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight prediction calculation failed: {str(e)}")


@router.get("/inventory", response_model=List[FlightInventoryItem], summary="Search Alternative Flight Inventory")
@router.get("/search", response_model=List[FlightInventoryItem], summary="Search Alternative Flights")
async def search_flights_endpoint(
    origin: str = Query(..., description="Three-letter departure airport code (e.g. DEL, BOM, JFK)"),
    destination: str = Query(..., description="Three-letter destination airport code (e.g. BOM, JAI, LHR)"),
    min_seats: int = Query(1, ge=1, description="Minimum available seats required")
):
    """
    Searches available flights between origin and destination with seat inventory.
    """
    try:
        results = await flight_service.search_flights(
            origin=origin,
            destination=destination,
            min_seats=min_seats
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")


@router.get("/provider-info", summary="Get Flight Provider Configuration")
def get_provider_info_endpoint():
    """
    Returns diagnostics on active aviation providers, credentials status, and fallback mode.
    """
    return flight_service.get_provider_info()
