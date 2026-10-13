from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class KafkaTopic(str, Enum):
    BOOKING_CREATED = "booking.created"
    BOOKING_UPDATED = "booking.updated"
    DISRUPTION_DETECTED = "disruption.detected"
    JOURNEY_AFFECTED = "journey.affected"
    RECOVERY_REQUESTED = "recovery.requested"
    RECOVERY_PLANNED = "recovery.planned"
    ACTION_REQUESTED = "action.requested"
    ACTION_COMPLETED = "action.completed"
    ACTION_FAILED = "action.failed"
    NOTIFICATION_REQUESTED = "notification.requested"
    DEAD_LETTER_TOPIC = "recovery.dlq"


ALL_KAFKA_TOPICS: List[str] = [
    KafkaTopic.BOOKING_CREATED.value,
    KafkaTopic.BOOKING_UPDATED.value,
    KafkaTopic.DISRUPTION_DETECTED.value,
    KafkaTopic.JOURNEY_AFFECTED.value,
    KafkaTopic.RECOVERY_REQUESTED.value,
    KafkaTopic.RECOVERY_PLANNED.value,
    KafkaTopic.ACTION_REQUESTED.value,
    KafkaTopic.ACTION_COMPLETED.value,
    KafkaTopic.ACTION_FAILED.value,
    KafkaTopic.NOTIFICATION_REQUESTED.value,
    KafkaTopic.DEAD_LETTER_TOPIC.value,
]


class KafkaEventEnvelope(BaseModel):
    """
    Standardized Kafka Event Schema with correlation tracking, idempotency keys,
    retry metadata, and WebSocket UI milestone summaries.
    """
    event_id: str = Field(..., description="Unique UUID for this specific event instance")
    correlation_id: str = Field(..., description="Shared UUID linking all events in a disruption recovery cascade")
    causation_id: Optional[str] = Field(None, description="Event ID of the upstream event that triggered this event")
    topic: str = Field(..., description="Kafka topic name")
    event_type: str = Field(..., description="Semantic event type identifier")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    producer: str = Field(..., description="Service or agent that produced this event")
    idempotency_key: str = Field(..., description="Deterministic key for idempotent consumer deduplication")
    partition: int = Field(0, description="Kafka partition index")
    offset: int = Field(0, description="Partition offset number")
    retry_count: int = Field(0, description="Number of delivery/processing retries attempted")
    max_retries: int = Field(3, description="Maximum allowed retries before routing to Dead-Letter Topic")
    ui_message: str = Field("", description="Real-time status milestone broadcast over WebSocket to the frontend")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured domain payload for the topic")


class DeadLetterEventRecord(BaseModel):
    """Schema for events routed to the Dead-Letter Topic (recovery.dlq) after exhausting retries."""
    dlq_id: str
    original_event: KafkaEventEnvelope
    failed_topic: str
    failed_consumer_group: str
    error_message: str
    retry_attempts: int
    retry_history: List[Dict[str, Any]] = Field(default_factory=list)
    failed_at: str
    replayed: bool = False


class EventDrivenDisruptionRequest(BaseModel):
    """Request payload to trigger the full Kafka event-driven disruption recovery pipeline."""
    journey_id: int = 1
    booking_ref: str = "AI-202"
    disruption_type: str = "flight_delay"
    delay_minutes: int = 240
    reason: str = "Air Traffic Control slot restriction & late inbound aircraft at BOM"
    correlation_id: Optional[str] = None
    event_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    step_delay_ms: int = Field(0, ge=0, le=2000, description="Optional delay between pipeline stages for live WebSocket visualization")
    inject_consumer_failure: Optional[str] = Field(
        None,
        description="Optional failure injection: 'recovery_agent_transient' (succeeds on retry 2), 'action_agent_poison_pill' (exhausts retries -> DLQ + action.failed)"
    )
    max_retries: int = Field(3, ge=0, le=5)
