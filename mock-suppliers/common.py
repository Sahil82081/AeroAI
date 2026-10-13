"""
Common utilities, schemas, and simulation middleware for the Mock Supplier Ecosystem.
IMPORTANT: All services using this module are explicitly marked as SIMULATED MOCK APIs.
"""
import time
import random
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException

MOCK_DISCLAIMER = "SIMULATED MOCK SUPPLIER API - FOR PROTOTYPE & DISRUPTION RECOVERY TESTING ONLY"


class SimulationConfig(BaseModel):
    """Runtime configuration for simulating API latency and supplier failures."""
    min_latency_ms: int = Field(default=15, ge=0, le=5000)
    max_latency_ms: int = Field(default=65, ge=0, le=5000)
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Probability (0.0 to 1.0) of random supplier error")
    forced_failure_mode: Optional[str] = Field(
        default=None,
        description="Optional forced failure mode: 'none', 'timeout', 'service_unavailable', 'seat_unavailable'"
    )


class SimulationEngine:
    """Manages simulated latency, failure injection, and state across mock suppliers."""
    _config: SimulationConfig = SimulationConfig()
    _call_log: List[Dict[str, Any]] = []

    @classmethod
    def get_config(cls) -> SimulationConfig:
        return cls._config

    @classmethod
    def update_config(cls, new_config: SimulationConfig) -> SimulationConfig:
        cls._config = new_config
        return cls._config

    @classmethod
    def apply_simulation(
        cls,
        supplier_name: str,
        endpoint: str,
        simulate_failure: Optional[str] = None,
        simulate_latency_ms: Optional[int] = None
    ) -> float:
        """
        Simulates network/GDS latency and optionally triggers realistic supplier API errors.
        Returns actual simulated latency in milliseconds.
        """
        # 1. Calculate and apply latency
        if simulate_latency_ms is not None and simulate_latency_ms >= 0:
            latency_ms = float(simulate_latency_ms)
        else:
            low = min(cls._config.min_latency_ms, cls._config.max_latency_ms)
            high = max(cls._config.min_latency_ms, cls._config.max_latency_ms)
            latency_ms = round(random.uniform(low, high), 2)

        if latency_ms > 0:
            # Cap actual blocking sleep in tests/requests to keep tests snappy while reporting realistic latency
            actual_sleep_sec = min(latency_ms / 1000.0, 0.25)
            time.sleep(actual_sleep_sec)

        # 2. Check failure injection
        failure_mode = simulate_failure or cls._config.forced_failure_mode
        if not failure_mode or failure_mode == "none":
            if cls._config.failure_rate > 0 and random.random() < cls._config.failure_rate:
                failure_mode = "service_unavailable"

        log_entry = {
            "id": f"sim-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
            "supplier": supplier_name,
            "endpoint": endpoint,
            "simulated_latency_ms": latency_ms,
            "failure_triggered": failure_mode if failure_mode and failure_mode != "none" else None,
            "is_mock_api": True
        }
        cls._call_log.append(log_entry)
        if len(cls._call_log) > 100:
            cls._call_log = cls._call_log[-100:]

        if failure_mode == "timeout":
            raise HTTPException(
                status_code=504,
                detail={
                    "error_code": "MOCK_SUPPLIER_GATEWAY_TIMEOUT",
                    "message": f"[MOCK API] {supplier_name} upstream reservation system timed out after {latency_ms}ms.",
                    "supplier": supplier_name,
                    "simulated": True,
                    "is_mock_api": True
                }
            )
        elif failure_mode == "service_unavailable":
            raise HTTPException(
                status_code=503,
                detail={
                    "error_code": "MOCK_SUPPLIER_SERVICE_UNAVAILABLE",
                    "message": f"[MOCK API] {supplier_name} GDS/CRS service is temporarily unavailable.",
                    "supplier": supplier_name,
                    "simulated": True,
                    "is_mock_api": True
                }
            )
        elif failure_mode == "seat_unavailable":
            raise HTTPException(
                status_code=409,
                detail={
                    "error_code": "MOCK_SUPPLIER_INVENTORY_EXHAUSTED",
                    "message": f"[MOCK API] Requested inventory on {supplier_name} is no longer available.",
                    "supplier": supplier_name,
                    "simulated": True,
                    "is_mock_api": True
                }
            )

        return latency_ms

    @classmethod
    def get_call_log(cls) -> List[Dict[str, Any]]:
        return list(reversed(cls._call_log))

    @classmethod
    def clear_call_log(cls) -> None:
        cls._call_log.clear()


