"""
Stage 8 Unit & Integration Tests: Autonomous Recovery Action Execution Engine.
Tests 6 action types, structured audit records, idempotency (preventing duplicate bookings),
retries, timeout handling, partial success, and compensating rollback.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.suppliers.service import supplier_service
from app.modules.recovery.action_executor import IdempotencyAndAuditStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    supplier_service.reset_simulation_state()
    IdempotencyAndAuditStore.clear()
    yield
    supplier_service.reset_simulation_state()
    IdempotencyAndAuditStore.clear()


def test_execute_full_recovery_plan_and_audit_records():
    """
    Verify that a recovery plan compiles into 6 executable actions (cancel, rebook,
    refund, hotel modify, notify traveler, notify contact) and produces structured audit records.
    """
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-FULL-001",
            "original_booking_id": "12015-SHT",
            "original_transport_id": "TRN123",
            "original_price": 800.0,
            "new_transport_id": "TRN124",
            "passenger_name": "Sahil Sharma",
            "seats": 1,
            "hotel_booking_id": "HTL-JAI-101",
            "hotel_id": "HTL101",
            "new_check_in": "2026-10-20T22:30:00"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "COMPLETED_SUCCESS"
    assert data["total_actions"] == 6
    assert data["succeeded_count"] == 6
    assert data["failed_count"] == 0
    assert data["simulated"] is True
    assert data["is_mock_supplier_transaction"] is True

    expected_types = [
        "cancel_booking",
        "rebook_transportation",
        "request_refund",
        "modify_hotel_checkin",
        "notify_traveler",
        "notify_relevant_contact"
    ]
    actual_types = [r["action_type"] for r in data["audit_records"]]
    assert actual_types == expected_types

    for record in data["audit_records"]:
        for key in ("action_type", "booking_id", "status", "timestamp", "request", "response", "error"):
            assert key in record
        assert record["status"] == "SUCCESS"
        assert record["error"] is None
        assert record["is_mock_supplier_transaction"] is True


def test_idempotency_prevents_duplicate_bookings_and_inventory_drain():
    """
    Verify that triggering the same recovery plan or action twice does NOT create
    duplicate bookings or decrement mock supplier seat inventory a second time.
    """
    # Check initial TRN124 seats (22)
    initial_trains = client.get("/trains/search", params={"origin": "Delhi", "destination": "Jaipur"}).json()["results"]
    trn124_before = next(t for t in initial_trains if t["transport_id"] == "TRN124")
    assert trn124_before["available_seats"] == 22

    payload = {
        "plan_id": "PLAN-IDEMP-777",
        "original_booking_id": "12015-SHT",
        "original_transport_id": "TRN123",
        "new_transport_id": "TRN124",
        "seats": 2
    }

    # First execution -> books 2 seats on TRN124 (22 -> 20)
    first_res = client.post("/api/v1/recovery/execute", json=payload)
    assert first_res.status_code == 200
    assert first_res.json()["execution_status"] == "COMPLETED_SUCCESS"
    assert first_res.json()["idempotent_replays"] == 0

    trains_after_first = client.get("/trains/search", params={"origin": "Delhi", "destination": "Jaipur"}).json()["results"]
    trn124_mid = next(t for t in trains_after_first if t["transport_id"] == "TRN124")
    assert trn124_mid["available_seats"] == 20

    # Second (accidental duplicate) execution with same plan_id -> idempotent replay, seats stay at 20!
    second_res = client.post("/api/v1/recovery/execute", json=payload)
    assert second_res.status_code == 200
    second_data = second_res.json()
    assert second_data["execution_status"] == "IDEMPOTENT_REPLAY_NO_OP"
    assert second_data["idempotent_replays"] == 6

    trains_after_second = client.get("/trains/search", params={"origin": "Delhi", "destination": "Jaipur"}).json()["results"]
    trn124_after = next(t for t in trains_after_second if t["transport_id"] == "TRN124")
    assert trn124_after["available_seats"] == 20  # Unchanged!


def test_retry_recovery_and_timeout_handling():
    """
    Verify transient supplier timeouts are automatically retried and recovered,
    and actions exceeding timeout_ms fail cleanly after retries.
    """
    # 1. Transient failure on Step 2 recovers on attempt #2
    retry_res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-RETRY-01",
            "new_transport_id": "TRN124",
            "max_retries": 2,
            "simulate_transient_failures_on_step": 2,
            "simulate_transient_count": 1
        }
    )
    assert retry_res.status_code == 200
    r_data = retry_res.json()
    assert r_data["execution_status"] == "COMPLETED_SUCCESS"
    step2_audit = next(r for r in r_data["audit_records"] if r["step"] == 2)
    assert step2_audit["status"] == "SUCCESS"
    assert step2_audit["attempts"] == 2

    # 2. Action exceeding timeout_ms budget fails with ACTION_EXECUTION_TIMEOUT
    timeout_res = client.post(
        "/api/v1/recovery/actions/execute-single",
        json={
            "plan_id": "PLAN-TIMEOUT-02",
            "step": 1,
            "action_type": "rebook_transportation",
            "booking_id": "TRN124",
            "timeout_ms": 50,
            "max_retries": 1,
            "request": {
                "transport_id": "TRN124",
                "seats": 1,
                "simulate_latency_ms": 200  # Exceeds 50ms timeout budget
            }
        }
    )
    assert timeout_res.status_code == 200
    t_data = timeout_res.json()
    assert t_data["status"] == "FAILED"
    assert t_data["attempts"] == 2
    assert "ACTION_EXECUTION_TIMEOUT" in t_data["error"]


def test_partial_success_on_non_critical_action_failure():
    """
    Verify that if core transport/hotel actions succeed but a non-critical step
    (e.g. notify_relevant_contact) fails, the plan reports PARTIAL_SUCCESS and
    queues only the failed action for recovery.
    """
    actions = [
        {
            "step": 1,
            "action_type": "rebook_transportation",
            "booking_id": "TRN124",
            "critical": True,
            "request": {"transport_id": "TRN124", "seats": 1}
        },
        {
            "step": 2,
            "action_type": "notify_relevant_contact",
            "booking_id": "HTL-JAI-101",
            "critical": False,
            "request": {"recipient": "hotel@example.com", "simulate_failure": "service_unavailable"}
        }
    ]
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-PARTIAL-01",
            "actions": actions,
            "max_retries": 1
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "PARTIAL_SUCCESS"
    assert data["succeeded_count"] == 1
    assert data["failed_count"] == 1
    assert len(data["failed_action_recovery_queue"]) == 1
    assert data["failed_action_recovery_queue"][0]["action_type"] == "notify_relevant_contact"


def test_compensating_rollback_when_rebook_fails_after_cancel():
    """
    Verify that when Step 1 (cancel_booking) succeeds and Step 2 (rebook_transportation)
    fails permanently (e.g., 409 insufficient seats), compensating rollback reinstates
    the cancelled booking and marks the plan ROLLED_BACK.
    """
    actions = [
        {
            "step": 1,
            "action_type": "cancel_booking",
            "booking_id": "12015-SHT",
            "critical": True,
            "request": {
                "booking_reference": "12015-SHT",
                "transport_id": "TRN123",
                "supplier_type": "train",
                "original_price": 800.0
            }
        },
        {
            "step": 2,
            "action_type": "rebook_transportation",
            "booking_id": "TRN124",
            "critical": True,
            "request": {
                "transport_id": "TRN124",
                "seats": 99  # Exceeds 22 available seats -> 409 INSUFFICIENT_SEATS
            }
        }
    ]
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-ROLLBACK-01",
            "actions": actions,
            "rollback_on_critical_failure": True
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "ROLLED_BACK"
    assert data["rolled_back_count"] == 1
    assert data["rollback_records"][0]["action_type"] == "rollback_reinstate_booking"
    assert data["rollback_records"][0]["status"] == "ROLLED_BACK"
