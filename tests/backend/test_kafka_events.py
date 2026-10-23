"""
Stage 9 Tests: Event-Driven Architecture with Apache Kafka & Real-Time WebSocket Updates
Covers:
1. All 10 domain Kafka topics + Dead-Letter Topic (`recovery.dlq`)
2. End-to-end event-driven disruption cascade:
   Disruption API -> Kafka -> Impact Agent -> Kafka -> Recovery Agent -> Kafka -> Action Agent -> Kafka -> Notification Agent
3. Correlation IDs, Causation IDs, Event IDs, and Timestamps
4. Idempotent Consumer deduplication (preventing duplicate cascade execution)
5. Consumer retry handling on transient failure (`recovery_agent_transient`)
6. Dead-Letter Topic (`recovery.dlq`) routing & replay on poison-pill failure (`action_agent_poison_pill`)
7. Real-Time WebSocket connection (`/api/v1/events/ws` & `/ws/events`) receiving live milestones
"""
from fastapi.testclient import TestClient
from app.main import app
from app.modules.suppliers.service import supplier_service

client = TestClient(app)


def setup_function():
    supplier_service.reset_simulation_state()
    client.post("/api/v1/recovery/actions/clear")
    client.post("/api/v1/events/reset")


def test_kafka_topics_and_full_event_driven_disruption_pipeline():
    """
    Verifies all 10 required Kafka topics exist and that triggering a disruption
    executes the full producer/consumer cascade with shared correlation_id and
    emits all 7 required real-time recovery updates.
    """
    # 1. Verify topics catalog
    topics_res = client.get("/api/v1/events/topics")
    assert topics_res.status_code == 200
    topic_names = [t["topic"] for t in topics_res.json()["topics"]]

    expected_topics = [
        "booking.created",
        "booking.updated",
        "disruption.detected",
        "journey.affected",
        "recovery.requested",
        "recovery.planned",
        "action.requested",
        "action.completed",
        "action.failed",
        "notification.requested",
        "recovery.dlq",
    ]
    for expected in expected_topics:
        assert expected in topic_names

    # 2. Trigger the event-driven disruption pipeline
    res = client.post(
        "/api/v1/events/disruption-pipeline",
        json={
            "journey_id": 1,
            "booking_ref": "AI-202",
            "disruption_type": "flight_delay",
            "delay_minutes": 240,
            "correlation_id": "corr-stage9-e2e",
            "auto_execute": True,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["correlation_id"] == "corr-stage9-e2e"
    assert data["total_events_emitted"] == 9

    # Check topics traversed in order
    assert data["topics_traversed"] == [
        "booking.updated",
        "disruption.detected",
        "journey.affected",
        "recovery.requested",
        "recovery.planned",
        "action.requested",
        "action.completed",
        "notification.requested",
    ]

    # Verify all events share the same correlation_id and have valid event_id and timestamp
    for evt in data["events"]:
        assert evt["correlation_id"] == "corr-stage9-e2e"
        assert evt["event_id"].startswith("evt-")
        assert "T" in evt["timestamp"]
        assert evt["idempotency_key"]

    # Verify real-time WebSocket milestone strings
    milestones = data["realtime_milestones"]
    required_milestones = [
        "Flight delay detected",
        "Train connection affected",
        "Searching alternatives",
        "Optimization completed",
        "Train rebooked",
        "Hotel updated",
        "Traveler notified",
    ]
    for req_ms in required_milestones:
        assert req_ms in milestones


def test_idempotent_consumer_deduplication():
    """
    Verifies that publishing a duplicate event (same event_id or idempotency_key)
    to `disruption.detected` is intercepted by `impact-agent-group` and skipped
    without triggering a duplicate downstream recovery cascade.
    """
    # First publish
    res1 = client.post(
        "/api/v1/events/disruption-pipeline",
        json={
            "journey_id": 1,
            "booking_ref": "AI-202",
            "disruption_type": "flight_delay",
            "delay_minutes": 240,
            "correlation_id": "corr-idem-test",
            "event_id": "evt-fixed-disruption-001",
            "idempotency_key": "KAFKA-IDEM-FIXED-001",
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["idempotent_skips"]) == 0

    # Re-publish the exact same disruption event directly to `disruption.detected`
    dup_res = client.post(
        "/api/v1/events/publish",
        json={
            "topic": "disruption.detected",
            "event_type": "DISRUPTION_DETECTED",
            "producer": "disruption-api",
            "correlation_id": "corr-idem-test",
            "event_id": "evt-fixed-disruption-001",
            "idempotency_key": "KAFKA-IDEM-FIXED-001",
            "ui_message": "Flight delay detected",
            "payload": {"journey_id": 1, "booking_ref": "AI-202", "delay_minutes": 240},
        },
    )
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    assert len(dup_data["idempotent_skips"]) >= 1
    assert dup_data["idempotent_skips"][-1]["status"] == "IDEMPOTENT_DUPLICATE_SKIPPED"
    assert dup_data["idempotent_skips"][-1]["consumer_group"] == "impact-agent-group"

    # Verify consumer metrics reflect 1 processed and 1 idempotent skip
    consumers_res = client.get("/api/v1/events/consumers")
    impact_group = next(
        g for g in consumers_res.json()["consumer_groups"] if g["group_id"] == "impact-agent-group"
    )
    assert impact_group["events_processed"] == 1
    assert impact_group["idempotent_skips"] == 1


def test_consumer_retry_handling_on_transient_error():
    """
    Verifies that when a consumer encounters a transient error (`recovery_agent_transient`),
    it automatically retries and succeeds on retry #1 without routing to DLQ.
    """
    res = client.post(
        "/api/v1/events/disruption-pipeline",
        json={
            "journey_id": 1,
            "booking_ref": "AI-202",
            "disruption_type": "flight_delay",
            "delay_minutes": 240,
            "correlation_id": "corr-retry-transient",
            "inject_consumer_failure": "recovery_agent_transient",
            "auto_execute": True,
            "max_retries": 3,
        },
    )
    assert res.status_code == 200
    data = res.json()

    # Pipeline still completed all the way to "Traveler notified"
    assert "Traveler notified" in data["realtime_milestones"]
    assert len(data["dlq_events"]) == 0

    # Recovery Agent consumer group recorded 1 retry attempt
    recovery_group = next(
        g for g in data["consumer_groups"] if g["group_id"] == "recovery-agent-group"
    )
    assert recovery_group["retry_attempts"] == 1
    assert recovery_group["events_processed"] == 1


def test_dead_letter_topic_and_dlq_replay():
    """
    Verifies that a poison-pill failure (`action_agent_poison_pill`) exhausts retries,
    routes the failed event to `recovery.dlq`, emits `action.failed`, and can then
    be replayed cleanly via `POST /api/v1/events/dlq/{dlq_id}/replay`.
    """
    res = client.post(
        "/api/v1/events/disruption-pipeline",
        json={
            "journey_id": 1,
            "booking_ref": "AI-202",
            "disruption_type": "flight_delay",
            "delay_minutes": 240,
            "correlation_id": "corr-dlq-test",
            "inject_consumer_failure": "action_agent_poison_pill",
            "auto_execute": True,
            "max_retries": 2,
        },
    )
    assert res.status_code == 200
    data = res.json()

    # Should have routed to DLQ and emitted action.failed
    assert len(data["dlq_events"]) == 1
    dlq_record = data["dlq_events"][0]
    assert dlq_record["failed_topic"] == "action.requested"
    assert dlq_record["failed_consumer_group"] == "action-agent-group"
    assert dlq_record["retry_attempts"] == 3  # 1 initial + 2 retries
    assert "recovery.dlq" in data["topics_traversed"]
    assert "action.failed" in data["topics_traversed"]

    # Inspect GET /api/v1/events/dlq
    dlq_list_res = client.get("/api/v1/events/dlq")
    assert dlq_list_res.status_code == 200
    assert dlq_list_res.json()["total_dlq_events"] == 1

    # Replay the DLQ event
    dlq_id = dlq_record["dlq_id"]
    replay_res = client.post(f"/api/v1/events/dlq/{dlq_id}/replay")
    assert replay_res.status_code == 200
    assert replay_res.json()["status"] == "REPLAYED_SUCCESSFULLY"

    # After replay, `action.completed` and `notification.requested` should now be present for `corr-dlq-test`
    stream_res = client.get("/api/v1/events/stream?correlation_id=corr-dlq-test")
    stream_topics = [e["topic"] for e in stream_res.json()["chronological_events"]]
    assert "action.completed" in stream_topics
    assert "notification.requested" in stream_topics


def test_websocket_realtime_recovery_updates():
    """
    Verifies that a frontend client connected to `/api/v1/events/ws` receives
    real-time Kafka events over WebSocket as a disruption cascade executes.
    """
    with client.websocket_connect("/api/v1/events/ws") as websocket:
        # 1. Receive initial WS_CONNECTED handshake
        welcome = websocket.receive_json()
        assert welcome["type"] == "WS_CONNECTED"

        # 2. Publish an event to `booking.created` while connected
        pub_res = client.post(
            "/api/v1/events/publish",
            json={
                "topic": "booking.created",
                "event_type": "BOOKING_CREATED",
                "producer": "email-ingestion-service",
                "correlation_id": "corr-ws-live",
                "ui_message": "Booking created: Air India AI-202",
                "payload": {"booking_ref": "AI-202", "journey_id": 1},
            },
        )
        assert pub_res.status_code == 200

        # 3. Receive the live KAFKA_EVENT frame from WebSocket
        ws_frame = websocket.receive_json()
        assert ws_frame["type"] == "KAFKA_EVENT"
        assert ws_frame["topic"] == "booking.created"
        assert ws_frame["correlation_id"] == "corr-ws-live"
        assert ws_frame["ui_message"] == "Booking created: Air India AI-202"
