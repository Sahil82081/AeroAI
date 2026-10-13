"""
Supplier Adapters Layer.
Implements the Supplier Service Interfaces by communicating with the Mock Supplier REST APIs
over HTTP/ASGI and normalizing responses into standard domain structures.

Architecture:
    Agent
     ↓
    Supplier Service Interface (interfaces.py / service.py)
     ↓
    Supplier Adapter (THIS MODULE)
     ↓
    Mock Supplier API (mock-suppliers/ FastAPI services)
"""
import os
import sys
from typing import Dict, Any, Optional, List
from fastapi.testclient import TestClient

from app.core.logger import logger
from app.modules.suppliers.interfaces import (
    FlightSupplierInterface,
    TrainSupplierInterface,
    BusSupplierInterface,
    HotelSupplierInterface,
    NormalizedTransportOption,
    NormalizedHotelOption,
    SupplierAdapterException
)

# Add mock-suppliers directory to sys.path so the ASGI gateway can be loaded cleanly
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
_MOCK_SUPPLIERS_DIR = os.path.join(_REPO_ROOT, "mock-suppliers")
if _MOCK_SUPPLIERS_DIR not in sys.path:
    sys.path.insert(0, _MOCK_SUPPLIERS_DIR)

from gateway import mock_supplier_app  # noqa: E402


class BaseMockSupplierAdapter:
    """
    Base HTTP/ASGI Adapter communicating with the Mock Supplier REST API ecosystem.
    Translates HTTP status codes (404, 409, 503, 504) into domain SupplierAdapterException.
    """
    _client: Optional[TestClient] = None

    @classmethod
    def get_http_client(cls) -> TestClient:
        if cls._client is None:
            cls._client = TestClient(mock_supplier_app, raise_server_exceptions=False)
        return cls._client

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        client = self.get_http_client()
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        logger.info(f"[SupplierAdapter] -> {method} {path} params={clean_params}")
        response = client.request(method, path, params=clean_params, json=json_body)

        if response.status_code >= 400:
            try:
                err_payload = response.json()
                detail = err_payload.get("detail", err_payload)
            except Exception:
                detail = {"message": response.text}

            if isinstance(detail, dict):
                msg = detail.get("message", f"Supplier API error ({response.status_code})")
                err_code = detail.get("error_code", f"HTTP_{response.status_code}")
            else:
                msg = str(detail)
                err_code = f"HTTP_{response.status_code}"

            logger.warning(f"[SupplierAdapter] <- Error {response.status_code} ({err_code}): {msg}")
            raise SupplierAdapterException(
                message=msg,
                status_code=response.status_code,
                error_code=err_code,
                details=detail if isinstance(detail, dict) else {"raw": detail}
            )

        data = response.json()
        if isinstance(data, dict):
            data["adapter_trace"] = {
                "architecture_flow": "Agent -> SupplierServiceInterface -> SupplierAdapter -> MockSupplierAPI",
                "adapter_class": self.__class__.__name__,
                "mock_api_endpoint": f"{method} {path}",
                "http_status": response.status_code,
                "is_mock_api": True,
                "simulated": True
            }
        return data


