"""
AeroAI Flight Intelligence Module.

Provides abstract flight tracking interfaces, real-world aviation API integrations
(OpenSky Network, Aviationstack), deterministic mock fallbacks, and prediction tracking.
"""

from app.modules.flights.interfaces import (
    FlightProvider,
    FlightStatusRecord,
    FlightInventoryItem,
    FlightPosition,
    DataSourceType,
    FlightStatusType
)
from app.modules.flights.mock_provider import MockFlightProvider
from app.modules.flights.real_provider import RealFlightProvider, FlightProviderError
from app.modules.flights.service import FlightService, flight_service

__all__ = [
    "FlightProvider",
    "FlightStatusRecord",
    "FlightInventoryItem",
    "FlightPosition",
    "DataSourceType",
    "FlightStatusType",
    "MockFlightProvider",
    "RealFlightProvider",
    "FlightProviderError",
    "FlightService",
    "flight_service"
]
