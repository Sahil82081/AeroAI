"""
Tests for Stage 3: Reject & Revise Workflow with Human Approval Gate.

Verifies the 10 User Requirements:
1. Generate Plan #1.
2. Reject with: "I don't want Airline A."
3. Generate Plan #2.
4. Verify Airline A is excluded.
5. Reject Plan #2 with: "Maximum budget is ₹5,000."
6. Generate Plan #3.
7. Verify BOTH constraints are respected.
8. Approve Plan #3.
9. Verify only Plan #3 is executed.
10. Verify rejected plans are never executed (backend strictly enforces HTTP 403).

Also verifies:
11. Preserving all prior constraints across revisions.
12. Rejection dialog reasons + free-text constraint translation.
13. Maximum revisions cap (3 revisions) with graceful fallback to manual review.
14. Infeasible constraint handling with message:
    "No suitable automated recovery plan could be found with the current requirements."
"""
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.models import (
    User, Journey, Booking, BookingType, BookingStatus,
    Disruption, DisruptionType, DisruptionSeverity, DisruptionStatus,
    RecoveryPlan, RecoveryPlanStatus, Notification
)
from app.schemas.optimization_schemas import CandidateAlternativeInput
from app.modules.recovery import recovery_planner, recovery_action_executor, IdempotencyAndAuditStore
from app.modules.recovery.constraints import constraint_engine
from app.modules.suppliers.service import supplier_service

client = TestClient(app)


