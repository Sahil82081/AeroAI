from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from app.models.models import DisruptionType, DisruptionSeverity, DisruptionStatus

# Affected / Unaffected Booking details
class BookingImpactDetail(BaseModel):
    booking_id: int
    reference_number: str
    title: str
    booking_type: str
    provider: str
    status: str
    original_start_time: datetime
    original_end_time: datetime
    revised_start_time: Optional[datetime] = None
    revised_end_time: Optional[datetime] = None
    impact_nature: Literal["DIRECT_DISRUPTION", "MISSED_CONNECTION", "DOWNSTREAM_DELAY", "SCHEDULE_THREATENED"]
    impact_description: str

class UnaffectedBookingDetail(BaseModel):
    booking_id: int
    reference_number: str
    title: str
    booking_type: str
    provider: str
    start_time: datetime
    end_time: datetime
    reason_unaffected: str

class MissedConnectionDetail(BaseModel):
    from_booking_id: int
    from_booking_ref: str
    to_booking_id: int
    to_booking_ref: str
    scheduled_arrival: datetime
    revised_arrival: datetime
    next_departure: datetime
    deficit_minutes: int
    explanation: str

# Structured Disruption Impact Analysis output
class ImpactAnalysisResult(BaseModel):
    disruption_id: int
    journey_id: int
    trigger_booking_id: int
    trigger_booking_ref: str
    disruption_type: str
    delay_minutes: int
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    affected_bookings: List[BookingImpactDetail] = []
    unaffected_bookings: List[UnaffectedBookingDetail] = []
    missed_connections: List[MissedConnectionDetail] = []
    reasoning: str
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Disruption simulation payload
class DisruptionSimulationRequest(BaseModel):
    booking_id: int = Field(..., description="Target booking database ID")
    type: str = Field(..., description="flight_delay, flight_cancellation, train_delay, train_cancellation, bus_cancellation, strike, weather")
    delay_minutes: Optional[int] = Field(0, description="Delay duration in minutes (if delay)")
    title: Optional[str] = None
    description: Optional[str] = None
