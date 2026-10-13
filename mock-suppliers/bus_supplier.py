"""
MOCK BUS SUPPLIER SERVICE (Simulated Intercity Coach / Bus Aggregator API).
Exposes REST APIs for bus search, rebooking, cancellation, and refund calculation.
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

bus_router = APIRouter(tags=["Mock Bus Supplier API"])


@bus_router.get("/buses/search")
def search_buses(
    origin: Optional[str] = Query(default=None, description="Origin city or bus terminal (e.g. Delhi, HND)"),
    destination: Optional[str] = Query(default=None, description="Destination city or bus terminal (e.g. Jaipur, Chandigarh, Tokyo)"),
    earliest_departure: Optional[str] = Query(default=None, description="Minimum departure ISO timestamp or HH:MM"),
    min_seats: int = Query(default=1, ge=1),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """
    [MOCK API] Search available intercity buses across simulated coach inventory.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockBusSupplierAPI",
        endpoint="GET /buses/search",
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )

    results = []
    for item in MockSupplierDataStore.buses:
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
        "supplier_service": "MockBusSupplierAPI",
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "simulated_latency_ms": latency_ms,
        "count": len(results),
        "results": results
    }


@bus_router.post("/buses/rebook")
def rebook_bus(payload: RebookRequestPayload):
    """
    [MOCK API] Rebook a passenger onto an intercity bus and decrement available seat inventory.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockBusSupplierAPI",
        endpoint="POST /buses/rebook",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    bus = None
    for item in MockSupplierDataStore.buses:
        if item["transport_id"].upper() == payload.transport_id.upper():
            bus = item
            break

    if not bus:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "BUS_NOT_FOUND",
                "message": f"[MOCK API] Bus transport_id '{payload.transport_id}' not found in Mock Bus Aggregator.",
                "is_mock_api": True,
                "simulated": True
            }
        )

    if bus["available_seats"] < payload.seats:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "INSUFFICIENT_SEATS",
                "message": f"[MOCK API] Bus {bus['bus_number']} only has {bus['available_seats']} seats left (requested {payload.seats}).",
                "is_mock_api": True,
                "simulated": True
            }
        )

    bus["available_seats"] -= payload.seats
    rebooking_fee = 0.0 if payload.waive_change_fee else bus["cancellation_rules"].get("rebooking_fee", 0.0)
    total_charged = round((bus["price"] * payload.seats) + rebooking_fee, 2)
    new_pnr = f"MOCK-BUS-{uuid.uuid4().hex[:6].upper()}"

    confirmation = {
        "confirmation_number": new_pnr,
        "original_booking_ref": payload.original_booking_ref,
        "transport_id": bus["transport_id"],
        "supplier_type": "bus",
        "provider": bus["provider"],
        "vehicle_number": bus["bus_number"],
        "origin": bus["origin"],
        "destination": bus["destination"],
        "departure": bus["departure"],
        "arrival": bus["arrival"],
        "passenger_name": payload.passenger_name,
        "seats_booked": payload.seats,
        "assigned_seat": "8A (Lower Sleeper/Window)",
        "base_fare": bus["price"] * payload.seats,
        "rebooking_fee": rebooking_fee,
        "total_charged": total_charged,
        "currency": bus["currency"],
        "remaining_seats": bus["available_seats"],
        "status": "CONFIRMED",
        "booked_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }
    MockSupplierDataStore.booking_ledger[new_pnr] = confirmation
    return confirmation


@bus_router.post("/buses/cancel")
def cancel_bus_booking(payload: CancelRequestPayload):
    """
    [MOCK API] Cancel an existing bus ticket and evaluate bus operator cancellation rules.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockBusSupplierAPI",
        endpoint="POST /buses/cancel",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    bus = MockSupplierDataStore.find_transport(payload.transport_id) if payload.transport_id else MockSupplierDataStore.buses[0]
    if bus and payload.transport_id:
        bus["available_seats"] += 1

    rules = bus["cancellation_rules"] if bus else {"fare_tier": "FLEXIBLE", "refundable": True, "penalty_pct": 10.0, "cancellation_fee": 50.0}
    price = payload.original_price if payload.original_price is not None else (bus["price"] if bus else 750.0)
    currency = bus["currency"] if bus else "INR"

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=price,
        currency=currency,
        cancellation_rules=rules,
        is_disruption_waiver=("DISRUPTION" in payload.reason.upper()),
        reason=payload.reason
    )

    return {
        "cancellation_id": f"CAN-BUS-{uuid.uuid4().hex[:6].upper()}",
        "booking_reference": payload.booking_reference,
        "supplier_type": "bus",
        "status": "CANCELLED",
        "cancelled_at": datetime.utcnow().isoformat(),
        "cancellation_evaluation": eval_result,
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


@bus_router.post("/buses/refund")
def refund_bus_booking(payload: RefundRequestPayload):
    """
    [MOCK API] Process a bus ticket refund based on operator cancellation rules.
    """
    latency_ms = SimulationEngine.apply_simulation(
        supplier_name="MockBusSupplierAPI",
        endpoint="POST /buses/refund",
        simulate_failure=payload.simulate_failure,
        simulate_latency_ms=payload.simulate_latency_ms
    )

    bus = MockSupplierDataStore.find_transport(payload.transport_id) if payload.transport_id else MockSupplierDataStore.buses[0]
    rules = bus["cancellation_rules"] if bus else {"fare_tier": "FLEXIBLE", "refundable": True, "penalty_pct": 10.0, "cancellation_fee": 50.0}

    eval_result = evaluate_cancellation_and_refund(
        booking_reference=payload.booking_reference,
        original_price=payload.original_price,
        currency=payload.currency,
        cancellation_rules=rules,
        is_disruption_waiver=payload.is_disruption_waiver,
        reason=payload.reason
    )

    return {
        "refund_transaction_id": f"RFD-BUS-{uuid.uuid4().hex[:8].upper()}",
        "supplier_type": "bus",
        "status": "REFUND_APPROVED" if eval_result["refund_eligible"] else "NON_REFUNDABLE",
        "estimated_processing_days": 2,
        **eval_result,
        "processed_at": datetime.utcnow().isoformat(),
        "simulated_latency_ms": latency_ms,
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER
    }


bus_app = FastAPI(
    title="[MOCK API] Bus Supplier Service",
    description=MOCK_DISCLAIMER,
    version="1.0.0"
)
bus_app.include_router(bus_router)