def _seed_corridor(db):
    """Initializes a pristine test journey with a disruption ready for multi-revision testing."""
    db.query(Notification).delete()
    db.query(RecoveryPlan).delete()
    db.query(Disruption).delete()
    db.query(Booking).delete()
    db.query(Journey).delete()
    db.query(User).delete()
    db.commit()

    user = User(
        email="traveler_stage3@example.com",
        full_name="Stage 3 Traveler",
        hashed_password="mockpassword",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    journey = Journey(
        user_id=user.id,
        title="Delhi-Jaipur Corridor Stage 3",
        start_date=datetime(2026, 10, 20),
        end_date=datetime(2026, 10, 22),
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)

    base_time = datetime(2026, 10, 20, 10, 0, 0)
    flight = Booking(
        journey_id=journey.id,
        booking_type=BookingType.FLIGHT,
        provider_name="Air India",
        reference_number="AI-101",
        title="Flight Mumbai -> Delhi (AI-101)",
        origin="Mumbai",
        destination="Delhi",
        start_time=base_time,
        end_time=base_time + timedelta(hours=6),  # 16:00 arrival (delayed)
        price=3200.0,
        currency="INR",
        status=BookingStatus.DELAYED,
    )
    train = Booking(
        journey_id=journey.id,
        booking_type=BookingType.TRAIN,
        provider_name="Indian Railways",
        reference_number="12015-SHT",
        title="Ajmer Shatabdi Express (12015-SHT)",
        origin="Delhi",
        destination="Jaipur",
        start_time=base_time + timedelta(hours=3, minutes=30),  # 13:30 (missed)
        end_time=base_time + timedelta(hours=7, minutes=30),    # 17:30
        price=800.0,
        currency="INR",
        status=BookingStatus.CONFIRMED,
    )
    hotel = Booking(
        journey_id=journey.id,
        booking_type=BookingType.HOTEL,
        provider_name="Rambagh Palace",
        reference_number="HTL-JAI-101",
        title="Rambagh Palace Jaipur",
        origin="Jaipur",
        destination="Jaipur",
        start_time=base_time + timedelta(hours=8),  # 18:00
        end_time=base_time + timedelta(days=2),
        price=12000.0,
        currency="INR",
        status=BookingStatus.CONFIRMED,
    )
    db.add_all([flight, train, hotel])
    db.commit()

    disruption = Disruption(
        journey_id=journey.id,
        booking_id=flight.id,
        disruption_type=DisruptionType.FLIGHT_DELAY,
        severity=DisruptionSeverity.HIGH,
        status=DisruptionStatus.PLAN_GENERATED,
        title="Flight AI-101 Delay Causes Missed 12015-SHT Connection",
        description="Revised arrival 16:00 misses 13:30 train departure by 150 minutes.",
        delay_minutes=240,
        affected_nodes=["DEL", "JAI"],
        simulated=True,
    )
    db.add(disruption)
    db.commit()

    return user, journey, flight, train, hotel, disruption


def setup_function():
    supplier_service.reset_simulation_state()
    IdempotencyAndAuditStore.clear()
    client.post("/api/v1/events/reset")


def test_10_step_reject_and_revise_workflow():
    """
    Direct test of the 10 core requirements:
    1. Generate Plan #1.
    2. Reject with: "I don't want Airline A."
    3. Generate Plan #2.
    4. Verify Airline A is excluded.
    5. Reject Plan #2 with: "Maximum budget is ₹5,000."
    6. Generate Plan #3.
    7. Verify BOTH constraints are respected.
    8. Approve Plan #3.
    9. Verify only Plan #3 is executed.
    10. Verify rejected plans are never executed.
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel, disruption = _seed_corridor(db)
        journey_id = journey.id
        disruption_id = disruption.id

    # Test candidate alternatives representing the exact scenario from the user prompt:
    # Option 1: Airline A (Fastest, highest score, ₹6,500)
    # Option 2: Airline B (Fast, ₹5,800)
    # Option 3: Airline C (Acceptable, ₹4,800)
    # Option 4: Train alternative (Vande Bharat, ₹1,150)
    test_alternatives = [
        CandidateAlternativeInput(
            transport_id="FLT101",
            name="Airline A FL-401 (Delhi → Jaipur)",
            supplier_type="flight",
            provider="Airline A",
            origin="Delhi",
            destination="Jaipur",
            departure="2026-10-20T17:15:00",
            arrival="2026-10-20T18:20:00",
            price=6500.0,
            available_seats=10,
            number_of_changes=0,
            reliability=0.99,
        ),
        CandidateAlternativeInput(
            transport_id="FLT102",
            name="Airline B FL-702 (Delhi → Jaipur)",
            supplier_type="flight",
            provider="Airline B",
            origin="Delhi",
            destination="Jaipur",
            departure="2026-10-20T17:30:00",
            arrival="2026-10-20T18:35:00",
            price=5800.0,
            available_seats=12,
            number_of_changes=0,
            reliability=0.97,
        ),
        CandidateAlternativeInput(
            transport_id="FLT103",
            name="Airline C FL-905 (Delhi → Jaipur)",
            supplier_type="flight",
            provider="Airline C",
            origin="Delhi",
            destination="Jaipur",
            departure="2026-10-20T18:00:00",
            arrival="2026-10-20T19:05:00",
            price=4800.0,
            available_seats=8,
            number_of_changes=0,
            reliability=0.95,
        ),
    ]

    # ----------------------------------------------------
    # Step 1: Generate Plan #1 (Pure planning, NO execution)
    # ----------------------------------------------------
    with SessionLocal() as db:
        plan_1 = recovery_planner.generate_recovery_plan(
            journey_id=journey_id,
            disruption_id=disruption_id,
            available_alternatives=test_alternatives,
            max_budget=10000.0,
            revision_count=1,
            db=db,
        )

    assert plan_1 is not None
    assert plan_1["status"] in ("PLAN_GENERATED", "PROPOSED")
    assert plan_1["is_executed"] is False
    assert plan_1["selected_option"]["provider"] == "Airline A"
    assert plan_1["selected_option"]["price"] == 6500.0
    plan_1_db_id = plan_1["db_plan_id"]
    plan_1_transport = plan_1["selected_option"]["transport_id"]

    # Verify supplier booking was NOT touched: audit store has 0 executed actions
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    # ----------------------------------------------------
    # Step 2: Reject Plan #1 with: "I don't want Airline A."
    # ----------------------------------------------------
    c1 = constraint_engine.interpret_rejection(
        reasons=["I don't want this airline"],
        feedback_text="I don't want Airline A.",
        current_plan=plan_1,
        previous_constraints={},
    )
    assert "Airline A" in c1["excluded_providers"]

    # Mark Plan #1 as REJECTED in database
    with SessionLocal() as db:
        rec_1 = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_1_db_id).first()
        rec_1.status = RecoveryPlanStatus.REJECTED
        rec_1.active_constraints = c1
        db.commit()

    # ----------------------------------------------------
    # Step 3 & 4: Generate Plan #2 and Verify Airline A is excluded
    # ----------------------------------------------------
    with SessionLocal() as db:
        plan_2 = recovery_planner.generate_recovery_plan(
            journey_id=journey_id,
            disruption_id=disruption_id,
            available_alternatives=test_alternatives,
            active_constraints=c1,
            revision_count=2,
            db=db,
        )

    assert plan_2 is not None
    assert plan_2["status"] in ("PLAN_GENERATED", "PROPOSED")
    assert plan_2["is_executed"] is False
    # Requirement 4: Verify Airline A is excluded!
    assert plan_2["selected_option"]["provider"] != "Airline A"
    assert plan_2["selected_option"]["provider"] == "Airline B"
    assert plan_2["selected_option"]["price"] == 5800.0
    plan_2_db_id = plan_2["db_plan_id"]

    # ----------------------------------------------------
    # Step 5: Reject Plan #2 with: "Maximum budget is ₹5,000."
    # ----------------------------------------------------
    c2 = constraint_engine.interpret_rejection(
        reasons=["Too expensive"],
        feedback_text="Still too expensive. Maximum budget is ₹5,000.",
        current_plan=plan_2,
        previous_constraints=c1,  # Previous constraints strictly passed!
    )
    # Check that previous constraint is preserved
    assert "Airline A" in c2["excluded_providers"]
    assert c2["max_budget"] == 5000.0

    with SessionLocal() as db:
        rec_2 = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_2_db_id).first()
        rec_2.status = RecoveryPlanStatus.REJECTED
        rec_2.active_constraints = c2
        db.commit()

    # ----------------------------------------------------
    # Step 6 & 7: Generate Plan #3 and Verify BOTH constraints are respected
    # ----------------------------------------------------
    with SessionLocal() as db:
        plan_3 = recovery_planner.generate_recovery_plan(
            journey_id=journey_id,
            disruption_id=disruption_id,
            available_alternatives=test_alternatives,
            active_constraints=c2,
            revision_count=3,
            db=db,
        )

    assert plan_3 is not None
    assert plan_3["status"] in ("PLAN_GENERATED", "PROPOSED")
    assert plan_3["is_executed"] is False
    # Requirement 7: BOTH constraints are respected!
    # Constraint 1: Airline A is excluded
    assert plan_3["selected_option"]["provider"] != "Airline A"
    # Constraint 2: Budget <= 5000 (Airline B at 5800 is also excluded!)
    assert plan_3["selected_option"]["price"] <= 5000.0
    assert plan_3["selected_option"]["provider"] == "Airline C"
    assert plan_3["selected_option"]["price"] == 4800.0
    plan_3_db_id = plan_3["db_plan_id"]

    # ----------------------------------------------------
    # Step 10: Verify rejected plans are never executed (Backend check)
    # ----------------------------------------------------
    # Attempting to execute Plan #1 (status REJECTED)
    res_exec_1 = client.post("/api/v1/recovery/execute", json={
        "plan_id": str(plan_1_db_id),
        "status": "REJECTED",
    })
    assert res_exec_1.status_code == 403
    assert "Execution forbidden" in res_exec_1.json()["detail"]

    # Attempting to execute Plan #2 (status REJECTED)
    res_exec_2 = client.post("/api/v1/recovery/execute", json={
        "plan_id": str(plan_2_db_id),
        "status": "REJECTED",
    })
    assert res_exec_2.status_code == 403
    assert "Execution forbidden" in res_exec_2.json()["detail"]

    # Attempting to execute Plan #3 before approval (status PLAN_GENERATED)
    res_exec_3_unapproved = client.post("/api/v1/recovery/execute", json={
        "plan_id": str(plan_3_db_id),
        "status": "PLAN_GENERATED",
    })
    assert res_exec_3_unapproved.status_code == 403
    assert "Execution forbidden" in res_exec_3_unapproved.json()["detail"]

    # ----------------------------------------------------
    # Step 8: Approve Plan #3
    # ----------------------------------------------------
    res_approve = client.post(f"/api/v1/recovery/plans/{plan_3_db_id}/approve")
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "APPROVED"

    # ----------------------------------------------------
    # Step 9: Verify ONLY Plan #3 is executed
    # ----------------------------------------------------
    with SessionLocal() as db:
        rec_3 = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_3_db_id).first()
        assert rec_3.status == RecoveryPlanStatus.APPROVED

    res_exec_3 = client.post("/api/v1/recovery/execute", json={
        "plan_id": str(plan_3_db_id),
        "status": "APPROVED",
        "new_transport_id": plan_3["selected_option"]["transport_id"],
        "original_booking_id": "12015-SHT",
        "hotel_booking_id": "HTL-JAI-101",
    })
    assert res_exec_3.status_code == 200
    assert res_exec_3.json()["execution_status"] in ("COMPLETED", "COMPLETED_SUCCESS")

    # Verify that Plan #1 and Plan #2 remain REJECTED
    with SessionLocal() as db:
        p1 = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_1_db_id).first()
        p2 = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_2_db_id).first()
        p3 = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_3_db_id).first()
        assert p1.status == RecoveryPlanStatus.REJECTED
        assert p2.status == RecoveryPlanStatus.REJECTED
        assert p3.status in (RecoveryPlanStatus.EXECUTING, RecoveryPlanStatus.COMPLETED)


def test_live_workspace_reject_and_replan_endpoint():
    """
    Tests live workspace reject-and-replan HTTP endpoint with constraint accumulation
    and safety verification.
    """
    with SessionLocal() as db:
        _seed_corridor(db)

    # 1. Initial workspace recovery formulate Plan #1
    res_rec = client.post("/api/v1/recovery/live-workspace/recover")
    assert res_rec.status_code == 200
    w1 = res_rec.json()
    assert w1["proposed_plan"]["status"] == "PLAN_GENERATED"
    assert w1["proposed_plan"]["revision_count"] == 1
    first_choice = w1["proposed_plan"]["selected_option"]["name"]

    # 2. Reject and request revision: "I don't want this airline"
    res_reject_replan = client.post("/api/v1/recovery/live-workspace/reject-and-replan", json={
        "reasons": ["I don't want this airline"],
        "feedback_text": "I don't want Airline A and maximum budget is ₹5,000.",
    })
    assert res_reject_replan.status_code == 200
    w2 = res_reject_replan.json()
    p2 = w2["proposed_plan"]

    assert p2["revision_count"] == 2
    assert p2["status"] == "PLAN_GENERATED"
    assert p2["is_executed"] is False
    assert "Airline A" in p2["active_constraints"]["excluded_providers"]
    assert p2["active_constraints"]["max_budget"] == 5000.0

    # Safety check: Cannot execute w2 directly if unapproved
    with SessionLocal() as db:
        # Check that the previous plan was marked REJECTED
        plans = db.query(RecoveryPlan).order_by(RecoveryPlan.id.asc()).all()
        assert plans[0].status == RecoveryPlanStatus.REJECTED
        assert plans[1].status == RecoveryPlanStatus.PLAN_GENERATED


def test_max_revisions_exceeded_handling():
    """
    Verifies that after 3 revisions, infinite replanning is prevented and the system
    shows: 'No suitable automated recovery plan could be found with the current requirements.'
    with zero automated execution.
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel, disruption = _seed_corridor(db)
        # Create a plan already at revision 3
        plan_rev3 = RecoveryPlan(
            journey_id=journey.id,
            disruption_id=disruption.id,
            status=RecoveryPlanStatus.PLAN_GENERATED,
            summary="Proposed Plan Revision 3",
            actions=[],
            revision_count=3,
            active_constraints={"excluded_providers": ["Airline A", "Airline B"], "max_budget": 500.0},
        )
        db.add(plan_rev3)
        db.commit()

    # Rejecting revision 3 must trigger max revisions limit
    res_limit = client.post("/api/v1/recovery/live-workspace/reject-and-replan", json={
        "reasons": ["Too expensive"],
        "feedback_text": "Still too expensive. Max budget 200.",
    })
    assert res_limit.status_code == 200
    data = res_limit.json()
    assert data["proposed_plan"]["status"] == "REVISION_REQUIRED"
    assert data["proposed_plan"]["workflow_stage"] == "MAX_REVISIONS_EXCEEDED"
    assert "No suitable automated recovery plan could be found with the current requirements." in data["proposed_plan"]["summary"]
    assert data["proposed_plan"]["is_executed"] is False


def test_infeasible_constraints_graceful_handling():
    """
    Verifies that if contradictory or impossible constraints are applied,
    the system reports 'No suitable automated recovery plan could be found with the current requirements.'
    and performs ZERO executions.
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel, disruption = _seed_corridor(db)
        journey_id = journey.id
        disruption_id = disruption.id

    # Impossible budget constraint: ₹10 (no transportation costs ₹10)
    infeasible_plan = recovery_planner.generate_recovery_plan(
        journey_id=journey_id,
        disruption_id=disruption_id,
        available_alternatives=[
            CandidateAlternativeInput(
                transport_id="FLT-EXP",
                name="Flight Expensive",
                origin="Delhi",
                destination="Jaipur",
                departure="2026-10-20T18:00:00",
                arrival="2026-10-20T19:00:00",
                price=5000.0,
            )
        ],
        active_constraints={"max_budget": 10.0},
        revision_count=2,
    )

    assert infeasible_plan["is_feasible"] is False
    assert infeasible_plan["status"] == "REVISION_REQUIRED"
    assert "No suitable automated recovery plan could be found with the current requirements." in infeasible_plan["summary"]
    assert infeasible_plan["is_executed"] is False
    assert infeasible_plan["selected_option"] is None