class RebookRequestPayload(BaseModel):
    original_booking_ref: Optional[str] = None
    transport_id: str = Field(..., description="Target transport ID (e.g., TRN123, FLT202, BUS101)")
    passenger_name: str = Field(default="Sahil Sharma")
    seats: int = Field(default=1, ge=1, le=9)
    reason: Optional[str] = Field(default="DISRUPTION_RECOVERY")
    waive_change_fee: bool = Field(default=False)
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class CancelRequestPayload(BaseModel):
    booking_reference: str = Field(..., description="Booking reference or PNR to cancel")
    transport_id: Optional[str] = None
    supplier_type: Optional[str] = Field(default=None, description="flight, train, bus, or hotel")
    reason: str = Field(default="DISRUPTION_CASCADE")
    original_price: Optional[float] = None
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class RefundRequestPayload(BaseModel):
    booking_reference: str = Field(..., description="Booking reference or PNR for refund evaluation")
    transport_id: Optional[str] = None
    supplier_type: Optional[str] = Field(default=None, description="flight, train, bus, or hotel")
    original_price: float = Field(default=800.0, ge=0)
    currency: str = Field(default="INR")
    reason: str = Field(default="CARRIER_DISRUPTION")
    is_disruption_waiver: bool = Field(
        default=True,
        description="True if refund is requested due to carrier delay/cancellation or upstream missed connection"
    )
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


class HotelModifyRequestPayload(BaseModel):
    booking_reference: str = Field(..., description="Hotel reservation reference (e.g., HYATT-9921, HTL-JAI-101)")
    hotel_id: Optional[str] = Field(default="HTL101")
    new_check_in: str = Field(..., description="Updated ISO check-in datetime or time string")
    new_check_out: Optional[str] = None
    late_arrival_notice: bool = Field(default=True, description="Hold room for late arrival without no-show penalty")
    notes: Optional[str] = Field(default="Traveler delayed due to upstream flight/train disruption.")
    simulate_failure: Optional[str] = None
    simulate_latency_ms: Optional[int] = None


def evaluate_cancellation_and_refund(
    booking_reference: str,
    original_price: float,
    currency: str,
    cancellation_rules: Dict[str, Any],
    is_disruption_waiver: bool = False,
    reason: str = "DISRUPTION_RECOVERY"
) -> Dict[str, Any]:
    """
    Calculates cancellation penalty and refund eligibility based on supplier rules
    and whether a disruption waiver applies.
    """
    refundable_by_rule = cancellation_rules.get("refundable", True)
    penalty_pct = cancellation_rules.get("penalty_pct", 10.0)
    flat_fee = cancellation_rules.get("cancellation_fee", 0.0)
    tier = cancellation_rules.get("fare_tier", "STANDARD")

    if is_disruption_waiver:
        # Carrier disruption or involuntary schedule change waives standard penalties
        refund_eligible = True
        penalty_deducted = 0.0
        refund_amount = round(original_price, 2)
        policy_applied = f"INVOLUNTARY_DISRUPTION_WAIVER ({tier} tier penalty waived)"
    elif not refundable_by_rule:
        # Non-refundable tier without waiver: only taxes (approx 12%) refundable
        refund_eligible = False
        refund_amount = round(original_price * 0.12, 2)
        penalty_deducted = round(original_price - refund_amount, 2)
        policy_applied = f"NON_REFUNDABLE_TIER ({tier}) - Tax-only refund"
    else:
        refund_eligible = True
        pct_deduction = original_price * (penalty_pct / 100.0)
        penalty_deducted = round(min(original_price, max(pct_deduction, flat_fee)), 2)
        refund_amount = round(max(0.0, original_price - penalty_deducted), 2)
        policy_applied = f"STANDARD_CANCELLATION_POLICY ({penalty_pct}% penalty / {flat_fee} {currency} min fee)"

    return {
        "booking_reference": booking_reference,
        "refund_eligible": refund_eligible,
        "original_price": original_price,
        "penalty_deducted": penalty_deducted,
        "refund_amount": refund_amount,
        "currency": currency,
        "fare_tier": tier,
        "policy_applied": policy_applied,
        "reason": reason,
        "is_disruption_waiver": is_disruption_waiver
    }
