import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Enum, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base

# Enums
class BookingType(str, enum.Enum):
    FLIGHT = "FLIGHT"
    TRAIN = "TRAIN"
    BUS = "BUS"
    HOTEL = "HOTEL"
    ACTIVITY = "ACTIVITY"
    RENTAL_CAR = "RENTAL_CAR"

class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    MODIFIED = "MODIFIED"
    DELAYED = "DELAYED"

class DisruptionType(str, enum.Enum):
    FLIGHT_DELAY = "FLIGHT_DELAY"
    FLIGHT_CANCELLATION = "FLIGHT_CANCELLATION"
    TRAIN_DELAY = "TRAIN_DELAY"
    TRAIN_CANCELLATION = "TRAIN_CANCELLATION"
    BUS_CANCELLATION = "BUS_CANCELLATION"
    STRIKE = "STRIKE"
    WEATHER = "WEATHER"
    ROAD_BLOCK = "ROAD_BLOCK"
    HOTEL_OVERBOOKED = "HOTEL_OVERBOOKED"

class DisruptionSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DisruptionStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    EVALUATING = "EVALUATING"
    PLAN_GENERATED = "PLAN_GENERATED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class RecoveryPlanStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"

class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    WEBSOCKET = "WEBSOCKET"
    SMS = "SMS"

class NotificationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"

class EmailParsingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARSED = "PARSED"
    UNCERTAIN = "UNCERTAIN"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journeys = relationship("Journey", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    ingested_emails = relationship("IngestedEmail", back_populates="user", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    reference_number = Column(String(100), index=True, nullable=False)
    booking_type = Column(Enum(BookingType), nullable=False)
    provider_name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    origin = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)
    price = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    raw_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="bookings")
    disruptions = relationship("Disruption", back_populates="booking")


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="PLANNED")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="journeys")
    bookings = relationship("Booking", back_populates="journey", cascade="all, delete-orphan")
    nodes = relationship("JourneyNode", back_populates="journey", cascade="all, delete-orphan")
    edges = relationship("JourneyEdge", back_populates="journey", cascade="all, delete-orphan")
    disruptions = relationship("Disruption", back_populates="journey", cascade="all, delete-orphan")
    recovery_plans = relationship("RecoveryPlan", back_populates="journey", cascade="all, delete-orphan")


class JourneyNode(Base):
    __tablename__ = "journey_nodes"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    node_key = Column(String(100), nullable=False)  # e.g., 'JFK', 'LHR_HOTEL'
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)  # AIRPORT, STATION, HOTEL, EVENT
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    departure_time = Column(DateTime, nullable=True)
    properties = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="nodes")


class JourneyEdge(Base):
    __tablename__ = "journey_edges"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(Integer, ForeignKey("journey_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("journey_nodes.id", ondelete="CASCADE"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    
    transport_mode = Column(String(50), nullable=False) # FLIGHT, TRAIN, TRANSFER
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=0)
    buffer_minutes = Column(Integer, default=0) # time until next edge
    properties = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="edges")


class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    
    disruption_type = Column(Enum(DisruptionType), nullable=False)
    severity = Column(Enum(DisruptionSeverity), default=DisruptionSeverity.MEDIUM, nullable=False)
    status = Column(Enum(DisruptionStatus), default=DisruptionStatus.DETECTED, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    delay_minutes = Column(Integer, default=0)
    affected_nodes = Column(JSON, nullable=True) # list of impacted node IDs or labels
    simulated = Column(Boolean, default=True) # Clearly marked simulated/mocked

    detected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="disruptions")
    booking = relationship("Booking", back_populates="disruptions")
    recovery_plans = relationship("RecoveryPlan", back_populates="disruption")


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False)
    disruption_id = Column(Integer, ForeignKey("disruptions.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(Enum(RecoveryPlanStatus), default=RecoveryPlanStatus.PROPOSED, nullable=False)
    summary = Column(Text, nullable=False)
    reasoning_explanation = Column(Text, nullable=True) # Explains why decisions were made
    estimated_additional_cost = Column(Float, default=0.0)
    refund_opportunities = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=False) # list of planned steps/actions
    alternatives_considered = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journey = relationship("Journey", back_populates="recovery_plans")
    disruption = relationship("Disruption", back_populates="recovery_plans")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="SET NULL"), nullable=True)
    
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.EMAIL, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.SENT, nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    simulated = Column(Boolean, default=True) # Clearly marked simulated
    
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")


class IngestedEmail(Base):
    __tablename__ = "ingested_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="SET NULL"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)

    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    raw_body = Column(Text, nullable=False)

    parsing_status = Column(Enum(EmailParsingStatus), default=EmailParsingStatus.PENDING, nullable=False)
    booking_type = Column(String(50), nullable=True)  # flight, train, bus, hotel, activity
    confidence_score = Column(Float, default=0.0)
    parsed_data = Column(JSON, nullable=True)
    missing_fields = Column(JSON, nullable=True)
    clarification_prompt = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    parser_used = Column(String(50), default="heuristic")  # "gemini" or "heuristic"

    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="ingested_emails")
    booking = relationship("Booking")
