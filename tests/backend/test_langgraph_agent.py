"""
Stage 7 Unit & Integration Tests: LangGraph 8-Agent Autonomous Recovery Workflow.
Verifies structured state transitions, WHY explanations, action approval rules,
transient failure handling & retry loops, and REST API endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.modules.ai_agents.recovery_graph import recovery_workflow_runner

client = TestClient(app)


def _sample_train_alternatives():
    return [
        {
            "transport_id": "TRAIN-A",
            "name": "Train A",
            "supplier_type": "train",
            "provider": "Indian Railways",
            "origin": "Delhi",
            "destination": "Jaipur",
            "departure": "5:00 PM",
            "arrival": "8:30 PM",
            "price": 500.0,
            "currency": "INR",
            "available_seats": 12,
            "number_of_changes": 0,
            "reliability": 0.95
        },
        {
            "transport_id": "TRAIN-B",
            "name": "Train B",
            "supplier_type": "train",
            "provider": "Indian Railways",
            "origin": "Delhi",
            "destination": "Jaipur",
            "departure": "5:30 PM",
            "arrival": "9:00 PM",
            "price": 700.0,
            "currency": "INR",
            "available_seats": 18,
            "number_of_changes": 0,
            "reliability": 0.97
        },
        {
            "transport_id": "TRAIN-C",
            "name": "Train C",
            "supplier_type": "train",
            "provider": "Indian Railways",
            "origin": "Delhi",
            "destination": "Jaipur",
            "departure": "7:00 PM",
            "arrival": "10:30 PM",
            "price": 400.0,
            "currency": "INR",
            "available_seats": 25,
            "number_of_changes": 0,
            "reliability": 0.88
        }
    ]


def test_langgraph_workflow_autonomous_train_b_selection():
    """
    Verify all 8 LangGraph agents execute in sequence, select Train B when arrival is 4:30 PM
    with 45m connection buffer and 10:00 PM hotel cutoff, explain WHY Train B was selected,
    and execute rebooking, refund claim, and hotel modification.
    """
    state = recovery_workflow_runner.run_workflow({
        "journey_id": "JRN-TEST-01",
        "disruption": {
            "type": "flight_delay",
            "delay_minutes": 240,
            "origin": "Delhi",
            "destination": "Jaipur",
            "revised_arrival": "4:30 PM"
        },
        "alternatives": _sample_train_alternatives(),
        "constraints_config": {
            "current_arrival": "4:30 PM",
            "hotel_latest_checkin": "10:00 PM",
            "min_connection_minutes": 45,
            "required_seats": 1
        },
        "preferences_config": {
            "max_budget": 1000.0
        },
        "approval_rules": {
            "auto_approve_max_cost": 1000.0,
            "min_confidence_threshold": 0.75,
            "require_human_approval": False
        }
    })

    # Verify structured state keys required by prompt
    for key in ("journey_id", "disruption", "affected_bookings", "alternatives", "constraints", "selected_plan", "actions", "verification", "notifications"):
        assert key in state

    assert len(state["agent_trace"]) == 8
    assert state["selected_plan"]["selected_option"]["transport_id"] == "TRAIN-B"
    assert state["approval_required"] is False
    assert state["confidence_score"] >= 0.90

    why = state["selected_plan"]["why_selected"]
    assert "Train B was selected because it is the earliest feasible" in why
    assert "before the hotel's latest check-in time" in why
    assert "within the traveler's configured limit" in why

    # Verify all 3 actions were executed
    action_types = {a["action_type"]: a["status"] for a in state["actions"]}
    assert action_types["REBOOK_TRANSPORT"] == "EXECUTED"
    assert action_types["CLAIM_REFUND"] == "EXECUTED"
    assert action_types["MODIFY_HOTEL_CHECKIN"] == "EXECUTED"
    assert state["verification"]["verified"] is True
    assert len(state["notifications"]) == 2


def test_langgraph_workflow_approval_rules_prevent_blind_execution():
    """
    Verify that when an option exceeds the autonomous spend limit or confidence threshold,
    the AI does NOT blindly execute rebooking and instead stages it as AWAITING_TRAVELER_APPROVAL.
    """
    state = recovery_workflow_runner.run_workflow({
        "journey_id": "JRN-APPROVAL-02",
        "alternatives": _sample_train_alternatives(),
        "constraints_config": {
            "current_arrival": "4:30 PM",
            "hotel_latest_checkin": "10:00 PM",
            "min_connection_minutes": 45,
            "required_seats": 1
        },
        "preferences_config": {
            "max_budget": 1000.0
        },
        "approval_rules": {
            "auto_approve_max_cost": 500.0,  # Train B costs 700 > 500 autonomous spend cap
            "min_confidence_threshold": 0.75,
            "require_human_approval": False
        }
    })

    assert state["approval_required"] is True
    assert state["selected_plan"]["status"] == "PENDING_TRAVELER_APPROVAL"
    rebook_action = next(a for a in state["actions"] if a["action_type"] == "REBOOK_TRANSPORT")
    assert rebook_action["status"] == "AWAITING_TRAVELER_APPROVAL"


def test_langgraph_workflow_retry_on_transient_supplier_failure():
    """
    Verify that when Action Agent encounters a transient supplier failure,
    Verification Agent routes back to Action Agent via conditional edge and succeeds on retry.
    """
    state = recovery_workflow_runner.run_workflow({
        "journey_id": "JRN-RETRY-03",
        "alternatives": _sample_train_alternatives(),
        "simulate_transient_failures": 1,
        "max_retries": 2
    })

    assert state["verification"]["verified"] is True
    assert state["verification"]["retries_used"] == 1
    # 8 standard steps + 2 retry steps (Action Agent #2 + Verification Agent #2) = 10 trace entries
    assert len(state["agent_trace"]) == 10


def test_langgraph_rest_api_and_graph_metadata():
    """Verify POST /api/v1/recovery/agent/run and GET /api/v1/recovery/agent/graph-metadata."""
    meta_res = client.get("/api/v1/recovery/agent/graph-metadata")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert len(meta["nodes"]) == 8
    assert "flowchart TD" in meta["mermaid_diagram"]

    run_res = client.post(
        "/api/v1/recovery/agent/run",
        json={
            "journey_id": "JRN-LIVE-04",
            "disruption": {
                "type": "flight_delay",
                "delay_minutes": 240,
                "origin": "Delhi",
                "destination": "Jaipur",
                "revised_arrival": "2026-10-20T16:00:00"
            },
            "constraints_config": {
                "current_arrival": "2026-10-20T16:00:00",
                "hotel_latest_checkin": "2026-10-20T23:00:00",
                "min_connection_minutes": 60,
                "required_seats": 1
            },
            "preferences_config": {
                "max_budget": 5000.0
            }
        }
    )
    assert run_res.status_code == 200
    data = run_res.json()
    assert data["verification"]["verified"] is True
    assert data["selected_plan"]["selected_option"] is not None
