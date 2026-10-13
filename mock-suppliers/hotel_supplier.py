"""
MOCK HOTEL SUPPLIER SERVICE (Simulated Hospitality CRS / Property Management API).
Exposes REST APIs for hotel search, check-in modification, cancellation, and refund calculation.
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, APIRouter, Query

from common import (
    MOCK_DISCLAIMER,
    SimulationEngine,
    CancelRequestPayload,
    RefundRequestPayload,
    HotelModifyRequestPayload,
    evaluate_cancellation_and_refund
)
from datasets import MockSupplierDataStore, matches_location

hotel_router = APIRouter(tags=["Mock Hotel Supplier API"])


@hotel_router.get("/hotels/search")
def search_hotels(
    location: Optional[str] = Query(default=None, description="City or location (e.g. Jaipur, Delhi, Mumbai, Tokyo)"),
    min_rooms: int = Query(default=1, ge=1),
    late_checkin_only: bool = Query(default=False),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """
    [MOCK API] Search available hotel properties and rooms across simulated hospitality CRS.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockHotelSupplierCRS",
        endpoint="GET /hotels/search",
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )

    results = []
    for item in MockSupplierDataStore.hotels:
        if location and not matches_location(item["location"], item.get("city", ""), location):
            continue
        if item["available_rooms"] < min_rooms:
            continue
        if late_checkin_only and not item.get("late_checkin_supported", True):
            continue
        results.append(item)

    return {
        "supplier_service": "MockHotelSupplierCRS",
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "simulated_latency_ms": latency_ms,
        "count": len(results),
        "results": results
    }


@hotel_router.post("/hotel/modify")
@hotel_router.post("/hotels/modify")
def modify_hotel_reservation(payload: HotelModifyRequestPayload):
    """
    [MOCK API] Modify hotel check-in time / date or register late arrival protection
    so the traveler's room is not released as a no-show during transit disruptions.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockHotelSupplierCRS",
        endpoint="POST /hotel/modify",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    hotel = MockSupplierDataStore.find_hotel(payload.hotel_id) if payload.hotel_id else MockSupplierDataStore.hotels[0]
    if not hotel:
        hotel = MockSupplierDataStore.hotels[0]

    mod_fee = hotel["cancellation_rules"].get("late_checkin_modification_fee", 0.0)
    mod_ref = f"MOD-HTL-{uuid.uuid4().hex[:6].upper()}"

    response = {
        "modification_id": mod_ref,
        "booking_reference": payload.booking_reference,
        "hotel_id": hotel["hotel_id"],
        "supplier_type": "hotel",
        "hotel_name": hotel["hotel_name"],
        "location": hotel["location"],
        "status": "CHECKIN_MODIFIED_CONFIRMED",
        "updated_check_in": payload.new_check_in,
        "updated_check_out": payload.new_check_out,
        "late_arrival_guaranteed": payload.late_arrival_notice,
        "no_show_penalty_waived": True,
        "modification_fee": mod_fee,
        "currency": hotel["currency"],
        "front_desk_notes": payload.notes,
        "modified_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }
    MockSupplierDataStore.booking_ledger[mod_ref] = response
    return response


@hotel_router.post("/hotels/cancel")
def cancel_hotel_booking(payload: CancelRequestPayload):
    """
    [MOCK API] Cancel a hotel reservation and evaluate property cancellation policy.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockHotelSupplierCRS",
        endpoint="POST /hotels/cancel",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    hotel = MockSupplierDataStore.find_hotel(payload.transport_id) if payload.transport_id else MockSupplierDataStore.hotels[0]
    if hotel and payload.transport_id:
        hotel["available_rooms"] += 1

    rules = hotel["cancellation_rules"] if hotel else {"fare_tier": "FLEXIBLE", "refundable": True, "penalty_pct": 20.0, "cancellation_fee": 1000.0}
    price = payload.original_price if payload.original_price is not None else (hotel["price"] if hotel else 5400.0)
    currency = hotel["currency"] if hotel else "INR"

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=price,
        currency=currency,
        cancellation_rules=rules,
        is_disruption_waiver=("DISRUPTION" in payload.reason.upper()),
        reason=payload.reason
    )

    return {
        "cancellation_id": f"CAN-HTL-{uuid.uuid4().hex[:6].upper()}",
        "booking_reference": payload.booking_reference,
        "supplier_type": "hotel",
        "status": "CANCELLED",
        "cancelled_at": datetime.utcnow().isoformat(),
        "cancellation_evaluation": eval_result,
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


@hotel_router.post("/hotels/refund")
def refund_hotel_booking(payload: RefundRequestPayload):
    """
    [MOCK API] Process a hotel reservation refund based on property policy and disruption waiver.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockHotelSupplierCRS",
        endpoint="POST /hotels/refund",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    hotel = MockSupplierDataStore.find_hotel(payload.transport_id) if payload.transport_id else MockSupplierDataStore.hotels[0]
    rules = hotel["cancellation_rules"] if hotel else {"fare_tier": "FLEXIBLE", "refundable": True, "penalty_pct": 20.0, "cancellation_fee": 1000.0}

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=payload.original_price,
        currency=payload.currency,
        cancellation_rules=rules,
        is_disruption_waiver=payload.is_disruption_waiver,
        reason=payload.reason
    )

    return {
        "refund_transaction_id": f"RFD-HTL-{uuid.uuid4().hex[:8].upper()}",
        "supplier_type": "hotel",
        "status": "REFUND_APPROVED" if eval_result["refund_eligible"] else "NON_REFUNDABLE",
        "estimated_processing_days": 4,
        **eval_result,
        "processed_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


hotel_app = FastAPI(
    title="[MOCK API] Hotel Supplier CRS Service",
    description=MOCK_DISCLAIMER,
    version="1.0.0"
)
hotel_app.include_router(hotel_router)