class MockFlightSupplierAdapter(BaseMockSupplierAdapter, FlightSupplierInterface):
    """Concrete Adapter for the Mock Flight Supplier GDS REST API."""

    def search_flights(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        raw = self._request(
            "GET",
            "/flights/search",
            params={
                "origin": origin,
                "destination": destination,
                "earliest_departure": earliest_departure,
                "min_seats": min_seats,
                "simulate_failure": simulate_failure,
                "simulate_latency_ms": simulate_latency_ms
            }
        )
        normalized: List[Dict[str, Any]] = []
        for item in raw.get("results", []):
            opt = NormalizedTransportOption(
                transport_id=item["transport_id"],
                supplier_type="flight",
                provider=item["provider"],
                vehicle_number=item.get("flight_number", item["transport_id"]),
                origin=item["origin"],
                destination=item["destination"],
                departure=item["departure"],
                arrival=item["arrival"],
                duration_minutes=item.get("duration_minutes", 120),
                price=item["price"],
                currency=item.get("currency", "INR"),
                available_seats=item["available_seats"],
                service_class=item.get("cabin_class", "ECONOMY"),
                cancellation_rules=item.get("cancellation_rules", {}),
                refund_eligibility=item.get("refund_eligibility", True),
                simulated_latency_ms=raw.get("simulated_latency_ms", 0.0),
                is_mock_api=True,
                simulated=True
            )
            normalized.append(opt.model_dump())

        raw["normalized_options"] = normalized
        return raw

    def rebook_flight(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/flights/rebook", json_body=payload)

    def cancel_flight(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/flights/cancel", json_body=payload)

    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/flights/refund", json_body=payload)


class MockTrainSupplierAdapter(BaseMockSupplierAdapter, TrainSupplierInterface):
    """Concrete Adapter for the Mock Train Supplier CRS REST API."""

    def search_trains(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        raw = self._request(
            "GET",
            "/trains/search",
            params={
                "origin": origin,
                "destination": destination,
                "earliest_departure": earliest_departure,
                "min_seats": min_seats,
                "simulate_failure": simulate_failure,
                "simulate_latency_ms": simulate_latency_ms
            }
        )
        normalized: List[Dict[str, Any]] = []
        for item in raw.get("results", []):
            opt = NormalizedTransportOption(
                transport_id=item["transport_id"],
                supplier_type="train",
                provider=item["provider"],
                vehicle_number=item.get("train_number", item["transport_id"]),
                origin=item["origin"],
                destination=item["destination"],
                departure=item["departure"],
                arrival=item["arrival"],
                duration_minutes=item.get("duration_minutes", 240),
                price=item["price"],
                currency=item.get("currency", "INR"),
                available_seats=item["available_seats"],
                service_class=item.get("coach_class", "AC_CHAIR_CAR"),
                cancellation_rules=item.get("cancellation_rules", {}),
                refund_eligibility=item.get("refund_eligibility", True),
                simulated_latency_ms=raw.get("simulated_latency_ms", 0.0),
                is_mock_api=True,
                simulated=True
            )
            normalized.append(opt.model_dump())

        raw["normalized_options"] = normalized
        return raw

    def rebook_train(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/trains/rebook", json_body=payload)

    def cancel_train(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/trains/cancel", json_body=payload)

    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/trains/refund", json_body=payload)


class MockBusSupplierAdapter(BaseMockSupplierAdapter, BusSupplierInterface):
    """Concrete Adapter for the Mock Bus Supplier REST API."""

    def search_buses(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        earliest_departure: Optional[str] = None,
        min_seats: int = 1,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        raw = self._request(
            "GET",
            "/buses/search",
            params={
                "origin": origin,
                "destination": destination,
                "earliest_departure": earliest_departure,
                "min_seats": min_seats,
                "simulate_failure": simulate_failure,
                "simulate_latency_ms": simulate_latency_ms
            }
        )
        normalized: List[Dict[str, Any]] = []
        for item in raw.get("results", []):
            opt = NormalizedTransportOption(
                transport_id=item["transport_id"],
                supplier_type="bus",
                provider=item["provider"],
                vehicle_number=item.get("bus_number", item["transport_id"]),
                origin=item["origin"],
                destination=item["destination"],
                departure=item["departure"],
                arrival=item["arrival"],
                duration_minutes=item.get("duration_minutes", 300),
                price=item["price"],
                currency=item.get("currency", "INR"),
                available_seats=item["available_seats"],
                service_class=item.get("bus_type", "AC_SLEEPER"),
                cancellation_rules=item.get("cancellation_rules", {}),
                refund_eligibility=item.get("refund_eligibility", True),
                simulated_latency_ms=raw.get("simulated_latency_ms", 0.0),
                is_mock_api=True,
                simulated=True
            )
            normalized.append(opt.model_dump())

        raw["normalized_options"] = normalized
        return raw

    def rebook_bus(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/buses/rebook", json_body=payload)

    def cancel_bus(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/buses/cancel", json_body=payload)

    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/buses/refund", json_body=payload)


class MockHotelSupplierAdapter(BaseMockSupplierAdapter, HotelSupplierInterface):
    """Concrete Adapter for the Mock Hotel Supplier CRS REST API."""

    def search_hotels(
        self,
        location: Optional[str] = None,
        min_rooms: int = 1,
        late_checkin_only: bool = False,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        raw = self._request(
            "GET",
            "/hotels/search",
            params={
                "location": location,
                "min_rooms": min_rooms,
                "late_checkin_only": late_checkin_only,
                "simulate_failure": simulate_failure,
                "simulate_latency_ms": simulate_latency_ms
            }
        )
        normalized: List[Dict[str, Any]] = []
        for item in raw.get("results", []):
            opt = NormalizedHotelOption(
                hotel_id=item["hotel_id"],
                supplier_type="hotel",
                provider=item["provider"],
                hotel_name=item["hotel_name"],
                location=item["location"],
                address=item.get("address", item["location"]),
                check_in_window=item.get("check_in_window", "14:00 - 23:59"),
                price_per_night=item.get("price_per_night", item.get("price", 5000.0)),
                currency=item.get("currency", "INR"),
                available_rooms=item["available_rooms"],
                room_type=item.get("room_type", "Deluxe Room"),
                late_checkin_supported=item.get("late_checkin_supported", True),
                cancellation_rules=item.get("cancellation_rules", {}),
                refund_eligibility=item.get("refund_eligibility", True),
                simulated_latency_ms=raw.get("simulated_latency_ms", 0.0),
                is_mock_api=True,
                simulated=True
            )
            normalized.append(opt.model_dump())

        raw["normalized_options"] = normalized
        return raw

    def modify_reservation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/hotel/modify", json_body=payload)

    def cancel_hotel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/hotels/cancel", json_body=payload)

    def request_refund(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/hotels/refund", json_body=payload)
