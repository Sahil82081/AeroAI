from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.models import (
    BookingType, BookingStatus, DisruptionType, DisruptionSeverity, DisruptionStatus,
    RecoveryPlanStatus, NotificationChannel, NotificationStatus
)

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Booking schemas
class BookingBase(BaseModel):
    reference_number: str
    booking_type: BookingType
    provider_name: str
    title: str
    description: Optional[str] = None
    status: BookingStatus = BookingStatus.CONFIRMED
    start_time: datetime
    end_time: datetime
    origin: Optional[str] = None
    destination: Optional[str] = None
    price: float = 0.0
    currency: str = "USD"
    raw_metadata: Optional[Dict[str, Any]] = None

class BookingCreate(BookingBase):
    journey_id: int

class BookingResponse(BookingBase):
    id: int
    journey_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Journey schemas
class JourneyNodeBase(BaseModel):
    node_key: str
    name: str
    location_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    properties: Optional[Dict[str, Any]] = None

class JourneyNodeResponse(JourneyNodeBase):
    id: int
    journey_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class JourneyEdgeBase(BaseModel):
    source_node_id: int
    target_node_id: int
    booking_id: Optional[int] = None
    transport_mode: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    duration_minutes: int = 0
    buffer_minutes: int = 0
    properties: Optional[Dict[str, Any]] = None

class JourneyEdgeResponse(JourneyEdgeBase):
    id: int
    journey_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class JourneyBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: str = "PLANNED"

class JourneyCreate(JourneyBase):
    pass

class JourneyResponse(JourneyBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    bookings: List[BookingResponse] = []
    nodes: List[JourneyNodeResponse] = []
    edges: List[JourneyEdgeResponse] = []

    class Config:
        from_attributes = True

# Disruption schemas
class DisruptionBase(BaseModel):
    disruption_type: DisruptionType
    severity: DisruptionSeverity = DisruptionSeverity.MEDIUM
    status: DisruptionStatus = DisruptionStatus.DETECTED
    title: str
    description: Optional[str] = None
    delay_minutes: int = 0
    affected_nodes: Optional[List[str]] = None
    simulated: bool = True

class DisruptionCreate(DisruptionBase):
    journey_id: int
    booking_id: Optional[int] = None

class DisruptionResponse(DisruptionBase):
    id: int
    journey_id: int
    booking_id: Optional[int] = None
    detected_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Recovery Plan schemas
class RecoveryPlanBase(BaseModel):
    status: RecoveryPlanStatus = RecoveryPlanStatus.PROPOSED
    summary: str
    reasoning_explanation: Optional[str] = None
    estimated_additional_cost: float = 0.0
    refund_opportunities: Optional[Dict[str, Any]] = None
    actions: List[Dict[str, Any]] = []
    alternatives_considered: Optional[List[Dict[str, Any]]] = None

class RecoveryPlanCreate(RecoveryPlanBase):
    journey_id: int
    disruption_id: int

class RecoveryPlanResponse(RecoveryPlanBase):
    id: int
    journey_id: int
    disruption_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Notification schemas
class NotificationBase(BaseModel):
    channel: NotificationChannel = NotificationChannel.EMAIL
    recipient: str
    subject: str
    content: str
    simulated: bool = True

class NotificationCreate(NotificationBase):
    journey_id: Optional[int] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    journey_id: Optional[int] = None
    status: NotificationStatus
    sent_at: datetime

    class Config:
        from_attributes = True

# Health schema
class HealthCheckResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    database: str
    timestamp: datetime
