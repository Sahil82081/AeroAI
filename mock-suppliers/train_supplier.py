"""
MOCK TRAIN SUPPLIER SERVICE (Simulated Rail / IRCTC / JR Reservation API).
Exposes REST APIs for train search, rebooking, cancellation, and refund calculation.
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

train_router = APIRouter(tags=["Mock Train Supplier API"])


@train_router.get("/trains/search")
def search_trains(
    origin: Optional[str] = Query(default=None, description="Origin station or city (e.g. Delhi, Mumbai, Tokyo)"),
    destination: Optional[str] = Query(default=None, description="Destination station or city (e.g. Jaipur, Delhi, Kyoto)"),
    earliest_departure: Optional[str] = Query(default=None, description="Minimum departure ISO timestamp or HH:MM"),
    min_seats: int = Query(default=1, ge=1),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """
    [MOCK API] Search available trains across simulated rail reservation inventory.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockTrainSupplierCRS",
        endpoint="GET /trains/search",
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )

    results = []
    for item in MockSupplierDataStore.trains:
        if origin and not matches_location(item["origin"], item.get("origin_code", ""), origin):
            continue
        if destination and not matches_location(item["destination"], item.get("destination_code", ""), destination):
            continue
        if item["available_seats"] < min_seats:
            continue
        if earliest_departure:
            if len(earliest_departure) <= 5:
                dep_time_part = item["departure"].split("T")[-1][:5]
                if dep_time_part < earliest_departure:
                    continue
            else:
                if item["departure"] < earliest_departure[:19]:
                    continue
        results.append(item)

    return {
        "supplier_service": "MockTrainSupplierCRS",
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "simulated_latency_ms": latency_ms,
        "count": len(results),
        "results": results
    }


@train_router.post("/trains/rebook")
def rebook_train(payload: RebookRequestPayload):
    """
    [MOCK API] Rebook a passenger onto an alternative train and decrement available seat inventory.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockTrainSupplierCRS",
        endpoint="POST /trains/rebook",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    train = None
    for item in MockSupplierDataStore.trains:
        if item["transport_id"].upper() == payload.transport_id.upper():
            train = item
            break

    if not train:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TRAIN_NOT_FOUND",
                "message": f"[MOCK API] Train transport_id '{payload.transport_id}' not found in Mock Rail CRS.",
                "is_mock_api": True,
                "simulated": True
            }
        )

    if train["available_seats"] < payload.seats:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "INSUFFICIENT_SEATS",
                "message": f"[MOCK API] Train {train['train_number']} only has {train['available_seats']} seats left (requested {payload.seats}).",
                "is_mock_api": True,
                "simulated": True
            }
        )

    train["available_seats"] -= payload.seats
    rebooking_fee = 0.0 if payload.waive_change_fee else train["cancellation_rules"].get("rebooking_fee", 0.0)
    total_charged = round((train["price"] * payload.seats) + rebooking_fee, 2)
    new_pnr = f"MOCK-TRN-{uuid.uuid4().hex[:6].upper()}"

    confirmation = {
        "confirmation_number": new_pnr,
        "original_booking_ref": payload.original_booking_ref,
        "transport_id": train["transport_id"],
        "supplier_type": "train",
        "provider": train["provider"],
        "vehicle_number": train["train_number"],
        "origin": train["origin"],
        "destination": train["destination"],
        "departure": train["departure"],
        "arrival": train["arrival"],
        "passenger_name": payload.passenger_name,
        "seats_booked": payload.seats,
        "assigned_seat": "C4-28 (Window)",
        "base_fare": train["price"] * payload.seats,
        "rebooking_fee": rebooking_fee,
        "total_charged": total_charged,
        "currency": train["currency"],
        "remaining_seats": train["available_seats"],
        "status": "CONFIRMED",
        "booked_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }
    MockSupplierDataStore.booking_ledger[new_pnr] = confirmation
    return confirmation


@train_router.post("/trains/cancel")
def cancel_train_booking(payload: CancelRequestPayload):
    """
    [MOCK API] Cancel an existing train ticket and evaluate rail cancellation policy.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockTrainSupplierCRS",
        endpoint="POST /trains/cancel",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    train = MockSupplierDataStore.find_transport(payload.transport_id) if payload.transport_id else MockSupplierDataStore.trains[0]
    if train and payload.transport_id:
        train["available_seats"] += 1

    rules = train["cancellation_rules"] if train else {"fare_tier": "FLEXIBLE", "refundable": True, "penalty_pct": 10.0, "cancellation_fee": 65.0}
    price = payload.original_price if payload.original_price is not None else (train["price"] if train else 800.0)
    currency = train["currency"] if train else "INR"

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=price,
        currency=currency,
        cancellation_rules=rules,
        is_disruption_waiver=("DISRUPTION" in payload.reason.upper() or "MISSED" in payload.reason.upper()),
        reason=payload.reason
    )

    return {
        "cancellation_id": f"CAN-TRN-{uuid.uuid4().hex[:6].upper()}",
        "booking_reference": payload.booking_reference,
        "supplier_type": "train",
        "status": "CANCELLED",
        "cancelled_at": datetime.utcnow().isoformat(),
        "cancellation_evaluation": eval_result,
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


@train_router.post("/trains/refund")
def refund_train_booking(payload: RefundRequestPayload):
    """
    [MOCK API] Process a train ticket TDR/refund request based on rail rules and disruption waivers.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockTrainSupplierCRS",
        endpoint="POST /trains/refund",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    train = MockSupplierDataStore.find_transport(payload.transport_id) if payload.transport_id else MockSupplierDataStore.trains[0]
    rules = train["cancellation_rules"] if train else {"fare_tier": "FLEXIBLE", "refundable": True, "penalty_pct": 10.0, "cancellation_fee": 65.0}

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=payload.original_price,
        currency=payload.currency,
        cancellation_rules=rules,
        is_disruption_waiver=payload.is_disruption_waiver,
        reason=payload.reason
    )

    return {
        "refund_transaction_id": f"RFD-TRN-{uuid.uuid4().hex[:8].upper()}",
        "supplier_type": "train",
        "status": "REFUND_APPROVED" if eval_result["refund_eligible"] else "NON_REFUNDABLE",
        "estimated_processing_days": 3,
        **eval_result,
        "processed_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


train_app = FastAPI(
    title="[MOCK API] Train Supplier CRS Service",
    description=MOCK_DISCLAIMER,
    version="1.0.0"
)
train_app.include_router(train_router)
