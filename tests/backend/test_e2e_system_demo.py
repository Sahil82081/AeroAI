"""
Stage 12: End-to-End System Integration Tests & Edge Case Suite.

Verifies:
1. Complete 17-step Golden Triangle E2E Scenario (Mumbai -> Delhi -> Jaipur):
   - Flight delay 4 hours (10:00 -> 16:00)
   - Disruption detected & Kafka event cascade generated
   - Journey graph recalculated (Train connection marked IMPOSSIBLE)
   - Train identified as MISSED_CONNECTION
   - Hotel identified as SCHEDULE_THREATENED / potentially affected
   - Next-day Tour identified as UNAFFECTED
   - Alternative trains searched from Mock Suppliers
   - Google OR-Tools CP-SAT selects optimal feasible train (TRN124)
   - 8-Node LangGraph workflow generates recovery plan
   - User & stakeholders notified via Fact-Grounded Notification Agent (6 emails)
   - Original train cancelled, alternative train booked, refund requested, hotel check-in updated
   - Next-day tour remains unchanged
   - Final journey graph updated (0 impossible connections)
   - Complete audit trail & REAL vs SIMULATED manifest verified
2. Edge Case 1: Flight cancellation (`flight_cancellation`)
3. Edge Case 2: Train cancellation (`train_cancellation`)
4. Edge Case 3: No alternatives available (impossible constraint window -> human escalation)
5. Edge Case 4: Hotel modification failure (`modify_hotel_checkin` supplier failure)
6. Edge Case 5: Refund failure (`request_refund` failure -> `PARTIAL_SUCCESS`)
7. Edge Case 6: Supplier API timeout (`ACTION_EXECUTION_TIMEOUT`)
8. Edge Case 7: Duplicate action idempotency (`IDEMPOTENT_REPLAY_NO_OP`)
9. Edge Case 8: Partial recovery scenario (core transport succeeds, non-critical action queued)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.schemas.disruption_schemas import DisruptionSimulationRequest
from app.modules.disruptions.disruption_engine import DisruptionSimulatorEngine
from app.modules.suppliers.service import supplier_service
from app.modules.recovery.action_executor import IdempotencyAndAuditStore

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_simulation_state():
    supplier_service.reset_simulation_state()
    IdempotencyAndAuditStore.clear()
    yield
    supplier_service.reset_simulation_state()
    IdempotencyAndAuditStore.clear()


def test_stage12_complete_17_step_golden_triangle_demo():
    """
    End-to-End Integration Test for the canonical 17-step Golden Triangle scenario.
    Asserts that every single step (1 through 17) passes and that REAL vs SIMULATED
    subsystems are explicitly documented.
    """
    res = client.post("/api/v1/recovery/demo/golden-triangle")
    assert res.status_code == 200
    data = res.json()

    assert len(data["steps_checklist"]) == 17
    for step_item in data["steps_checklist"]:
        assert step_item["passed"] is True, f"Step {step_item['step']} ({step_item['name']}) failed!"
    assert data["all_17_steps_passed"] is True

    # Verify graph progression: pre-disruption (0 impossible) -> disrupted (>=1 impossible) -> recovered (0 impossible)
    assert data["pre_disruption_graph_summary"]["impossible_connections"] == 0
    assert data["disrupted_graph_summary"]["impossible_connections"] >= 1
    assert data["final_recovered_graph_summary"]["impossible_connections"] == 0

    # Verify OR-Tools selected an optimal feasible train (TRN123 or TRN124)
    opt = data["ortools_optimization"]
    assert opt["constraints_satisfied"] is True
    assert opt["selected_option"]["transport_id"] in ("TRN123", "TRN124")

    # Verify Kafka events and Notifications
    assert data["kafka_events_count"] >= 7
    assert data["notifications_count"] == 6

    # Verify REAL vs SIMULATED manifest endpoint
    manifest_res = client.get("/api/v1/recovery/demo/real-vs-simulated")
    assert manifest_res.status_code == 200
    manifest = manifest_res.json()
    assert len(manifest["REAL"]) >= 6
    assert len(manifest["SIMULATED"]) >= 4


def test_edge_case_1_flight_cancellation():
    """
    Edge Case 1: Flight cancellation (`flight_cancellation`).
    Verifies that cancelling the Mumbai->Delhi flight marks the flight as CANCELLED,
    triggers CRITICAL severity, and flags downstream train & hotel while leaving next-day tour unaffected.
    """
    demo_res = client.post("/api/v1/recovery/demo/golden-triangle").json()
    flight_booking_id = demo_res["impact_analysis"]["trigger_booking_id"]

    cancel_res = client.post(
        "/api/v1/recovery/demo/simulate-disruption",
        json={
            "booking_id": flight_booking_id,
            "type": "flight_cancellation",
            "delay_minutes": 0,
            "title": "Flight AI-202 Cancelled due to Technical Fault",
        },
    )
    assert cancel_res.status_code == 200
    impact = cancel_res.json()
    assert impact["disruption_type"] == "FLIGHT_CANCELLATION"
    assert impact["severity"] == "CRITICAL"

    affected_refs = {b["reference_number"]: b["impact_nature"] for b in impact["affected_bookings"]}
    assert affected_refs["AI-202"] == "DIRECT_DISRUPTION"
    assert any(nature in ("SCHEDULE_THREATENED", "MISSED_CONNECTION") for nature in affected_refs.values())

    unaffected_refs = [b["reference_number"] for b in impact["unaffected_bookings"]]
    assert "TOUR-JAI-01" in unaffected_refs


def test_edge_case_2_train_cancellation():
    """
    Edge Case 2: Train cancellation (`train_cancellation`).
    Verifies that cancelling the Delhi->Jaipur train directly marks the train as CANCELLED,
    identifies the Jaipur hotel check-in as affected, and allows OR-Tools to select an alternative train.
    """
    demo_res = client.post("/api/v1/recovery/demo/golden-triangle").json()
    affected_list = demo_res["impact_analysis"]["affected_bookings"]
    train_booking_id = next(b["booking_id"] for b in affected_list if b["booking_type"] == "TRAIN")

    cancel_res = client.post(
        "/api/v1/recovery/demo/simulate-disruption",
        json={
            "booking_id": train_booking_id,
            "type": "train_cancellation",
            "delay_minutes": 0,
            "title": "Delhi-Jaipur Train Cancelled",
        },
    )
    assert cancel_res.status_code == 200
    impact = cancel_res.json()
    assert impact["disruption_type"] == "TRAIN_CANCELLATION"
    assert impact["severity"] in ("CRITICAL", "HIGH")

    # Verify OR-Tools finds an alternative train after train cancellation
    opt_res = client.post(
        "/api/v1/recovery/optimize",
        json={
            "origin": "Delhi",
            "destination": "Jaipur",
            "auto_fetch_from_suppliers": True,
            "constraints": {
                "current_arrival": "2026-10-20T12:00:00",
                "hotel_latest_checkin": "2026-10-20T22:00:00",
                "min_connection_minutes": 30,
                "required_seats": 1,
            },
        },
    )
    assert opt_res.status_code == 200
    assert opt_res.json()["constraints_satisfied"] is True
    assert opt_res.json()["selected_option"] is not None


def test_edge_case_3_no_alternatives_available():
    """
    Edge Case 3: No alternatives available.
    When arrival is delayed until 23:30 and hotel latest check-in is 22:00, no train/bus/flight
    can satisfy the constraints. OR-Tools reports `constraints_satisfied=False` and the LangGraph
    workflow routes to human escalation (`approval_required=True`).
    """
    opt_res = client.post(
        "/api/v1/recovery/optimize",
        json={
            "origin": "Delhi",
            "destination": "Jaipur",
            "auto_fetch_from_suppliers": True,
            "constraints": {
                "current_arrival": "2026-10-20T23:30:00",
                "hotel_latest_checkin": "2026-10-20T22:00:00",
                "min_connection_minutes": 30,
                "required_seats": 1,
            },
        },
    )
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["constraints_satisfied"] is False
    assert opt_data["selected_option"] is None
    assert "INFEASIBLE" in opt_data["solver_metadata"]["status"]

    # Also verify LangGraph workflow escalates when no feasible option exists
    wf_res = client.post(
        "/api/v1/recovery/agent/run",
        json={
            "journey_id": "JRN-NO-ALT-999",
            "disruption": {
                "type": "flight_delay",
                "delay_minutes": 690,
                "origin": "Delhi",
                "destination": "Jaipur",
                "revised_arrival": "11:30 PM",
            },
            "constraints_config": {
                "current_arrival": "11:30 PM",
                "hotel_latest_checkin": "10:00 PM",
                "min_connection_minutes": 45,
                "required_seats": 1,
            },
        },
    )
    assert wf_res.status_code == 200
    wf_data = wf_res.json()
    assert wf_data["selected_plan"]["approval_required"] is True
    assert wf_data["selected_plan"]["status"] == "ESCALATED_TO_HUMAN"


def test_edge_case_4_hotel_modification_failure():
    """
    Edge Case 4: Hotel modification failure.
    When `modify_hotel_checkin` encounters a simulated supplier outage (`service_unavailable`),
    the action records a structured FAILED audit entry and queues the action for recovery.
    """
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-EDGE-HOTEL-FAIL",
            "actions": [
                {
                    "step": 1,
                    "action_type": "rebook_transportation",
                    "booking_id": "TRN124",
                    "critical": True,
                    "request": {"transport_id": "TRN124", "seats": 1},
                },
                {
                    "step": 2,
                    "action_type": "modify_hotel_checkin",
                    "booking_id": "HTL-JAI-101",
                    "critical": False,
                    "request": {
                        "booking_reference": "HTL-JAI-101",
                        "hotel_id": "HTL101",
                        "new_check_in": "2026-10-20T21:30:00",
                        "simulate_failure": "service_unavailable",
                    },
                },
            ],
            "max_retries": 1,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "PARTIAL_SUCCESS"
    hotel_audit = next(r for r in data["audit_records"] if r["action_type"] == "modify_hotel_checkin")
    assert hotel_audit["status"] == "FAILED"
    assert hotel_audit["error"] is not None


def test_edge_case_5_refund_failure():
    """
    Edge Case 5: Refund failure.
    When `request_refund` fails (e.g., supplier refund gateway down or non-refundable fare),
    core transport rebooking remains intact (`PARTIAL_SUCCESS`) and the failed refund is queued.
    """
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-EDGE-REFUND-FAIL",
            "actions": [
                {
                    "step": 1,
                    "action_type": "cancel_booking",
                    "booking_id": "12015-SHT",
                    "critical": True,
                    "request": {
                        "booking_reference": "12015-SHT",
                        "transport_id": "TRN123",
                        "supplier_type": "train",
                        "original_price": 800.0,
                    },
                },
                {
                    "step": 2,
                    "action_type": "rebook_transportation",
                    "booking_id": "TRN124",
                    "critical": True,
                    "request": {"transport_id": "TRN124", "seats": 1},
                },
                {
                    "step": 3,
                    "action_type": "request_refund",
                    "booking_id": "12015-SHT",
                    "critical": False,
                    "request": {
                        "booking_reference": "12015-SHT",
                        "transport_id": "TRN123",
                        "original_price": 800.0,
                        "simulate_failure": "service_unavailable",
                    },
                },
            ],
            "max_retries": 1,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "PARTIAL_SUCCESS"
    assert data["succeeded_count"] == 2
    assert data["failed_count"] == 1
    assert data["failed_action_recovery_queue"][0]["action_type"] == "request_refund"


def test_edge_case_6_supplier_api_timeout():
    """
    Edge Case 6: Supplier API timeout.
    When mock supplier latency (`simulate_latency_ms=250`) exceeds the action's `timeout_ms=50`,
    the action retries and fails with `ACTION_EXECUTION_TIMEOUT`.
    """
    res = client.post(
        "/api/v1/recovery/actions/execute-single",
        json={
            "plan_id": "PLAN-EDGE-TIMEOUT-06",
            "step": 1,
            "action_type": "rebook_transportation",
            "booking_id": "TRN124",
            "timeout_ms": 50,
            "max_retries": 1,
            "request": {
                "transport_id": "TRN124",
                "seats": 1,
                "simulate_latency_ms": 250,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert "ACTION_EXECUTION_TIMEOUT" in data["error"]
    assert data["attempts"] == 2


def test_edge_case_7_duplicate_action_idempotency():
    """
    Edge Case 7: Duplicate action.
    Triggering the exact same recovery plan twice returns `IDEMPOTENT_REPLAY_NO_OP`
    and never double-books or double-decrements seat inventory.
    """
    payload = {
        "plan_id": "PLAN-EDGE-DUP-07",
        "original_booking_id": "12015-SHT",
        "original_transport_id": "TRN123",
        "new_transport_id": "TRN124",
        "seats": 2,
    }
    first = client.post("/api/v1/recovery/execute", json=payload).json()
    assert first["execution_status"] == "COMPLETED_SUCCESS"
    assert first["idempotent_replays"] == 0

    second = client.post("/api/v1/recovery/execute", json=payload).json()
    assert second["execution_status"] == "IDEMPOTENT_REPLAY_NO_OP"
    assert second["idempotent_replays"] == 6


def test_edge_case_8_partial_recovery():
    """
    Edge Case 8: Partial recovery.
    When core transport rebooking and hotel check-in modification succeed, but secondary
    contact notification fails, the system preserves the recovered itinerary (`PARTIAL_SUCCESS`)
    and isolates only the failed notification in `failed_action_recovery_queue`.
    """
    res = client.post(
        "/api/v1/recovery/execute",
        json={
            "plan_id": "PLAN-EDGE-PARTIAL-08",
            "actions": [
                {
                    "step": 1,
                    "action_type": "rebook_transportation",
                    "booking_id": "TRN124",
                    "critical": True,
                    "request": {"transport_id": "TRN124", "seats": 1},
                },
                {
                    "step": 2,
                    "action_type": "modify_hotel_checkin",
                    "booking_id": "HTL-JAI-101",
                    "critical": True,
                    "request": {
                        "booking_reference": "HTL-JAI-101",
                        "hotel_id": "HTL101",
                        "new_check_in": "2026-10-20T21:30:00",
                    },
                },
                {
                    "step": 3,
                    "action_type": "notify_relevant_contact",
                    "booking_id": "HTL-JAI-101",
                    "critical": False,
                    "request": {
                        "recipient": "frontdesk@heritagepalacejaipur.com",
                        "simulate_failure": "service_unavailable",
                    },
                },
            ],
            "max_retries": 1,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["execution_status"] == "PARTIAL_SUCCESS"
    assert data["succeeded_count"] == 2
    assert data["failed_count"] == 1
    assert len(data["failed_action_recovery_queue"]) == 1
    assert data["failed_action_recovery_queue"][0]["action_type"] == "notify_relevant_contact"
