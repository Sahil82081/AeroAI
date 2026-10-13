"""
REST API Endpoints for the Mock Supplier Integration Layer.
Exposes search, rebooking, cancellation, refund, hotel modification,
and simulation controls through the decoupled SupplierIntegrationService -> SupplierAdapter -> Mock Supplier API pipeline.
"""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.modules.suppliers.service import supplier_service
from app.modules.suppliers.interfaces import SupplierAdapterException
from app.modules.events.event_bus import event_bus

router = APIRouter(tags=["Mock Suppliers (Stage 5)"])


class RebookAPIRequest(BaseModel):
    original_booking_ref: Optional[str] = "UA-875"
    transport_id: str = Field(..., description="Target transport ID (e.g., TRN123, FLT101, BUS101)")
    passenger_name: str = Field(default="Sahil Sharma")
    seats: int = Field(default=1, ge=1, le=9)
    reason: Optional[str] = Field(default="DISRUPTION_RECOVERY")
    waive_change_fee: bool = Field(default=False)
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class CancelAPIRequest(BaseModel):
    booking_reference: str = Field(..., description="Booking reference or PNR to cancel")
    transport_id: Optional[str] = None
    supplier_type: Optional[str] = Field(default=None, description="flight, train, bus, or hotel")
    reason: str = Field(default="DISRUPTION_CASCADE")
    original_price: Optional[float] = None
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class RefundAPIRequest(BaseModel):
    booking_reference: str = Field(..., description="Booking reference or PNR for refund evaluation")
    transport_id: Optional[str] = None
    supplier_type: Optional[str] = Field(default=None, description="flight, train, bus, or hotel")
    original_price: float = Field(default=800.0, ge=0)
    currency: str = Field(default="INR")
    reason: str = Field(default="CARRIER_DISRUPTION")
    is_disruption_waiver: bool = Field(default=True)
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class HotelModifyAPIRequest(BaseModel):
    booking_reference: str = Field(..., description="Hotel reservation reference (e.g., HYATT-9921, HTL-JAI-101)")
    hotel_id: Optional[str] = Field(default="HTL101")
    new_check_in: str = Field(..., description="Updated check-in timestamp or HH:MM")
    new_check_out: Optional[str] = None
    late_arrival_notice: bool = Field(default=True)
    notes: Optional[str] = Field(default="Traveler delayed due to upstream transit disruption.")
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class SimulationConfigAPIRequest(BaseModel):
    min_latency_ms: int = Field(default=15, ge=0, le=5000)
    max_latency_ms: int = Field(default=65, ge=0, le=5000)
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    forced_failure_mode: Optional[str] = None


def _handle_supplier_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except SupplierAdapterException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "is_mock_api": True,
                "simulated": True
            }
        )


