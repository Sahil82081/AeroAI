"""
UNIFIED MOCK SUPPLIER ECOSYSTEM GATEWAY.
Combines the 4 independent Mock Supplier Services:
1. Flight Supplier Service (GET /flights/search, POST /flights/rebook, ...)
2. Train Supplier Service  (GET /trains/search, POST /trains/rebook, ...)
3. Bus Supplier Service    (GET /buses/search, POST /buses/rebook, ...)
4. Hotel Supplier Service  (GET /hotels/search, POST /hotel/modify, ...)

Also exposes the unified REST endpoints:
- POST /bookings/rebook
- POST /bookings/cancel
- POST /bookings/refund
- POST /hotel/modify
- GET & POST /simulation/config
- POST /simulation/reset
"""
import sys
import os

# Ensure mock-suppliers directory is on sys.path for both standalone & embedded imports
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from common import (
    MOCK_DISCLAIMER,
    SimulationConfig,
    SimulationEngine,
    RebookRequestPayload,
    CancelRequestPayload,
    RefundRequestPayload
)
from datasets import MockSupplierDataStore
from flight_supplier import flight_router, rebook_flight, cancel_flight_booking, refund_flight_booking
from train_supplier import train_router, rebook_train, cancel_train_booking, refund_train_booking
from bus_supplier import bus_router, rebook_bus, cancel_bus_booking, refund_bus_booking
from hotel_supplier import hotel_router, cancel_hotel_booking, refund_hotel_booking

mock_supplier_app = FastAPI(
    title="[MOCK SUPPLIER ECOSYSTEM] Flight, Train, Bus & Hotel APIs",
    description=MOCK_DISCLAIMER,
    version="1.0.0"
)

mock_supplier_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@mock_supplier_app.middleware("http")
async def add_mock_supplier_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Mock-Supplier-API"] = "true"
    response.headers["X-Mock-Disclaimer"] = MOCK_DISCLAIMER
    return response


# Include the 4 separate supplier routers
mock_supplier_app.include_router(flight_router)
mock_supplier_app.include_router(train_router)
mock_supplier_app.include_router(bus_router)
mock_supplier_app.include_router(hotel_router)


@mock_supplier_app.post("/bookings/rebook", tags=["Unified Mock Booking Operations"])
def unified_rebook_booking(payload: RebookRequestPayload):
    """
    [MOCK API] Unified endpoint to rebook across Flight, Train, or Bus suppliers
    based on transport_id (e.g., FLT101, TRN123, BUS101).
    """
    tid = payload.transport_id.upper()
    if tid.startswith("FLT"):
        return rebook_flight(payload)
    elif tid.startswith("TRN"):
        return rebook_train(payload)
    elif tid.startswith("BUS"):
        return rebook_bus(payload)

    item = MockSupplierDataStore.find_transport(tid)
    if item:
        stype = item.get("supplier_type", "flight")
        if stype == "train":
            return rebook_train(payload)
        elif stype == "bus":
            return rebook_bus(payload)
    return rebook_flight(payload)


@mock_supplier_app.post("/bookings/cancel", tags=["Unified Mock Booking Operations"])
def unified_cancel_booking(payload: CancelRequestPayload):
    """
    [MOCK API] Unified endpoint to cancel a booking across Flight, Train, Bus, or Hotel suppliers.
    """
    stype = (payload.supplier_type or "").lower()
    tid = (payload.transport_id or "").upper()
    bref = (payload.booking_reference or "").upper()

    if stype == "train" or tid.startswith("TRN") or "TRN" in bref or "SHINKANSEN" in bref or "SHT" in bref:
        return cancel_train_booking(payload)
    elif stype == "bus" or tid.startswith("BUS") or "BUS" in bref or "TIN" in bref:
        return cancel_bus_booking(payload)
    elif stype == "hotel" or tid.startswith("HTL") or "HYATT" in bref or "MARRIOTT" in bref or "HTL" in bref:
        return cancel_hotel_booking(payload)
    return cancel_flight_booking(payload)


@mock_supplier_app.post("/bookings/refund", tags=["Unified Mock Booking Operations"])
def unified_refund_booking(payload: RefundRequestPayload):
    """
    [MOCK API] Unified endpoint to evaluate and process a refund claim across Flight, Train, Bus, or Hotel suppliers.
    """
    stype = (payload.supplier_type or "").lower()
    tid = (payload.transport_id or "").upper()
    bref = (payload.booking_reference or "").upper()

    if stype == "train" or tid.startswith("TRN") or "TRN" in bref or "SHINKANSEN" in bref:
        return refund_train_booking(payload)
    elif stype == "bus" or tid.startswith("BUS") or "BUS" in bref or "TIN" in bref:
        return refund_bus_booking(payload)
    elif stype == "hotel" or tid.startswith("HTL") or "HYATT" in bref or "HTL" in bref:
        return refund_hotel_booking(payload)
    return refund_flight_booking(payload)


@mock_supplier_app.get("/simulation/config", tags=["Mock Simulation Control"])
def get_simulation_config():
    """[MOCK API] Get current latency and failure simulation parameters."""
    return {
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "config": SimulationEngine.get_config().model_dump(),
        "recent_calls": SimulationEngine.get_call_log()[:25]
    }


@mock_supplier_app.post("/simulation/config", tags=["Mock Simulation Control"])
def update_simulation_config(config: SimulationConfig):
    """[MOCK API] Configure simulated latency range, random failure probability, or forced error mode."""
    updated = SimulationEngine.update_config(config)
    return {
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "status": "SIMULATION_CONFIG_UPDATED",
        "config": updated.model_dump()
    }


@mock_supplier_app.post("/simulation/reset", tags=["Mock Simulation Control"])
def reset_simulation_state():
    """[MOCK API] Reset all mock supplier inventories, booking ledger, and simulation config to defaults."""
    MockSupplierDataStore.reset()
    SimulationEngine.update_config(SimulationConfig())
    SimulationEngine.clear_call_log()
    return {
        "is_mock_api": True,
        "simulated": True,
        "disclaimer": MOCK_DISCLAIMER,
        "status": "INVENTORY_AND_SIMULATION_RESET",
        "counts": {
            "flights": len(MockSupplierDataStore.flights),
            "trains": len(MockSupplierDataStore.trains),
            "buses": len(MockSupplierDataStore.buses),
            "hotels": len(MockSupplierDataStore.hotels)
        }
    }


@mock_supplier_app.get("/health", tags=["Mock Simulation Control"])
def mock_supplier_health():
    return {
        "status": "healthy",
        "service": "MockSupplierEcosystemGateway",
        "is_mock_api": True,
        "simulated": True,
        "suppliers_active": ["flight", "train", "bus", "hotel"]
    }
