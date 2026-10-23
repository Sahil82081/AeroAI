"""
Tests for Strict Separation of Recovery Plan Generation from Recovery Plan Execution.

Verifies the 5 Core Requirements:
1. A disruption is detected.
2. A recovery plan is generated.
3. The plan is returned/stored with status PROPOSED.
4. Generating a recovery plan DOES NOT execute any actions:
   - Does NOT cancel any booking
   - Does NOT rebook any flight/train
   - Does NOT initiate a refund
   - Does NOT submit a claim
   - Does NOT send execution-related notifications
   - Does NOT perform any other real-world action
5. Existing execution functions still work when explicitly called.
"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.models import (
    User, Journey, Booking, BookingType, BookingStatus,
    Disruption, DisruptionType, DisruptionSeverity, DisruptionStatus,
    RecoveryPlan, RecoveryPlanStatus, Notification
)
from app.modules.recovery import recovery_planner, recovery_action_executor, IdempotencyAndAuditStore
from app.modules.suppliers.service import supplier_service
from app.modules.disruptions.disruption_engine import DisruptionSimulatorEngine
from app.schemas.disruption_schemas import DisruptionSimulationRequest

client = TestClient(app)


def _seed_test_journey(db):
    """Creates a fresh test journey with Flight -> Train -> Hotel."""
    db.query(Notification).delete()
    db.query(RecoveryPlan).delete()
    db.query(Disruption).delete()
    db.query(Booking).delete()
    db.query(Journey).delete()
    db.query(User).delete()
    db.commit()

    user = User(
        email="test_traveler@example.com",
        full_name="Test Traveler",
        hashed_password="mockpassword",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    journey = Journey(
        user_id=user.id,
        title="Delhi-Jaipur Test Corridor",
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
        reference_number="AI-202",
        title="Flight Mumbai -> Delhi (AI-202)",
        origin="Mumbai",
        destination="Delhi",
        start_time=base_time,
        end_time=base_time + timedelta(hours=2),  # 12:00
        price=3200.0,
        currency="INR",
        status=BookingStatus.CONFIRMED,
    )
    train = Booking(
        journey_id=journey.id,
        booking_type=BookingType.TRAIN,
        provider_name="Indian Railways",
        reference_number="12015-SHT",
        title="Ajmer Shatabdi Express (12015-SHT)",
        origin="Delhi",
        destination="Jaipur",
        start_time=base_time + timedelta(hours=3, minutes=30),  # 13:30
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
    db.refresh(journey)
    return user, journey, flight, train, hotel


def setup_function():
    supplier_service.reset_simulation_state()
    IdempotencyAndAuditStore.clear()
    client.post("/api/v1/events/reset")


def test_disruption_generates_plan_and_stops_without_execution():
    """
    Verification Requirement 1-4:
    1. A disruption is detected.
    2. A recovery plan is generated.
    3. The plan is returned/stored with status PROPOSED.
    4. NO execution action occurs (no cancellation, rebooking, refund, claim, or notifications).
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel = _seed_test_journey(db)
        flight_id = flight.id
        train_ref = train.reference_number
        journey_id = journey.id
        user_id = user.id

    # 1. Simulate disruption (4-hour delay on flight AI-202)
    impact = DisruptionSimulatorEngine.simulate_disruption(
        db=SessionLocal(),
        request=DisruptionSimulationRequest(
            booking_id=flight_id,
            type="flight_delay",
            delay_minutes=240,
            title="Air India AI-202 Delayed 4 Hours",
            description="Flight delayed 240 mins causing missed connection to 12015-SHT train.",
        ),
    )

    # Check 1: Disruption detected
    assert impact.severity == "CRITICAL"
    assert any(b.reference_number == train_ref and b.impact_nature == "MISSED_CONNECTION" for b in impact.affected_bookings)

    with SessionLocal() as db:
        # Check 2 & 3: Disruption recorded and proposed recovery plan stored with status PROPOSED
        disruption_rec = db.query(Disruption).filter(Disruption.journey_id == journey_id).first()
        assert disruption_rec is not None
        assert disruption_rec.status in (DisruptionStatus.DETECTED, DisruptionStatus.PLAN_GENERATED)

        plans = db.query(RecoveryPlan).filter(RecoveryPlan.journey_id == journey_id).all()
        assert len(plans) >= 1
        proposed_plan = plans[0]
        assert proposed_plan.status in (RecoveryPlanStatus.PLAN_GENERATED, RecoveryPlanStatus.PROPOSED)
        assert proposed_plan.actions is not None
        # Verify compiled actions in plan are labeled PROPOSED
        for act in proposed_plan.actions:
            assert act.get("status") in ("PROPOSED", "PLAN_GENERATED")

        # Check 4: VERIFY NO EXECUTION OCCURRED
        # A. Database bookings are NOT rebooked or cancelled by execution
        train_in_db = db.query(Booking).filter(Booking.reference_number == "12015-SHT").first()
        assert train_in_db is not None
        assert train_in_db.reference_number == "12015-SHT"  # Original booking reference preserved!
        # Alternative train (TRN124) was NOT inserted or rebooked into SQLite bookings
        assert db.query(Booking).filter(Booking.reference_number == "TRN124").first() is None

        # B. Audit store has 0 executed actions
        assert len(IdempotencyAndAuditStore.get_history()) == 0

        # C. Audit store confirms 0 actions were executed
        assert len(IdempotencyAndAuditStore.get_history()) == 0

        # D. No execution notifications exist in DB
        notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
        assert len(notifications) == 0


