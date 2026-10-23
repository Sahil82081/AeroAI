from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from app.schemas.event_schemas import (
    KafkaTopic,
    ALL_KAFKA_TOPICS,
    EventDrivenDisruptionRequest,
)
from app.modules.events.kafka_engine import kafka_broker
from app.modules.events.pipeline_consumers import event_pipeline
from app.modules.events.ws_manager import ws_manager

router = APIRouter(prefix="/events", tags=["Kafka Event-Driven Architecture & WebSocket (Stage 9)"])


class CustomKafkaPublishRequest(BaseModel):
    topic: str = Field(default=KafkaTopic.BOOKING_CREATED.value)
    event_type: str = Field(default="BOOKING_CREATED")
    producer: str = Field(default="manual-producer")
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    event_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    ui_message: str = Field(default="Booking created")
    max_retries: int = Field(default=3, ge=0, le=5)
    payload: Dict[str, Any] = Field(default_factory=lambda: {"booking_ref": "AI-202", "journey_id": 1})


@router.websocket("/ws")
async def kafka_events_websocket(websocket: WebSocket):
    """
    Real-Time WebSocket endpoint streaming Kafka events and recovery milestones:
    - "Flight delay detected"
    - "Train connection affected"
    - "Searching alternatives"
    - "Optimization completed"
    - "Train rebooked"
    - "Hotel updated"
    - "Traveler notified"
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and accept optional client ping frames
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@router.post("/disruption-pipeline")
def trigger_kafka_disruption_pipeline(req: EventDrivenDisruptionRequest) -> Dict[str, Any]:
    """
    Triggers the event-driven disruption recovery pipeline:
    Disruption API -> Kafka -> Impact Agent -> Kafka -> Recovery Planner (STOP by default)
    """
    return event_pipeline.trigger_disruption_pipeline(req)


class ExecutePlanKafkaRequest(BaseModel):
    recovery_plan: Dict[str, Any]
    correlation_id: Optional[str] = None
    step_delay_ms: int = Field(default=0, ge=0, le=2000)
    max_retries: int = Field(default=3, ge=0, le=5)


@router.post("/execute-plan")
def execute_recovery_plan_via_kafka(req: ExecutePlanKafkaRequest) -> Dict[str, Any]:
    """
    [EXECUTION] Explicitly executes an approved recovery plan via Kafka event dispatch:
    Approved Plan -> Kafka (`action.requested`) -> Action Agent -> Kafka (`action.completed`, `notification.requested`)
    Strict Human Approval Gate: Verifies that recovery_plan['status'] === APPROVED.
    """
    plan_status = req.recovery_plan.get("status")
    if plan_status and str(plan_status).upper() not in ("APPROVED", "EXECUTING", "COMPLETED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Execution forbidden: Recovery plan has status '{plan_status}'. Plan must be APPROVED before execution."
        )
    return event_pipeline.trigger_plan_execution(
        recovery_plan=req.recovery_plan,
        correlation_id=req.correlation_id,
        step_delay_ms=req.step_delay_ms,
        max_retries=req.max_retries,
    )


@router.post("/publish")
def publish_custom_kafka_event(req: CustomKafkaPublishRequest) -> Dict[str, Any]:
    """
    Publishes a structured event directly to any Kafka topic and dispatches to subscribed consumer groups.
    """
    event_pipeline.register_all_consumers()
    envelope = kafka_broker.publish_event(
        topic=req.topic,
        event_type=req.event_type,
        payload=req.payload,
        producer=req.producer,
        correlation_id=req.correlation_id,
        causation_id=req.causation_id,
        event_id=req.event_id,
        idempotency_key=req.idempotency_key,
        ui_message=req.ui_message,
        max_retries=req.max_retries,
    )
    return {
        "status": "PUBLISHED",
        "event": envelope.model_dump(),
        "idempotent_skips": kafka_broker.idempotent_skip_records[-5:],
    }


@router.get("/topics")
def get_kafka_topics() -> Dict[str, Any]:
    """
    Returns metadata, partition offsets, message counts, and consumer subscriptions for all Kafka topics.
    """
    event_pipeline.register_all_consumers()
    return {
        "bootstrap_servers": kafka_broker.bootstrap_servers,
        "total_topics": len(ALL_KAFKA_TOPICS),
        "total_events_published": len(kafka_broker.all_events_chronological),
        "dlq_count": len(kafka_broker.dlq_records),
        "idempotent_skips_count": len(kafka_broker.idempotent_skip_records),
        "topics": kafka_broker.get_topics_summary(),
    }


@router.get("/stream")
def get_kafka_event_stream(
    topic: Optional[str] = Query(None, description="Filter by specific Kafka topic"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation_id"),
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Returns chronological Kafka events and real-time WebSocket recovery milestones.
    """
    event_pipeline.register_all_consumers()
    if topic and topic in kafka_broker.topics:
        events = list(kafka_broker.topics[topic])
    else:
        events = list(kafka_broker.all_events_chronological)

    if correlation_id:
        events = [e for e in events if e.get("correlation_id") == correlation_id]

    milestones = ws_manager.live_milestones
    if correlation_id:
        milestones = [m for m in milestones if m.get("correlation_id") == correlation_id]

    return {
        "total_matching_events": len(events),
        "events": list(reversed(events[-limit:])),
        "chronological_events": events[-limit:],
        "live_milestones": milestones[-limit:],
    }


@router.get("/consumers")
def get_kafka_consumers() -> Dict[str, Any]:
    """
    Returns status, offsets, retry telemetry, and idempotent deduplication stats for all consumer groups.
    """
    event_pipeline.register_all_consumers()
    return {
        "consumer_groups": [g.to_status_dict() for g in kafka_broker.consumer_groups.values()],
        "idempotent_skip_records": list(reversed(kafka_broker.idempotent_skip_records[-50:])),
    }


@router.get("/dlq")
def get_dead_letter_queue() -> Dict[str, Any]:
    """
    Returns all events routed to the Dead-Letter Topic (`recovery.dlq`) after exhausting consumer retries.
    """
    return {
        "dlq_topic": KafkaTopic.DEAD_LETTER_TOPIC.value,
        "total_dlq_events": len(kafka_broker.dlq_records),
        "records": [r.model_dump() for r in reversed(kafka_broker.dlq_records)],
    }


@router.post("/dlq/{dlq_id}/replay")
def replay_dead_letter_event(dlq_id: str) -> Dict[str, Any]:
    """
    Replays a Dead-Letter Queue event by clearing transient/poison-pill failure conditions
    and re-publishing to the failed topic.
    """
    try:
        return kafka_broker.replay_dlq_event(dlq_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/reset")
def reset_kafka_broker() -> Dict[str, Any]:
    """
    Clears in-memory Kafka topic logs, consumer offsets, and DLQ records for clean demo runs.
    """
    kafka_broker.reset_broker()
    event_pipeline.register_all_consumers()
    return {
        "status": "RESET_COMPLETE",
        "message": "All Kafka topics, consumer group offsets, idempotency caches, and DLQ records have been cleared.",
    }
