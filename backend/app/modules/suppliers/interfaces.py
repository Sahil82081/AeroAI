"""
Supplier Service Interfaces (Port Definitions).
Decouples AI Agents and Recovery Orchestrators from concrete supplier API implementations.

Architecture:
    Agent / Recovery Engine
        ↓
    Supplier Service Interface (defined here)
        ↓
    Supplier Adapter (e.g. MockFlightSupplierAdapter, or future AmadeusAdapter)
        ↓
    External / Mock Supplier REST API
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SupplierAdapterException(Exception):
    """Domain exception raised by Supplier Adapters when a supplier API fails or times out."""
    def __init__(self, message: str, status_code: int = 502, error_code: str = "SUPPLIER_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class NormalizedTransportOption(BaseModel):
    """Normalized transport alternative returned to Agents regardless of underlying supplier."""
    transport_id: str
    supplier_type: str  # flight, train, bus
    provider: str
    vehicle_number: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration_minutes: int
    price: float
    currency: str = "INR"
    available_seats: int
    service_class: str = "STANDARD"
    cancellation_rules: Dict[str, Any] = Field(default_factory=dict)
    refund_eligibility: bool = True
    simulated_latency_ms: float = 0.0
    is_mock_api: bool = True
    simulated: bool = True


class NormalizedHotelOption(BaseModel):
    """Normalized hotel option returned to Agents regardless of underlying hospitality CRS."""
    hotel_id: str
    supplier_type: str = "hotel"
    provider: str
    hotel_name: str
    location: str
    address: str
    check_in_window: str
    price_per_night: float
    currency: str = "INR"
    available_rooms: int
    room_type: str
    late_checkin_supported: bool = True
    cancellation_rules: Dict[str, Any] = Field(default_factory=dict)
    refund_eligibility: bool = True
    simulated_latency_ms: float = 0.0
    is_mock_api: bool = True
    simulated: bool = True


class FlightSupplierInterface(ABC):
    """Abstract interface for Flight Supplier operations."""

    @abstractmethod
    def search_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def rebook_flight(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_flight(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass


class TrainSupplierInterface(ABC):
    """Abstract interface for Train Supplier operations."""

    @abstractmethod
    def search_trains(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def rebook_train(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_train(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass


class BusSupplierInterface(ABC):
    """Abstract interface for Bus Supplier operations."""

    @abstractmethod
    def search_buses(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def rebook_bus(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_bus(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass


class HotelSupplierInterface(ABC):
    """Abstract interface for Hotel Supplier operations."""

    @abstractmethod
    def search_hotels(
        self,
        location: Optional[str] = None,
        min_rooms: int = 1,
        late_checkin_only: bool = False,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def modify_reservation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_hotel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