def test_live_workspace_recover_endpoint_pure_planning():
    """
    Verification: POST /api/v1/recovery/live-workspace/recover returns the proposed plan
    without executing actions, leaving bookings disrupted and execution_summary as None.
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel = _seed_test_journey(db)
        flight.status = BookingStatus.DELAYED
        flight.end_time = flight.end_time + timedelta(hours=4)
        train.status = BookingStatus.DELAYED
        db.commit()

    res = client.post("/api/v1/recovery/live-workspace/recover")
    assert res.status_code == 200
    data = res.json()

    # Plan is returned
    assert data["optimization_result"] is not None
    assert data["proposed_plan"] is not None
    assert data["proposed_plan"]["status"] in ("PLAN_GENERATED", "PROPOSED")
    assert data["proposed_plan"]["is_executed"] is False
    assert len(data["proposed_plan"]["actions"]) == 6

    # Execution summary is explicitly None (NOT executed)
    assert data["execution_summary"] is None
    assert data["recovery_details"]["status"] in ("PLAN_GENERATED", "PROPOSED")
    assert data["recovery_details"]["execution_status"] in ("AWAITING_APPROVAL", "AWAITING_HUMAN_APPROVAL")

    # Verify no execution occurred against suppliers or DB
    assert len(IdempotencyAndAuditStore.get_history()) == 0
    with SessionLocal() as db:
        # Train booking in DB is still 12015-SHT (not rebooked)
        orig_train = db.query(Booking).filter(Booking.reference_number == "12015-SHT").first()
        assert orig_train is not None
        assert db.query(Booking).filter(Booking.reference_number == "TRN124").first() is None


def test_explicit_execution_works_separately():
    """
    Verification Requirement 5: Existing execution functions still work when explicitly called.
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel = _seed_test_journey(db)
        flight.status = BookingStatus.DELAYED
        flight.end_time = flight.end_time + timedelta(hours=4)
        train.status = BookingStatus.DELAYED
        db.commit()

    # Step 1: Generate proposed recovery plan (planning stage)
    plan_res = client.post("/api/v1/recovery/live-workspace/recover")
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert plan_data["proposed_plan"]["status"] in ("PLAN_GENERATED", "PROPOSED")

    # Verify 0 actions executed prior to explicit execution call
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    # Step 2: Attempting to execute unapproved plan MUST be rejected with HTTP 403
    unapproved_res = client.post("/api/v1/recovery/live-workspace/execute")
    assert unapproved_res.status_code == 403
    assert "APPROVED" in unapproved_res.json()["detail"]
    assert len(IdempotencyAndAuditStore.get_history()) == 0  # 0 actions executed!

    # Step 3: Approve recovery plan via Human Approval Gate
    approve_res = client.post("/api/v1/recovery/live-workspace/approve")
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["proposed_plan"]["status"] == "APPROVED"
    assert len(IdempotencyAndAuditStore.get_history()) == 0  # Still 0 actions executed!

    # Step 4: Explicitly call execution via POST /api/v1/recovery/live-workspace/execute
    exec_res = client.post("/api/v1/recovery/live-workspace/execute")
    assert exec_res.status_code == 200
    exec_data = exec_res.json()

    # Verify execution succeeded
    assert exec_data["execution_summary"] is not None
    assert exec_data["execution_summary"]["execution_status"] in ("COMPLETED_SUCCESS", "SUCCESS")
    assert exec_data["recovery_details"]["status"] == "COMPLETED"

    # Verify actions were recorded in audit store
    assert len(IdempotencyAndAuditStore.get_history()) == 6
    audit_action_types = [a["action_type"] for a in IdempotencyAndAuditStore.get_history()]
    assert "cancel_booking" in audit_action_types
    assert "rebook_transportation" in audit_action_types
    assert "request_refund" in audit_action_types
    assert "modify_hotel_checkin" in audit_action_types
    assert "notify_traveler" in audit_action_types

    # Verify database bookings now reflect recovered state
    selected_tid = plan_data["proposed_plan"]["selected_option"]["transport_id"]
    with SessionLocal() as db:
        rebooked_train = db.query(Booking).filter(Booking.reference_number == selected_tid).first()
        assert rebooked_train is not None
        assert rebooked_train.status == BookingStatus.CONFIRMED

        completed_plan = db.query(RecoveryPlan).filter(RecoveryPlan.status == RecoveryPlanStatus.COMPLETED).first()
        assert completed_plan is not None


