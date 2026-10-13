"""
MOCK FLIGHT SUPPLIER SERVICE (Simulated Airline GDS API).
Exposes REST APIs for flight search, rebooking, cancellation, and refund calculation.
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, APIRouter, Query, HTTPException

from common import (
    MOCK_DISCLAIMER,
    SimulationEngine,
    RebookRequestPayload,
    CancelRequestPayload,
    RefundRequestPayload,
    evaluate_cancellation_and_refund
)
from datasets import MockSupplierDataStore, matches_location

flight_router = APIRouter(tags=["Mock Flight Supplier API"])


@flight_router.get("/flights/search")
def search_flights(
    origin: Optional[str] = Query(default=None, description="Origin city or airport code (e.g. Mumbai, BOM, Delhi, SFO)"),
    destination: Optional[str] = Query(default=None, description="Destination city or airport code (e.g. Delhi, Jaipur, HND)"),
    earliest_departure: Optional[str] = Query(default=None, description="Minimum departure ISO timestamp or HH:MM"),
    min_seats: int = Query(default=1, ge=1),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """
    [MOCK API] Search available flights across simulated airline GDS inventory.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockFlightSupplierGDS",
        endpoint="GET /flights/search",
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )

    results = []
    for item in MockSupplierDataStore.flights:
        if origin and not matches_location(item["origin"], item.get("origin_code", ""), origin):
            continue
        if destination and not matches_location(item["destination"], item.get("destination_code", ""), destination):
            continue
        if item["available_seats"] < min_seats:
            continue
        if earliest_departure:
            # Support full ISO string or time prefix comparison
            if len(earliest_departure) <= 5:
                dep_time_part = item["departure"].split("T")[-1][:5]
                if dep_time_part < earliest_departure:
                    continue
            else:
                if item["departure"] < earliest_departure[:19]:
                    continue
        results.append(item)

    return {
        "supplier_service": "MockFlightSupplierGDS",
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "simulated_latency_ms": latency_ms,
        "count": len(results),
        "results": results
    }


@flight_router.post("/flights/rebook")
def rebook_flight(payload: RebookRequestPayload):
    """
    [MOCK API] Rebook a passenger onto an alternative flight and decrement seat inventory.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockFlightSupplierGDS",
        endpoint="POST /flights/rebook",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    flight = None
    for item in MockSupplierDataStore.flights:
        if item["transport_id"].upper() == payload.transport_id.upper():
            flight = item
            break

    if not flight:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "FLIGHT_NOT_FOUND",
                "message": f"[MOCK API] Flight transport_id '{payload.transport_id}' not found in Mock Flight GDS.",
                "is_mock_api": True,
                "simulated": True
            }
        )

    if flight["available_seats"] < payload.seats:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "INSUFFICIENT_SEATS",
                "message": f"[MOCK API] Flight {flight['flight_number']} only has {flight['available_seats']} seats left (requested {payload.seats}).",
                "is_mock_api": True,
                "simulated": True
            }
        )

    flight["available_seats"] -= payload.seats
    rebooking_fee = 0.0 if payload.waive_change_fee else flight["cancellation_rules"].get("rebooking_fee", 0.0)
    total_charged = round((flight["price"] * payload.seats) + rebooking_fee, 2)
    new_pnr = f"MOCK-FLT-{uuid.uuid4().hex[:6].upper()}"

    confirmation = {
        "confirmation_number": new_pnr,
        "original_booking_ref": payload.original_booking_ref,
        "transport_id": flight["transport_id"],
        "supplier_type": "flight",
        "provider": flight["provider"],
        "vehicle_number": flight["flight_number"],
        "origin": flight["origin"],
        "destination": flight["destination"],
        "departure": flight["departure"],
        "arrival": flight["arrival"],
        "passenger_name": payload.passenger_name,
        "seats_booked": payload.seats,
        "assigned_seat": "14C",
        "base_fare": flight["price"] * payload.seats,
        "rebooking_fee": rebooking_fee,
        "total_charged": total_charged,
        "currency": flight["currency"],
        "remaining_seats": flight["available_seats"],
        "status": "CONFIRMED",
        "booked_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }
    MockSupplierDataStore.booking_ledger[new_pnr] = confirmation
    return confirmation


@flight_router.post("/flights/cancel")
def cancel_flight_booking(payload: CancelRequestPayload):
    """
    [MOCK API] Cancel an existing flight booking and evaluate cancellation rules.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockFlightSupplierGDS",
        endpoint="POST /flights/cancel",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    flight = MockSupplierDataStore.find_transport(payload.transport_id) if payload.transport_id else MockSupplierDataStore.flights[0]
    if flight and payload.transport_id:
        flight["available_seats"] += 1

    rules = flight["cancellation_rules"] if flight else {"fare_tier": "STANDARD", "refundable": True, "penalty_pct": 15.0, "cancellation_fee": 500.0}
    price = payload.original_price if payload.original_price is not None else (flight["price"] if flight else 5850.0)
    currency = flight["currency"] if flight else "INR"

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=price,
        currency=currency,
        cancellation_rules=rules,
        is_disruption_waiver=("DISRUPTION" in payload.reason.upper() or "DELAY" in payload.reason.upper()),
        reason=payload.reason
    )

    return {
        "cancellation_id": f"CAN-FLT-{uuid.uuid4().hex[:6].upper()}",
        "booking_reference": payload.booking_reference,
        "supplier_type": "flight",
        "status": "CANCELLED",
        "cancelled_at": datetime.utcnow().isoformat(),
        "cancellation_evaluation": eval_result,
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


@flight_router.post("/flights/refund")
def refund_flight_booking(payload: RefundRequestPayload):
    """
    [MOCK API] Process a flight refund claim based on fare rules and disruption waiver eligibility.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockFlightSupplierGDS",
        endpoint="POST /flights/refund",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    flight = MockSupplierDataStore.find_transport(payload.transport_id) if payload.transport_id else MockSupplierDataStore.flights[0]
    rules = flight["cancellation_rules"] if flight else {"fare_tier": "STANDARD", "refundable": True, "penalty_pct": 15.0, "cancellation_fee": 500.0}

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=payload.original_price,
        currency=payload.currency,
        cancellation_rules=rules,
        is_disruption_waiver=payload.is_disruption_waiver,
        reason=payload.reason
    )

    return {
        "refund_transaction_id": f"RFD-FLT-{uuid.uuid4().hex[:8].upper()}",
        "supplier_type": "flight",
        "status": "REFUND_APPROVED" if eval_result["refund_eligible"] else "PARTIAL_TAX_REFUND_ONLY",
        "estimated_processing_days": 5,
        **eval_result,
        "processed_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


flight_app = FastAPI(
    title="[MOCK API] Flight Supplier GDS Service",
    description=MOCK_DISCLAIMER,
    version="1.0.0"
)
flight_app.include_router(flight_router)
