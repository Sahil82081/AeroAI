from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from app.models.models import EmailParsingStatus

# Normalized booking payload schema produced by parser
class NormalizedBooking(BaseModel):
    type: Literal["flight", "train", "bus", "hotel", "activity"] = Field(..., description="Classified travel type")
    provider: str = Field(..., description="Provider name e.g., United Airlines, Amtrak, Marriott")
    booking_reference: str = Field(..., description="Booking PNR, reservation, or reference number")
    title: Optional[str] = None
    description: Optional[str] = None
    passenger: Optional[str] = None
    
    # Times
    departure: Optional[str] = Field(None, description="ISO datetime string for departure / check-in / start")
    arrival: Optional[str] = Field(None, description="ISO datetime string for arrival / check-out / end")
    
    # Locations
    origin: Optional[str] = Field(None, description="Origin city or airport / station code")
    destination: Optional[str] = Field(None, description="Destination city or airport / station code")
    
    # Specific attributes
    flight_number: Optional[str] = None
    train_number: Optional[str] = None
    bus_number: Optional[str] = None
    hotel_name: Optional[str] = None
    room_type: Optional[str] = None
    seat: Optional[str] = None
    price: Optional[float] = 0.0
    currency: Optional[str] = "USD"
    raw_metadata: Optional[Dict[str, Any]] = None

# Parser extraction result schema
class ParserExtractionResult(BaseModel):
    success: bool
    status: EmailParsingStatus
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score 0.0 - 1.0")
    booking_type: Optional[str] = None
    normalized_booking: Optional[NormalizedBooking] = None
    missing_fields: List[str] = Field(default_factory=list, description="Critical or desired fields that were absent")
    clarification_prompt: Optional[str] = Field(None, description="Clarification request if fields are uncertain or missing")
    error_message: Optional[str] = None
    parser_used: str = "heuristic"

# Email ingestion request/response schemas
class EmailIngestRequest(BaseModel):
    sender: str
    recipient: Optional[str] = "inbox@autonomous-recovery.travel"
    subject: str
    body: str
    journey_id: Optional[int] = None
    force_parser: Optional[Literal["auto", "heuristic", "gemini"]] = "auto"

class EmailIngestResponse(BaseModel):
    id: int
    user_id: int
    journey_id: Optional[int] = None
    booking_id: Optional[int] = None
    sender: str
    recipient: str
    subject: str
    parsing_status: EmailParsingStatus
    booking_type: Optional[str] = None
    confidence_score: float
    missing_fields: Optional[List[str]] = None
    clarification_prompt: Optional[str] = None
    error_message: Optional[str] = None
    parser_used: str
    parsed_data: Optional[Dict[str, Any]] = None
    received_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SampleEmailItem(BaseModel):
    id: str
    category: str
    title: str
    sender: str
    subject: str
    body: str
    is_imperfect: bool = False
    expected_type: str