def test_human_approval_gate_blocks_unapproved_plan_execution():
    """
    Critical Safety Requirement:
    Backend strictly enforces that plan.status === APPROVED before executing anything.
    If an unapproved plan is sent, reject the request and perform ZERO execution actions:
    - PLAN_GENERATED -> execution forbidden (403)
    - REJECTED -> execution forbidden (403)
    - REVISION_REQUIRED -> execution forbidden (403)
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel = _seed_test_journey(db)
        flight.status = BookingStatus.DELAYED
        flight.end_time = flight.end_time + timedelta(hours=4)
        train.status = BookingStatus.DELAYED
        db.commit()

    # 1. Generate plan -> status PLAN_GENERATED
    plan_res = client.post("/api/v1/recovery/live-workspace/recover")
    assert plan_res.status_code == 200

    # 2. Direct execute must return 403 Forbidden
    res1 = client.post("/api/v1/recovery/live-workspace/execute")
    assert res1.status_code == 403
    assert "APPROVED" in res1.json()["detail"]
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    # 3. Reject plan -> status REJECTED
    reject_res = client.post("/api/v1/recovery/live-workspace/reject?reason=Needs+earlier+arrival")
    assert reject_res.status_code == 200
    assert reject_res.json()["proposed_plan"]["status"] == "REJECTED"

    # Direct execute on REJECTED plan must return 403 Forbidden
    res2 = client.post("/api/v1/recovery/live-workspace/execute")
    assert res2.status_code == 403
    assert "REJECTED" in res2.json()["detail"]
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    # 4. Direct API execution endpoint POST /api/v1/recovery/execute with unapproved status
    res3 = client.post("/api/v1/recovery/execute", json={
        "plan_id": "PLAN-UNAPPROVED-01",
        "status": "PLAN_GENERATED",
    })
    assert res3.status_code == 403
    assert "APPROVED" in res3.json()["detail"]
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    res4 = client.post("/api/v1/recovery/execute", json={
        "plan_id": "PLAN-REJECTED-02",
        "status": "REJECTED",
    })
    assert res4.status_code == 403
    assert "APPROVED" in res4.json()["detail"]
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    res5 = client.post("/api/v1/recovery/execute", json={
        "plan_id": "PLAN-REVISION-03",
        "status": "REVISION_REQUIRED",
    })
    assert res5.status_code == 403
    assert len(IdempotencyAndAuditStore.get_history()) == 0


def test_approve_and_execute_combined_workflow():
    """
    Tests the Approve & Execute combined flow:
    PLAN_GENERATED -> HUMAN_REVIEW -> APPROVED -> EXECUTING -> COMPLETED
    """
    with SessionLocal() as db:
        user, journey, flight, train, hotel = _seed_test_journey(db)
        flight.status = BookingStatus.DELAYED
        flight.end_time = flight.end_time + timedelta(hours=4)
        train.status = BookingStatus.DELAYED
        db.commit()

    # Step 1: Generate plan
    plan_res = client.post("/api/v1/recovery/live-workspace/recover")
    assert plan_res.status_code == 200
    assert plan_res.json()["proposed_plan"]["status"] in ("PLAN_GENERATED", "PROPOSED")
    assert len(IdempotencyAndAuditStore.get_history()) == 0

    # Step 2: Approve & Execute
    combined_res = client.post("/api/v1/recovery/live-workspace/approve-and-execute")
    assert combined_res.status_code == 200
    data = combined_res.json()

    assert data["recovery_details"]["status"] == "COMPLETED"
    assert data["execution_summary"]["execution_status"] in ("COMPLETED_SUCCESS", "SUCCESS")
    assert len(IdempotencyAndAuditStore.get_history()) == 6


def test_recovery_action_executor_standalone_execution():
    """
    Verification: RecoveryActionExecutor.execute_recovery_plan checks approval and executes when approved.
    """
    import pytest

    # Fails when plan status is unapproved
    with pytest.raises(ValueError, match="APPROVED"):
        recovery_action_executor.execute_recovery_plan(
            plan_input={
                "plan_id": "PLAN-FAIL-01",
                "status": "PLAN_GENERATED",
            }
        )

    # Succeeds when approved
    summary = recovery_action_executor.execute_recovery_plan(
        plan_input={
            "plan_id": "PLAN-DIRECT-EXEC-01",
            "status": "APPROVED",
            "original_booking_id": "12015-SHT",
            "original_transport_id": "TRN123",
            "original_price": 800.0,
            "new_transport_id": "TRN124",
            "hotel_booking_id": "HTL-JAI-101",
            "hotel_id": "HTL101",
            "new_check_in": "2026-10-20T21:30:00",
            "passenger_name": "Aarav Sharma",
            "traveler_email": "aarav.sharma@example.com",
            "contact_email": "frontdesk@heritagepalacejaipur.com",
        }
    )
    assert summary["execution_status"] == "COMPLETED_SUCCESS"
    assert summary["succeeded_count"] == 6
    assert len(summary["audit_records"]) == 6
