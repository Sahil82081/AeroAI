"""
Stage 5 Tests: Mock Supplier Ecosystem, Decoupled Interfaces, Adapters,
Inventory State, Cancellation/Refund Rules, and Failure/Latency Simulation.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.suppliers.interfaces import (
    FlightSupplierInterface,
    SupplierAdapterException
)
from app.modules.suppliers.service import SupplierIntegrationService, supplier_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock_suppliers():
    """Ensure clean inventory and simulation state before each test."""
    supplier_service.reset_simulation_state()
    yield
    supplier_service.reset_simulation_state()


def test_search_trains_delhi_to_jaipur_dataset():
    """Verify GET /trains/search returns TRN123 (Delhi -> Jaipur, price 800, 15 seats) labeled as MOCK API."""
    response = client.get("/trains/search", params={"origin": "Delhi", "destination": "Jaipur"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_mock_api"] is True
    assert data["simulated"] is True
    assert data["count"] >= 3

    trn123 = next((t for t in data["results"] if t["transport_id"] == "TRN123"), None)
    assert trn123 is not None
    assert trn123["origin"] == "Delhi"
    assert trn123["destination"] == "Jaipur"
    assert trn123["price"] == 800.0
    assert trn123["available_seats"] == 15
    assert "adapter_trace" in data
    assert data["adapter_trace"]["architecture_flow"] == "Agent -> SupplierServiceInterface -> SupplierAdapter -> MockSupplierAPI"


def test_search_flights_buses_and_hotels():
    """Verify GET /flights/search, /buses/search, and /hotels/search return realistic mock datasets."""
    flt_res = client.get("/flights/search", params={"origin": "Mumbai", "destination": "Delhi"})
    assert flt_res.status_code == 200
    assert flt_res.json()["count"] >= 2
    assert flt_res.json()["is_mock_api"] is True

    bus_res = client.get("/buses/search", params={"origin": "Delhi", "destination": "Jaipur"})
    assert bus_res.status_code == 200
    assert bus_res.json()["count"] >= 3
    assert bus_res.json()["results"][0]["supplier_type"] == "bus"

    htl_res = client.get("/hotels/search", params={"location": "Jaipur"})
    assert htl_res.status_code == 200
    assert htl_res.json()["count"] >= 2
    assert htl_res.json()["results"][0]["late_checkin_supported"] is True


def test_rebook_decrements_seat_inventory_and_enforces_availability():
    """Verify POST /bookings/rebook confirms booking, decrements available_seats, and rejects over-booking."""
    rebook_res = client.post(
        "/bookings/rebook",
        json={
            "original_booking_ref": "12015-SHT",
            "transport_id": "TRN123",
            "passenger_name": "Sahil Sharma",
            "seats": 3,
            "waive_change_fee": True
        }
    )
    assert rebook_res.status_code == 200
    conf = rebook_res.json()
    assert conf["status"] == "CONFIRMED"
    assert conf["transport_id"] == "TRN123"
    assert conf["confirmation_number"].startswith("MOCK-TRN-")
    assert conf["remaining_seats"] == 12  # 15 - 3 = 12
    assert conf["total_charged"] == 2400.0  # 800 * 3, 0 change fee
    assert conf["is_mock_api"] is True

    # Requesting 9 seats should succeed (12 - 9 = 3 left), then requesting 5 more should fail with 409
    res2 = client.post("/bookings/rebook", json={"transport_id": "TRN123", "seats": 9})
    assert res2.status_code == 200
    assert res2.json()["remaining_seats"] == 3

    res_fail = client.post("/bookings/rebook", json={"transport_id": "TRN123", "seats": 5})
    assert res_fail.status_code == 409
    assert res_fail.json()["detail"]["error_code"] == "INSUFFICIENT_SEATS"


def test_cancellation_and_refund_eligibility_rules():
    """Verify POST /bookings/cancel and POST /bookings/refund calculate waivers vs penalties accurately."""
    # 1. Refund with disruption waiver -> 100% full refund, 0 penalty
    waiver_refund = client.post(
        "/bookings/refund",
        json={
            "booking_reference": "6E-IND789",
            "transport_id": "FLT104",  # SAVER non-refundable tier normally
            "original_price": 3400.0,
            "currency": "INR",
            "reason": "UPSTREAM_FLIGHT_DELAY",
            "is_disruption_waiver": True
        }
    )
    assert waiver_refund.status_code == 200
    w_data = waiver_refund.json()
    assert w_data["refund_eligible"] is True
    assert w_data["penalty_deducted"] == 0.0
    assert w_data["refund_amount"] == 3400.0
    assert w_data["status"] == "REFUND_APPROVED"

    # 2. Voluntary refund on SAVER non-refundable tier (is_disruption_waiver=False) -> Tax-only refund
    saver_refund = client.post(
        "/bookings/refund",
        json={
            "booking_reference": "9I-831-VOL",
            "transport_id": "FLT104",
            "original_price": 3400.0,
            "currency": "INR",
            "reason": "VOLUNTARY_CHANGE",
            "is_disruption_waiver": False
        }
    )
    assert saver_refund.status_code == 200
    s_data = saver_refund.json()
    assert s_data["refund_eligible"] is False
    assert s_data["status"] == "PARTIAL_TAX_REFUND_ONLY"
    assert s_data["refund_amount"] < 500.0

    # 3. Cancel train booking
    cancel_res = client.post(
        "/bookings/cancel",
        json={
            "booking_reference": "PNR-245890",
            "transport_id": "TRN123",
            "supplier_type": "train",
            "reason": "DISRUPTION_CASCADE",
            "original_price": 800.0
        }
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


def test_hotel_modify_checkin():
    """Verify POST /hotel/modify updates check-in window and waives no-show penalty."""
    mod_res = client.post(
        "/hotel/modify",
        json={
            "booking_reference": "HTL-JAI-991",
            "hotel_id": "HTL101",
            "new_check_in": "2026-10-20T22:45:00",
            "late_arrival_notice": True,
            "notes": "Delayed due to flight UA-875 / train connection shift."
        }
    )
    assert mod_res.status_code == 200
    m_data = mod_res.json()
    assert m_data["status"] == "CHECKIN_MODIFIED_CONFIRMED"
    assert m_data["no_show_penalty_waived"] is True
    assert m_data["updated_check_in"] == "2026-10-20T22:45:00"
    assert m_data["is_mock_api"] is True


def test_simulated_failures_and_latency():
    """Verify mock suppliers simulate API latency and failure modes (503, 504, 409)."""
    # Test simulated latency
    lat_res = client.get("/trains/search", params={"origin": "Delhi", "simulate_latency_ms": 42})
    assert lat_res.status_code == 200
    assert lat_res.json()["simulated_latency_ms"] == 42.0

    # Test 504 Gateway Timeout simulation
    timeout_res = client.get("/flights/search", params={"simulate_failure": "timeout"})
    assert timeout_res.status_code == 504
    assert timeout_res.json()["detail"]["error_code"] == "MOCK_SUPPLIER_GATEWAY_TIMEOUT"

    # Test 503 Service Unavailable simulation
    unavail_res = client.post(
        "/bookings/rebook",
        json={"transport_id": "BUS101", "simulate_failure": "service_unavailable"}
    )
    assert unavail_res.status_code == 503
    assert unavail_res.json()["detail"]["error_code"] == "MOCK_SUPPLIER_SERVICE_UNAVAILABLE"


def test_decoupled_supplier_interface_injection():
    """
    Verify that SupplierIntegrationService depends strictly on Supplier Interfaces
    so a custom/real supplier adapter can replace the Mock Adapter without changing caller code.
    """
    class CustomProductionFlightAdapter(FlightSupplierInterface):
        def search_flights(self, origin=None, destination=None, earliest_departure=None, min_seats=1, simulate_failure=None, simulate_latency_ms=None):
            return {"supplier_service": "CustomRealAmadeusAdapter", "is_mock_api": False, "count": 1, "results": [{"transport_id": "REAL-999"}]}

        def rebook_flight(self, payload):
            return {"status": "CONFIRMED_REAL", "transport_id": payload["transport_id"]}

        def cancel_flight(self, payload):
            return {"status": "CANCELLED_REAL"}

        def request_refund(self, payload):
            return {"status": "REFUNDED_REAL"}

    custom_service = SupplierIntegrationService(flight_supplier=CustomProductionFlightAdapter())
    res = custom_service.search_flights(origin="Mumbai", destination="Delhi")
    assert res["supplier_service"] == "CustomRealAmadeusAdapter"
    assert res["is_mock_api"] is False
    assert res["results"][0]["transport_id"] == "REAL-999"
