"""
Supplier Service Layer (Facade for AI Agents and Backend Orchestrators).

Enforces the strict decoupling pattern:
    Agent
     ↓
    SupplierIntegrationService (Supplier Service Interface)
     ↓
    SupplierAdapter (MockFlightSupplierAdapter / MockTrainSupplierAdapter / etc.)
     ↓
    Mock Supplier REST API
"""
from typing import Dict, Any, Optional, List
from app.modules.suppliers.interfaces import (
    FlightSupplierInterface,
    TrainSupplierInterface,
    BusSupplierInterface,
    HotelSupplierInterface
)
from app.modules.suppliers.adapters import (
    BaseMockSupplierAdapter,
    MockFlightSupplierAdapter,
    MockTrainSupplierAdapter,
    MockBusSupplierAdapter,
    MockHotelSupplierAdapter
)


class SupplierIntegrationService:
    """
    High-level Supplier Service Interface injected into AI Recovery Agents and REST controllers.
    Accepts any concrete adapter implementing the Supplier Interfaces so Mock Supplier Adapters
    can be swapped for real GDS/CRS adapters without changing agent logic.
    """

    def __init__(
        self,
        flight_supplier: Optional[FlightSupplierInterface] = None,
        train_supplier: Optional[TrainSupplierInterface] = None,
        bus_supplier: Optional[BusSupplierInterface] = None,
        hotel_supplier: Optional[HotelSupplierInterface] = None
    ):
        self.flight_supplier = flight_supplier or MockFlightSupplierAdapter()
        self.train_supplier = train_supplier or MockTrainSupplierAdapter()
        self.bus_supplier = bus_supplier or MockBusSupplierAdapter()
        self.hotel_supplier = hotel_supplier or MockHotelSupplierAdapter()
        self._control_adapter = BaseMockSupplierAdapter()

    def search_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.flight_supplier.search_flights(
            origin=origin,
            destination=destination,
            earliest_departure=earliest_departure,
            min_seats=min_seats,
            simulate_failure=simulate_failure,
            simulate_latency_ms=simulate_latency_ms
        )

    def search_trains(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.train_supplier.search_trains(
            origin=origin,
            destination=destination,
            earliest_departure=earliest_departure,
            min_seats=min_seats,
            simulate_failure=simulate_failure,
            simulate_latency_ms=simulate_latency_ms
        )

    def search_buses(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.bus_supplier.search_buses(
            origin=origin,
            destination=destination,
            earliest_departure=earliest_departure,
            min_seats=min_seats,
            simulate_failure=simulate_failure,
            simulate_latency_ms=simulate_latency_ms
        )

    def search_hotels(
        self,
        location: Optional[str] = None,
        min_rooms: int = 1,
        late_checkin_only: bool = False,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.hotel_supplier.search_hotels(
            location=location,
            min_rooms=min_rooms,
            late_checkin_only=late_checkin_only,
            simulate_failure=simulate_failure,
            simulate_latency_ms=simulate_latency_ms
        )

    def search_multimodal_alternatives(
        self,
        origin: str,
        destination: str,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1
    ) -> Dict[str, Any]:
        """
        Queries Flight, Train, and Bus suppliers through their respective interfaces
        and aggregates normalized options for AI Agent / OR-Tools recovery evaluation.
        """
        flights_resp = self.search_flights(origin=origin, destination=destination, earliest_departure=earliest_departure, min_seats=min_seats)
        trains_resp = self.search_trains(origin=origin, destination=destination, earliest_departure=earliest_departure, min_seats=min_seats)
        buses_resp = self.search_buses(origin=origin, destination=destination, earliest_departure=earliest_departure, min_seats=min_seats)

        combined: List[Dict[str, Any]] = []
        combined.extend(flights_resp.get("normalized_options", []))
        combined.extend(trains_resp.get("normalized_options", []))
        combined.extend(buses_resp.get("normalized_options", []))

        return {
            "origin": origin,
            "destination": destination,
            "earliest_departure": earliest_departure,
            "total_alternatives": len(combined),
            "by_mode": {
                "flights": len(flights_resp.get("results", [])),
                "trains": len(trains_resp.get("results", [])),
                "buses": len(buses_resp.get("results", []))
            },
            "alternatives": combined,
            "is_mock_api": True,
            "simulated": True
        }

    def rebook_booking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Routes rebooking command through the appropriate supplier interface."""
        tid = str(payload.get("transport_id", "")).upper()
        if tid.startswith("TRN"):
            return self.train_supplier.rebook_train(payload)
        elif tid.startswith("BUS"):
            return self.bus_supplier.rebook_bus(payload)
        return self.flight_supplier.rebook_flight(payload)

    def cancel_booking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Routes cancellation command through the appropriate supplier interface."""
        stype = str(payload.get("supplier_type") or "").lower()
        tid = str(payload.get("transport_id") or "").upper()
        bref = str(payload.get("booking_reference") or "").upper()

        if stype == "train" or tid.startswith("TRN") or "TRN" in bref or "SHINKANSEN" in bref or "SHT" in bref:
            return self.train_supplier.cancel_train(payload)
        elif stype == "bus" or tid.startswith("BUS") or "BUS" in bref or "TIN" in bref:
            return self.bus_supplier.cancel_bus(payload)
        elif stype == "hotel" or tid.startswith("HTL") or "HYATT" in bref or "MARRIOTT" in bref or "HTL" in bref:
            return self.hotel_supplier.cancel_hotel(payload)
        return self.flight_supplier.cancel_flight(payload)

    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Routes refund evaluation/claim command through the appropriate supplier interface."""
        stype = str(payload.get("supplier_type") or "").lower()
        tid = str(payload.get("transport_id") or "").upper()
        bref = str(payload.get("booking_reference") or "").upper()

        if stype == "train" or tid.startswith("TRN") or "TRN" in bref or "SHINKANSEN" in bref or "SHT" in bref:
            return self.train_supplier.request_refund(payload)
        elif stype == "bus" or tid.startswith("BUS") or "BUS" in bref or "TIN" in bref:
            return self.bus_supplier.request_refund(payload)
        elif stype == "hotel" or tid.startswith("HTL") or "HYATT" in bref or "MARRIOTT" in bref or "HTL" in bref:
            return self.hotel_supplier.request_refund(payload)
        return self.flight_supplier.request_refund(payload)

    def modify_hotel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Routes hotel check-in modification through the HotelSupplierInterface."""
        return self.hotel_supplier.modify_reservation(payload)

    def get_simulation_config(self) -> Dict[str, Any]:
        return self._control_adapter._request("GET", "/simulation/config")

    def update_simulation_config(self, config_payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._control_adapter._request("POST", "/simulation/config", json_body=config_payload)

    def reset_simulation_state(self) -> Dict[str, Any]:
        return self._control_adapter._request("POST", "/simulation/reset")


supplier_service = SupplierIntegrationService()