@router.get("/flights/search")
@router.get("/suppliers/flights/search")
def search_flights_endpoint(
    origin: Optional[str] = Query(default=None),
    destination: Optional[str] = Query(default=None),
    earliest_departure: Optional[str] = Query(default=None),
    min_seats: int = Query(default=1, ge=1),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """[MOCK SUPPLIER API] Search available flights through the FlightSupplierAdapter."""
    return _handle_supplier_call(
        supplier_service.search_flights,
        origin=origin,
        destination=destination,
        earliest_departure=earliest_departure,
        min_seats=min_seats,
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )


@router.get("/trains/search")
@router.get("/suppliers/trains/search")
def search_trains_endpoint(
    origin: Optional[str] = Query(default=None),
    destination: Optional[str] = Query(default=None),
    earliest_departure: Optional[str] = Query(default=None),
    min_seats: int = Query(default=1, ge=1),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """[MOCK SUPPLIER API] Search available trains through the TrainSupplierAdapter."""
    return _handle_supplier_call(
        supplier_service.search_trains,
        origin=origin,
        destination=destination,
        earliest_departure=earliest_departure,
        min_seats=min_seats,
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )


@router.get("/buses/search")
@router.get("/suppliers/buses/search")
def search_buses_endpoint(
    origin: Optional[str] = Query(default=None),
    destination: Optional[str] = Query(default=None),
    earliest_departure: Optional[str] = Query(default=None),
    min_seats: int = Query(default=1, ge=1),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """[MOCK SUPPLIER API] Search available buses through the BusSupplierAdapter."""
    return _handle_supplier_call(
        supplier_service.search_buses,
        origin=origin,
        destination=destination,
        earliest_departure=earliest_departure,
        min_seats=min_seats,
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )


@router.get("/hotels/search")
@router.get("/suppliers/hotels/search")
def search_hotels_endpoint(
    location: Optional[str] = Query(default=None),
    min_rooms: int = Query(default=1, ge=1),
    late_checkin_only: bool = Query(default=False),
    simulate_failure: Optional[str] = Query(default=None),
    simulate_latency_ms: Optional[int] = Query(default=None)
):
    """[MOCK SUPPLIER API] Search available hotels through the HotelSupplierAdapter."""
    return _handle_supplier_call(
        supplier_service.search_hotels,
        location=location,
        min_rooms=min_rooms,
        late_checkin_only=late_checkin_only,
        simulate_failure=simulate_failure,
        simulate_latency_ms=simulate_latency_ms
    )


@router.get("/suppliers/multimodal/search")
def search_multimodal_endpoint(
    origin: str = Query(..., description="Origin city/code (e.g., Delhi)"),
    destination: str = Query(..., description="Destination city/code (e.g., Jaipur)"),
    earliest_departure: Optional[str] = Query(default=None),
    min_seats: int = Query(default=1, ge=1)
):
    """[MOCK SUPPLIER API] Search across Flight, Train, and Bus suppliers simultaneously."""
    return _handle_supplier_call(
        supplier_service.search_multimodal_alternatives,
        origin=origin,
        destination=destination,
        earliest_departure=earliest_departure,
        min_seats=min_seats
    )


@router.post("/bookings/rebook")
@router.post("/suppliers/bookings/rebook")
def rebook_booking_endpoint(payload: RebookAPIRequest):
    """[MOCK SUPPLIER API] Rebook a passenger onto an alternative flight, train, or bus."""
    res = _handle_supplier_call(supplier_service.rebook_booking, payload.model_dump())
    event_bus.publish("SUPPLIER_BOOKING_REBOOKED", {
        "confirmation_number": res.get("confirmation_number"),
        "transport_id": res.get("transport_id"),
        "supplier_type": res.get("supplier_type"),
        "total_charged": res.get("total_charged"),
        "simulated": True
    })
    return res


@router.post("/bookings/cancel")
@router.post("/suppliers/bookings/cancel")
def cancel_booking_endpoint(payload: CancelAPIRequest):
    """[MOCK SUPPLIER API] Cancel an existing booking and evaluate supplier cancellation rules."""
    res = _handle_supplier_call(supplier_service.cancel_booking, payload.model_dump())
    event_bus.publish("SUPPLIER_BOOKING_CANCELLED", {
        "cancellation_id": res.get("cancellation_id"),
        "booking_reference": res.get("booking_reference"),
        "supplier_type": res.get("supplier_type"),
        "simulated": True
    })
    return res


@router.post("/bookings/refund")
@router.post("/suppliers/bookings/refund")
def refund_booking_endpoint(payload: RefundAPIRequest):
    """[MOCK SUPPLIER API] Evaluate refund eligibility and process a simulated refund claim."""
    res = _handle_supplier_call(supplier_service.request_refund, payload.model_dump())
    event_bus.publish("SUPPLIER_REFUND_PROCESSED", {
        "refund_transaction_id": res.get("refund_transaction_id"),
        "booking_reference": res.get("booking_reference"),
        "refund_amount": res.get("refund_amount"),
        "refund_eligible": res.get("refund_eligible"),
        "simulated": True
    })
    return res


@router.post("/hotel/modify")
@router.post("/suppliers/hotel/modify")
def modify_hotel_endpoint(payload: HotelModifyAPIRequest):
    """[MOCK SUPPLIER API] Modify hotel check-in window or register late-arrival room hold."""
    res = _handle_supplier_call(supplier_service.modify_hotel, payload.model_dump())
    event_bus.publish("SUPPLIER_HOTEL_MODIFIED", {
        "modification_id": res.get("modification_id"),
        "booking_reference": res.get("booking_reference"),
        "updated_check_in": res.get("updated_check_in"),
        "simulated": True
    })
    return res


@router.get("/suppliers/simulation/config")
def get_simulation_config_endpoint():
    """[MOCK SUPPLIER API] Inspect current latency, failure simulation settings, and recent adapter call log."""
    return _handle_supplier_call(supplier_service.get_simulation_config)


@router.post("/suppliers/simulation/config")
def update_simulation_config_endpoint(payload: SimulationConfigAPIRequest):
    """[MOCK SUPPLIER API] Update latency and failure simulation parameters."""
    return _handle_supplier_call(supplier_service.update_simulation_config, payload.model_dump())


@router.post("/suppliers/simulation/reset")
def reset_simulation_endpoint():
    """[MOCK SUPPLIER API] Reset all mock supplier inventories and simulation state."""
    return _handle_supplier_call(supplier_service.reset_simulation_state)
