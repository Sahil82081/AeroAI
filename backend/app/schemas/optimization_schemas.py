"""
Pydantic Schemas for Stage 6: Recovery Optimization using Google OR-Tools.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OptimizationWeights(BaseModel):
    """Configurable multi-criteria objective weights for OR-Tools optimization."""
    price: float = Field(default=0.30, ge=0.0, description="Weight for ticket price minimization")
    travel_time: float = Field(default=0.25, ge=0.0, description="Weight for total transit duration minimization")
    waiting_time: float = Field(default=0.15, ge=0.0, description="Weight for connection layover/waiting time minimization")
    number_of_changes: float = Field(default=0.10, ge=0.0, description="Weight for minimizing transfers/stops")
    arrival_time: float = Field(default=0.10, ge=0.0, description="Weight for earlier arrival at destination")
    reliability: float = Field(default=0.10, ge=0.0, description="Weight for maximizing carrier on-time reliability")


class OptimizationConstraints(BaseModel):
    """Hard mathematical constraints enforced by Google OR-Tools CP-SAT solver."""
    current_arrival: str = Field(
        default="16:00",
        description="Traveler's current/revised arrival time at the transfer hub (ISO timestamp, HH:MM, or '4:00 PM')"
    )
    hotel_latest_checkin: Optional[str] = Field(
        default="22:00",
        description="Latest permissible check-in time at destination hotel (ISO timestamp, HH:MM, or '10:00 PM')"
    )
    min_connection_minutes: int = Field(
        default=30,
        ge=0,
        description="Minimum feasible transfer buffer in minutes between current arrival and option departure"
    )
    max_waiting_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Optional maximum waiting time at connection hub in minutes"
    )
    required_seats: int = Field(
        default=1,
        ge=1,
        description="Minimum available seats required on the alternative transport"
    )


class TravelerPreferences(BaseModel):
    """Passenger preferences and configurable objective weights."""
    max_budget: Optional[float] = Field(default=None, ge=0.0, description="Maximum acceptable ticket price")
    allowed_modes: Optional[List[str]] = Field(
        default=None,
        description="Allowed transport modes (e.g., ['train', 'flight', 'bus']). None allows all modes."
    )
    excluded_modes: List[str] = Field(
        default_factory=list,
        description="Transport modes to exclude (e.g., ['bus'])"
    )
    max_changes: Optional[int] = Field(default=None, ge=0, description="Maximum acceptable number of changes/transfers")
    min_reliability: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum reliability score (0.0-1.0)")
    weights: OptimizationWeights = Field(default_factory=OptimizationWeights)


class CandidateAlternativeInput(BaseModel):
    """Input representation of a candidate transport alternative."""
    transport_id: str
    name: Optional[str] = None
    supplier_type: str = Field(default="train", description="flight, train, or bus")
    provider: str = Field(default="Indian Railways")
    vehicle_number: Optional[str] = None
    origin: str = Field(default="Delhi")
    destination: str = Field(default="Jaipur")
    departure: str = Field(..., description="Departure time (ISO 8601, '17:00', or '5:00 PM')")
    arrival: str = Field(..., description="Arrival time (ISO 8601, '20:30', or '8:30 PM')")
    price: float = Field(..., ge=0.0)
    currency: str = Field(default="INR")
    available_seats: int = Field(default=10, ge=0)
    number_of_changes: int = Field(default=0, ge=0)
    reliability: float = Field(default=0.92, ge=0.0, le=1.0)
    duration_minutes: Optional[int] = None


class OptimizationRequest(BaseModel):
    """Complete input payload for the OR-Tools Recovery Optimization Service."""
    current_journey: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current journey context (optional metadata)"
    )
    disruption: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Disruption context triggering recovery optimization"
    )
    available_alternatives: Optional[List[CandidateAlternativeInput]] = Field(
        default=None,
        description="List of candidate transport alternatives. If omitted and auto_fetch_from_suppliers=True, fetched from Mock Suppliers."
    )
    auto_fetch_from_suppliers: bool = Field(
        default=False,
        description="Automatically query Mock Supplier Ecosystem (Flight/Train/Bus) when available_alternatives is not provided"
    )
    origin: str = Field(default="Delhi")
    destination: str = Field(default="Jaipur")
    constraints: OptimizationConstraints = Field(default_factory=OptimizationConstraints)
    traveler_preferences: TravelerPreferences = Field(default_factory=TravelerPreferences)


class OptimizationResponse(BaseModel):
    """Standardized output of the OR-Tools Recovery Optimization Engine."""
    selected_option: Optional[Dict[str, Any]] = None
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    objective_score: float = 0.0
    constraints_satisfied: bool = False
    explanation: str = ""
    solver_metadata: Dict[str, Any] = Field(default_factory=dict)
