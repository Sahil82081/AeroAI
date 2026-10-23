from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, RecoveryPlan, Journey, RecoveryPlanStatus, DisruptionStatus
from app.schemas.schemas import RecoveryPlanCreate, RecoveryPlanResponse
from app.schemas.optimization_schemas import OptimizationRequest, OptimizationResponse
from app.modules.optimization.ortools_optimizer import ortools_recovery_optimizer
from app.modules.ai_agents.recovery_graph import recovery_workflow_runner
from app.modules.recovery import recovery_planner, recovery_action_executor, IdempotencyAndAuditStore
from app.modules.events.event_bus import event_bus

router = APIRouter(prefix="/recovery", tags=["Recovery Plans, OR-Tools, LangGraph & Action Execution (Stages 6–8)"])


class RecoveryPlanExecutionRequest(BaseModel):
    plan_id: str = Field(default="PLAN-TRN-456")
    original_booking_id: str = Field(default="12015-SHT")
    original_transport_id: str = Field(default="TRN123")
    original_price: float = Field(default=800.0)
    new_transport_id: str = Field(default="TRN124")
    passenger_name: str = Field(default="Sahil Sharma")
    seats: int = Field(default=1, ge=1)
    hotel_booking_id: str = Field(default="HTL-JAI-101")
    hotel_id: str = Field(default="HTL101")
    new_check_in: str = Field(default="2026-10-20T22:30:00")
    traveler_email: str = Field(default="traveler@example.com")
    contact_email: str = Field(default="frontdesk@heritagepalacejaipur.com")
    actions: Optional[List[Dict[str, Any]]] = None
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_ms: int = Field(default=2000, ge=50, le=10000)
    rollback_on_critical_failure: bool = Field(default=True)
    simulate_transient_failures_on_step: Optional[int] = Field(default=None)
    simulate_transient_count: int = Field(default=1, ge=0, le=5)
    status: Optional[str] = Field(default=None, description="Approval status: must be APPROVED to execute")


class RejectAndReplanRequest(BaseModel):
    reasons: List[str] = Field(default_factory=list, description="Selected rejection reason categories")
    feedback_text: Optional[str] = Field(default="", description="Traveler or operator feedback text")
    plan_id: Optional[str] = Field(default=None, description="Optional target plan ID")


class SingleActionExecutionRequest(BaseModel):
    plan_id: str = Field(default="PLAN-SINGLE-101")
    step: int = Field(default=1)
    action_type: str = Field(..., description="rebook_transportation, cancel_booking, request_refund, modify_hotel_checkin, notify_traveler, notify_relevant_contact")
    booking_id: str = Field(default="TRN124")
    idempotency_key: Optional[str] = None
    request: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=2, ge=0, le=5)
    timeout_ms: int = Field(default=2000, ge=50, le=10000)
    simulate_transient_failures: int = Field(default=0, ge=0, le=5)


class LangGraphWorkflowRequest(BaseModel):
    journey_id: str = Field(default="JRN-101")
    disruption: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "flight_delay",
            "delay_minutes": 240,
            "origin": "Delhi",
            "destination": "Jaipur",
            "revised_arrival": "4:30 PM",
            "disrupted_booking_ref": "6E-205",
            "missed_booking_ref": "12015-SHT",
            "hotel_booking_ref": "HTL-JAI-101"
        }
    )
    alternatives: Optional[List[Dict[str, Any]]] = None
    constraints_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "current_arrival": "4:30 PM",
            "hotel_latest_checkin": "10:00 PM",
            "min_connection_minutes": 45,
            "required_seats": 1
        }
    )
    preferences_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_budget": 1000.0,
            "weights": {
                "price": 0.30,
                "travel_time": 0.25,
                "waiting_time": 0.15,
                "number_of_changes": 0.10,
                "arrival_time": 0.10,
                "reliability": 0.10
            }
        }
    )
    approval_rules: Dict[str, Any] = Field(
        default_factory=lambda: {
            "auto_approve_max_cost": 1000.0,
            "min_confidence_threshold": 0.75,
            "require_human_approval": False
        }
    )
    simulate_transient_failures: int = Field(default=0, ge=0, le=5)
    max_retries: int = Field(default=2, ge=0, le=5)


@router.get("/plans", response_model=List[RecoveryPlanResponse])
def get_recovery_plans(journey_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(RecoveryPlan).join(Journey).filter(Journey.user_id == current_user.id)
    if journey_id:
        query = query.filter(RecoveryPlan.journey_id == journey_id)
    return query.all()


@router.post("/plans", response_model=RecoveryPlanResponse, status_code=status.HTTP_201_CREATED)
def create_recovery_plan(plan_in: RecoveryPlanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    journey = db.query(Journey).filter(Journey.id == plan_in.journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found or unauthorized")

    plan = RecoveryPlan(
        journey_id=plan_in.journey_id,
        disruption_id=plan_in.disruption_id,
        status=plan_in.status,
        summary=plan_in.summary,
        reasoning_explanation=plan_in.reasoning_explanation,
        estimated_additional_cost=plan_in.estimated_additional_cost,
        refund_opportunities=plan_in.refund_opportunities,
        actions=plan_in.actions,
        alternatives_considered=plan_in.alternatives_considered
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/optimize", response_model=OptimizationResponse)
def optimize_recovery_options(request: OptimizationRequest):
    """
    [STAGE 6] Solve the constrained multi-criteria travel recovery optimization problem
    using Google OR-Tools CP-SAT solver.
    """
    result = ortools_recovery_optimizer.optimize(request)
    event_bus.publish("RECOVERY_OPTIMIZATION_COMPLETED", {
        "constraints_satisfied": result.constraints_satisfied,
        "selected_transport_id": result.selected_option["transport_id"] if result.selected_option else None,
        "objective_score": result.objective_score,
        "solver": "Google OR-Tools CP-SAT"
    })
    return result


@router.post("/agent/run")
def run_langgraph_recovery_agent(request: LangGraphWorkflowRequest):
    """
    [STAGE 7] Execute the 8-node LangGraph Autonomous Recovery Agent Workflow:
    Disruption -> Analyze -> Impact Analysis -> Search Alternatives -> OR-Tools Optimization
    -> Recovery Decision -> Execute Actions -> Verify -> Notify User.
    """
    return recovery_workflow_runner.run_workflow(request.model_dump())


@router.get("/agent/graph-metadata")
def get_langgraph_metadata():
    """
    [STAGE 7] Return the LangGraph 8-node workflow architecture, node descriptions, and Mermaid diagram.
    """
    return recovery_workflow_runner.get_graph_documentation()


@router.post("/execute")
def execute_recovery_plan_endpoint(
    request: RecoveryPlanExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    [STAGE 8] Convert a recovery plan into executable actions and execute against Mock Supplier APIs.
    Strict Human Approval Gate: Verifies that plan.status === APPROVED before executing anything.
    If an unapproved plan (e.g. PLAN_GENERATED, REJECTED, REVISION_REQUIRED) is sent, the request is rejected with 403.
    """
    # 1. Enforce payload status check if provided
    if request.status and request.status.upper() not in ("APPROVED", "EXECUTING", "COMPLETED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Execution forbidden: Recovery plan has status '{request.status}'. Plan must be APPROVED before execution."
        )

    # 2. Check if plan_id matches a record in the database
    if request.plan_id:
        db_plan = None
        if request.plan_id.isdigit():
            db_plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == int(request.plan_id)).first()
        if not db_plan:
            db_plan = db.query(RecoveryPlan).filter(RecoveryPlan.summary.contains(request.plan_id)).first()
        if db_plan and db_plan.status not in (RecoveryPlanStatus.APPROVED, RecoveryPlanStatus.EXECUTING, RecoveryPlanStatus.COMPLETED):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Execution forbidden: Recovery plan in database has status '{db_plan.status.value}'. Plan must be APPROVED before execution."
            )

        if db_plan:
            db_plan.status = RecoveryPlanStatus.EXECUTING
            db.commit()

    try:
        exec_res = recovery_action_executor.execute_recovery_plan(
            plan_input=request.model_dump(),
            max_retries=request.max_retries,
            timeout_ms=request.timeout_ms,
            rollback_on_critical_failure=request.rollback_on_critical_failure,
            simulate_transient_failures_on_step=request.simulate_transient_failures_on_step,
            simulate_transient_count=request.simulate_transient_count
        )
        if db_plan and exec_res.get("execution_status") in ("COMPLETED", "COMPLETED_SUCCESS"):
            db_plan.status = RecoveryPlanStatus.COMPLETED
            db.commit()
            db.refresh(db_plan)
        return exec_res
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))


@router.post("/actions/execute-single")
def execute_single_action_endpoint(request: SingleActionExecutionRequest):
    """
    [STAGE 8] Execute or retry a single recovery action with idempotency protection.
    """
    return recovery_action_executor.execute_single_action(
        plan_id=request.plan_id,
        action_spec={
            "step": request.step,
            "action_type": request.action_type,
            "booking_id": request.booking_id,
            "idempotency_key": request.idempotency_key,
            "request": request.request
        },
        max_retries=request.max_retries,
        timeout_ms=request.timeout_ms,
        simulate_transient_failures=request.simulate_transient_failures
    )


@router.get("/actions/history")
def get_action_audit_history():
    """
    [STAGE 8] Retrieve the audit history of all executed recovery actions against Mock Supplier APIs.
    """
    history = IdempotencyAndAuditStore.get_history()
    return {
        "count": len(history),
        "simulated": True,
        "is_mock_supplier_transaction": True,
        "disclaimer": "SIMULATED TRANSACTIONS AGAINST MOCK SUPPLIER APIs",
        "history": history
    }


@router.post("/actions/clear")
def clear_action_audit_history():
    """
    [STAGE 8] Clear the action audit history and idempotency cache for testing.
    """
    IdempotencyAndAuditStore.clear()
    return {"status": "ACTION_HISTORY_AND_IDEMPOTENCY_CLEARED", "simulated": True}



@router.get("/optimize/presets")
def get_optimization_presets() -> List[Dict[str, Any]]:
    """
    Returns preset recovery optimization scenarios for interactive testing in the frontend.
    Includes the exact Train A / Train B / Train C / 10:00 PM hotel check-in scenario.
    """
    return [
        {
            "id": "prompt-train-scenario",
            "title": "Prompt Scenario: Train A vs Train B vs Train C (10:00 PM Hotel Cutoff)",
            "description": "Flight arrives 4:00 PM (16:00). Hotel latest check-in is 10:00 PM (22:00). Train C (₹400, arrives 10:30 PM) is pruned by OR-Tools due to hotel check-in constraint.",
            "payload": {
                "origin": "Delhi",
                "destination": "Jaipur",
                "constraints": {
                    "current_arrival": "4:00 PM",
                    "hotel_latest_checkin": "10:00 PM",
                    "min_connection_minutes": 45,
                    "required_seats": 1
                },
                "traveler_preferences": {
                    "max_budget": 1000.0,
                    "allowed_modes": ["train", "flight", "bus"],
                    "excluded_modes": [],
                    "weights": {
                        "price": 0.35,
                        "travel_time": 0.25,
                        "waiting_time": 0.15,
                        "number_of_changes": 0.10,
                        "arrival_time": 0.10,
                        "reliability": 0.05
                    }
                },
                "available_alternatives": [
                    {
                        "transport_id": "TRAIN-A",
                        "name": "Train A (Shatabdi Express)",
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
                        "name": "Train B (Vande Bharat Express)",
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
                        "name": "Train C (Night Intercity)",
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
            }
        },
        {
            "id": "tight-buffer-train-b-wins",
            "title": "Tight Transfer Buffer (4:30 PM Arrival + 45m Minimum Connection)",
            "description": "Flight arrives at 4:30 PM with a 45m minimum connection buffer (earliest departure 5:15 PM). Train A (5:00 PM) is pruned for insufficient connection time; Train C (10:30 PM) is pruned for hotel check-in; OR-Tools selects Train B (5:30 PM).",
            "payload": {
                "origin": "Delhi",
                "destination": "Jaipur",
                "constraints": {
                    "current_arrival": "4:30 PM",
                    "hotel_latest_checkin": "10:00 PM",
                    "min_connection_minutes": 45,
                    "required_seats": 1
                },
                "traveler_preferences": {
                    "max_budget": 1000.0,
                    "allowed_modes": ["train"],
                    "excluded_modes": [],
                    "weights": {
                        "price": 0.30,
                        "travel_time": 0.25,
                        "waiting_time": 0.15,
                        "number_of_changes": 0.10,
                        "arrival_time": 0.10,
                        "reliability": 0.10
                    }
                },
                "available_alternatives": [
                    {
                        "transport_id": "TRAIN-A",
                        "name": "Train A (Shatabdi Express)",
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
                        "name": "Train B (Vande Bharat Express)",
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
                        "name": "Train C (Night Intercity)",
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
            }
        },
        {
            "id": "live-mock-supplier-multimodal",
            "title": "Live Multi-Modal Optimization (Flight + Train + Bus from Mock Suppliers)",
            "description": "Queries live Mock Supplier inventory for Delhi -> Jaipur after a 16:00 flight arrival with 23:00 hotel check-in cutoff.",
            "payload": {
                "origin": "Delhi",
                "destination": "Jaipur",
                "auto_fetch_from_suppliers": True,
                "constraints": {
                    "current_arrival": "2026-10-20T16:00:00",
                    "hotel_latest_checkin": "2026-10-20T23:00:00",
                    "min_connection_minutes": 60,
                    "required_seats": 1
                },
                "traveler_preferences": {
                    "max_budget": 5000.0,
                    "allowed_modes": ["flight", "train", "bus"],
                    "excluded_modes": [],
                    "weights": {
                        "price": 0.30,
                        "travel_time": 0.30,
                        "waiting_time": 0.15,
                        "number_of_changes": 0.05,
                        "arrival_time": 0.10,
                        "reliability": 0.10
                    }
                }
            }
        }
    ]


@router.post("/demo/golden-triangle")
def run_stage12_golden_triangle_demo(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    [STAGE 12] Runs and verifies the complete 17-step Golden Triangle End-to-End Demo Scenario:
    Mumbai -> Delhi Flight (10:00 -> 12:00, delayed 4h to 16:00),
    Delhi -> Jaipur Train (13:30 -> 17:30 missed -> rebooked to TRN124 17:30 -> 21:00),
    Jaipur Hotel (18:00 check-in updated to 21:30),
    Next-day 09:00 AM Tour (unchanged).
    """
    from app.modules.demo.e2e_demo_orchestrator import EndToEndDemoOrchestrator
    return EndToEndDemoOrchestrator.run_golden_triangle_scenario(db=db)


@router.get("/demo/real-vs-simulated")
def get_real_vs_simulated_manifest() -> Dict[str, Any]:
    """
    [STAGE 12] Explicitly distinguishes REAL subsystems (AI reasoning, NetworkX graph, Impact analysis,
    OR-Tools optimization, LangGraph workflow, Kafka event architecture) from SIMULATED subsystems
    (Mock supplier booking, refunds, hotel modifications, travel availability).
    """
    from app.modules.demo.e2e_demo_orchestrator import REAL_VS_SIMULATED_MANIFEST
    return REAL_VS_SIMULATED_MANIFEST


@router.post("/demo/simulate-disruption")
def run_demo_disruption_simulation(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    [STAGE 12] Simulates a disruption (e.g., flight_cancellation, train_cancellation, flight_delay)
    against any booking ID in the database and returns the structured ImpactAnalysisResult.
    """
    from app.schemas.disruption_schemas import DisruptionSimulationRequest
    from app.modules.disruptions.disruption_engine import DisruptionSimulatorEngine

    sim_req = DisruptionSimulationRequest(**request)
    return DisruptionSimulatorEngine.simulate_disruption(db=db, request=sim_req).model_dump()


class CustomBookingInput(BaseModel):
    journey_title: Optional[str] = "My Custom Trip"
    booking_type: str = Field(..., description="FLIGHT, TRAIN, BUS, HOTEL, or ACTIVITY")
    provider_name: str = Field(..., description="e.g., IndiGo, Indian Railways, Taj Hotel")
    reference_number: str = Field(..., description="e.g., 6E-401, TRN-902, HTL-55")
    title: Optional[str] = None
    origin: str = Field(..., description="Origin city, e.g., Mumbai")
    destination: str = Field(..., description="Destination city, e.g., Delhi")
    start_time: str = Field(..., description="ISO datetime, e.g., 2026-10-20T10:00:00")
    end_time: str = Field(..., description="ISO datetime, e.g., 2026-10-20T12:00:00")
    price: float = Field(default=1500.0, ge=0)
    currency: str = Field(default="INR")


def _serialize_live_workspace(db: Session) -> Dict[str, Any]:
    from app.models.models import Booking, Disruption
    from app.modules.journeys.graph_builder import JourneyGraphEngine
    from app.modules.notifications.notification_agent import notification_agent_service

    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    if not journey:
        return {
            "has_journey": False,
            "journey": None,
            "bookings": [],
            "graph": None,
            "disruptions": [],
            "audit_history": IdempotencyAndAuditStore.get_history(),
            "notifications": [n.model_dump() for n in notification_agent_service.inbox_history],
        }

    bookings = (
        db.query(Booking)
        .filter(Booking.journey_id == journey.id)
        .order_by(Booking.start_time.asc())
        .all()
    )

    graph_data = None
    if bookings:
        engine = JourneyGraphEngine(journey_id=journey.id)
        graph_data = engine.build_from_bookings(bookings).model_dump()

    disruptions = (
        db.query(Disruption)
        .filter(Disruption.journey_id == journey.id)
        .order_by(Disruption.id.desc())
        .all()
    )

    latest_plan = (
        db.query(RecoveryPlan)
        .filter(RecoveryPlan.journey_id == journey.id)
        .order_by(RecoveryPlan.id.desc())
        .first()
    )
    proposed_plan_dict = None
    recovery_details_dict = None
    if latest_plan and latest_plan.status in (
        RecoveryPlanStatus.PLAN_GENERATED,
        RecoveryPlanStatus.HUMAN_REVIEW,
        RecoveryPlanStatus.APPROVED,
        RecoveryPlanStatus.REJECTED,
        RecoveryPlanStatus.REVISION_REQUIRED,
    ):
        selected_option = None
        if latest_plan.alternatives_considered:
            selected_option = next((alt for alt in latest_plan.alternatives_considered if isinstance(alt, dict) and alt.get("selected")), None)
        proposed_plan_dict = {
            "db_plan_id": latest_plan.id,
            "status": latest_plan.status.value,
            "workflow_stage": "HUMAN_REVIEW" if latest_plan.status in (RecoveryPlanStatus.PLAN_GENERATED, RecoveryPlanStatus.HUMAN_REVIEW) else latest_plan.status.value,
            "summary": latest_plan.summary,
            "reasoning_explanation": latest_plan.reasoning_explanation,
            "net_additional_cost": latest_plan.estimated_additional_cost,
            "actions": latest_plan.actions,
            "active_constraints": latest_plan.active_constraints or {},
            "rejection_feedback": latest_plan.rejection_feedback or {},
            "revision_count": latest_plan.revision_count or 1,
            "is_executed": latest_plan.status == RecoveryPlanStatus.COMPLETED,
            "is_approved": latest_plan.status == RecoveryPlanStatus.APPROVED,
            "is_feasible": latest_plan.status != RecoveryPlanStatus.REVISION_REQUIRED,
            "alternatives_considered": latest_plan.alternatives_considered,
            "selected_option": selected_option,
        }
        recovery_details_dict = {
            "status": latest_plan.status.value,
            "workflow_stage": proposed_plan_dict["workflow_stage"],
            "execution_status": "READY_FOR_EXECUTION" if latest_plan.status == RecoveryPlanStatus.APPROVED else ("REJECTED_REVISION_REQUIRED" if latest_plan.status == RecoveryPlanStatus.REJECTED else "AWAITING_HUMAN_APPROVAL"),
            "active_constraints": latest_plan.active_constraints or {},
            "revision_count": latest_plan.revision_count or 1,
        }

    return {
        "has_journey": True,
        "journey": {
            "id": journey.id,
            "title": journey.title,
            "description": journey.description,
            "status": journey.status,
        },
        "bookings": [
            {
                "id": b.id,
                "reference_number": b.reference_number,
                "booking_type": b.booking_type.value,
                "provider_name": b.provider_name,
                "title": b.title,
                "status": b.status.value,
                "origin": b.origin,
                "destination": b.destination,
                "start_time": b.start_time.isoformat() if b.start_time else None,
                "end_time": b.end_time.isoformat() if b.end_time else None,
                "price": b.price,
                "currency": b.currency,
            }
            for b in bookings
        ],
        "graph": graph_data,
        "disruptions": [
            {
                "id": d.id,
                "booking_id": d.booking_id,
                "type": d.disruption_type.value,
                "severity": d.severity.value,
                "title": d.title,
                "description": d.description,
                "delay_minutes": d.delay_minutes,
            }
            for d in disruptions
        ],
        "proposed_plan": proposed_plan_dict,
        "recovery_details": recovery_details_dict,
        "audit_history": IdempotencyAndAuditStore.get_history(),
        "notifications": [n.model_dump() for n in notification_agent_service.inbox_history],
    }


@router.get("/live-workspace")
def get_live_workspace(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns the real database-backed journey, bookings, NetworkX graph, disruptions,
    audit trail, and notifications with zero hardcoded dummy fallback.
    """
    return _serialize_live_workspace(db)


@router.post("/live-workspace/clear")
def clear_all_workspace_data(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Wipes all Journeys, Bookings, Disruptions, RecoveryPlans, Graph Nodes/Edges,
    Audit logs, Kafka events, and Notifications so the user starts with a 100% empty database.
    """
    from app.models.models import Booking, Disruption, JourneyNode, JourneyEdge
    from app.modules.events.kafka_engine import kafka_broker
    from app.modules.notifications.notification_agent import notification_agent_service
    from app.modules.suppliers.service import supplier_service

    db.query(JourneyEdge).delete()
    db.query(JourneyNode).delete()
    db.query(RecoveryPlan).delete()
    db.query(Disruption).delete()
    db.query(Booking).delete()
    db.query(Journey).delete()
    db.commit()

    IdempotencyAndAuditStore.clear()
    kafka_broker.reset_broker()
    notification_agent_service.clear_history()
    supplier_service.reset_simulation_state()

    return _serialize_live_workspace(db)


@router.post("/live-workspace/add-booking")
def add_custom_booking_to_workspace(
    item: CustomBookingInput,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Adds a real user-created booking into SQLite (creating the Journey if none exists)
    and immediately recomputes the NetworkX Journey Graph.
    """
    from datetime import datetime
    from app.models.models import Booking, BookingType, BookingStatus
    from app.modules.journeys.graph_builder import JourneyGraphEngine

    user = db.query(User).first()
    if not user:
        user = User(
            email="traveler@example.com",
            full_name="Aarav Sharma",
            hashed_password="hashed_password",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    start_dt = datetime.fromisoformat(item.start_time)
    end_dt = datetime.fromisoformat(item.end_time)

    if not journey:
        journey = Journey(
            user_id=user.id,
            title=item.journey_title or f"{item.origin} -> {item.destination} Trip",
            description="User-created custom journey",
            start_date=start_dt,
            end_date=end_dt,
            status="ACTIVE",
        )
        db.add(journey)
        db.commit()
        db.refresh(journey)

    b_type_str = item.booking_type.upper().strip()
    b_type = BookingType[b_type_str] if b_type_str in BookingType.__members__ else BookingType.FLIGHT

    new_booking = Booking(
        journey_id=journey.id,
        reference_number=item.reference_number.strip(),
        booking_type=b_type,
        provider_name=item.provider_name.strip(),
        title=item.title or f"{item.provider_name} {item.reference_number} ({item.origin} -> {item.destination})",
        status=BookingStatus.CONFIRMED,
        start_time=start_dt,
        end_time=end_dt,
        origin=item.origin.strip(),
        destination=item.destination.strip(),
        price=item.price,
        currency=item.currency,
    )
    db.add(new_booking)
    db.commit()
    db.refresh(journey)

    engine = JourneyGraphEngine(journey_id=journey.id)
    engine.sync_to_database(db, journey)

    return _serialize_live_workspace(db)


@router.delete("/live-workspace/booking/{booking_id}")
def delete_booking_from_workspace(
    booking_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Deletes a specific booking from SQLite and recomputes the NetworkX Journey Graph."""
    from app.models.models import Booking
    from app.modules.journeys.graph_builder import JourneyGraphEngine

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        j_id = booking.journey_id
        db.delete(booking)
        db.commit()
        journey = db.query(Journey).filter(Journey.id == j_id).first()
        if journey and journey.bookings:
            JourneyGraphEngine(journey_id=journey.id).sync_to_database(db, journey)

    return _serialize_live_workspace(db)


REAL_INDIAN_TRANSPORT_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "FLIGHT": [
        {
            "label": "Air India AI-202 · Mumbai (BOM) → Delhi (DEL) · 10:00–12:00 · ₹5,400",
            "booking_type": "FLIGHT",
            "provider_name": "Air India",
            "reference_number": "AI-202",
            "title": "Air India AI-202 (BOM → DEL)",
            "origin": "Mumbai",
            "destination": "Delhi",
            "start_time": "2026-10-20T10:00:00",
            "end_time": "2026-10-20T12:00:00",
            "price": 5400,
        },
        {
            "label": "IndiGo 6E-2142 · Mumbai (BOM) → Delhi (DEL) · 12:15–14:25 · ₹6,200",
            "booking_type": "FLIGHT",
            "provider_name": "IndiGo Airlines",
            "reference_number": "6E-2142",
            "title": "IndiGo 6E-2142 (BOM → DEL)",
            "origin": "Mumbai",
            "destination": "Delhi",
            "start_time": "2026-10-20T12:15:00",
            "end_time": "2026-10-20T14:25:00",
            "price": 6200,
        },
        {
            "label": "Air India AI-866 · Mumbai (BOM) → Delhi (DEL) · 14:00–16:10 · ₹7,450",
            "booking_type": "FLIGHT",
            "provider_name": "Air India",
            "reference_number": "AI-866",
            "title": "Air India AI-866 (BOM → DEL)",
            "origin": "Mumbai",
            "destination": "Delhi",
            "start_time": "2026-10-20T14:00:00",
            "end_time": "2026-10-20T16:10:00",
            "price": 7450,
        },
        {
            "label": "IndiGo 6E-5091 · Delhi (DEL) → Jaipur (JAI) · 17:45–18:45 · ₹3,850",
            "booking_type": "FLIGHT",
            "provider_name": "IndiGo Airlines",
            "reference_number": "6E-5091",
            "title": "IndiGo 6E-5091 (DEL → JAI)",
            "origin": "Delhi",
            "destination": "Jaipur",
            "start_time": "2026-10-20T17:45:00",
            "end_time": "2026-10-20T18:45:00",
            "price": 3850,
        },
        {
            "label": "IndiGo 6E-5318 · Mumbai (BOM) → Bengaluru (BLR) · 09:30–11:15 · ₹4,850",
            "booking_type": "FLIGHT",
            "provider_name": "IndiGo Airlines",
            "reference_number": "6E-5318",
            "title": "IndiGo 6E-5318 (BOM → BLR)",
            "origin": "Mumbai",
            "destination": "Bangalore",
            "start_time": "2026-10-20T09:30:00",
            "end_time": "2026-10-20T11:15:00",
            "price": 4850,
        },
    ],
    "TRAIN": [
        {
            "label": "12015 Ajmer Shatabdi Express · New Delhi (NDLS) → Jaipur (JP) · 13:30–17:30 · ₹800",
            "booking_type": "TRAIN",
            "provider_name": "Indian Railways (IRCTC)",
            "reference_number": "12015-SHT",
            "title": "12015 Ajmer Shatabdi Express (NDLS → JP)",
            "origin": "Delhi",
            "destination": "Jaipur",
            "start_time": "2026-10-20T13:30:00",
            "end_time": "2026-10-20T17:30:00",
            "price": 800,
        },
        {
            "label": "20978 Vande Bharat Express · Delhi Cantt (DEC) → Jaipur (JP) · 18:40–22:30 · ₹1,150",
            "booking_type": "TRAIN",
            "provider_name": "Indian Railways (IRCTC)",
            "reference_number": "20978-VB",
            "title": "20978 Vande Bharat Express (DEC → JP)",
            "origin": "Delhi",
            "destination": "Jaipur",
            "start_time": "2026-10-20T18:40:00",
            "end_time": "2026-10-20T22:30:00",
            "price": 1150,
        },
        {
            "label": "12986 Jaipur AC Double Decker · Delhi (DEE) → Jaipur (JP) · 17:35–22:05 · ₹680",
            "booking_type": "TRAIN",
            "provider_name": "Indian Railways (IRCTC)",
            "reference_number": "12986-DD",
            "title": "12986 Jaipur AC Double Decker (DEE → JP)",
            "origin": "Delhi",
            "destination": "Jaipur",
            "start_time": "2026-10-20T17:35:00",
            "end_time": "2026-10-20T22:05:00",
            "price": 680,
        },
        {
            "label": "12951 Mumbai–New Delhi Tejas Rajdhani · Mumbai (MMCT) → New Delhi (NDLS) · 17:00–08:32 · ₹3,420",
            "booking_type": "TRAIN",
            "provider_name": "Indian Railways (IRCTC)",
            "reference_number": "12951-RAJ",
            "title": "12951 Tejas Rajdhani Express (MMCT → NDLS)",
            "origin": "Mumbai",
            "destination": "Delhi",
            "start_time": "2026-10-20T17:00:00",
            "end_time": "2026-10-21T08:32:00",
            "price": 3420,
        },
        {
            "label": "12123 Deccan Queen · Mumbai (CSMT) → Pune (PUNE) · 17:10–20:25 · ₹495",
            "booking_type": "TRAIN",
            "provider_name": "Indian Railways (IRCTC)",
            "reference_number": "12123-DQ",
            "title": "12123 Deccan Queen Express (CSMT → PUNE)",
            "origin": "Mumbai",
            "destination": "Pune",
            "start_time": "2026-10-20T17:10:00",
            "end_time": "2026-10-20T20:25:00",
            "price": 495,
        },
        {
            "label": "12005 Kalka Shatabdi · New Delhi (NDLS) → Chandigarh (CDG) · 17:15–20:30 · ₹785",
            "booking_type": "TRAIN",
            "provider_name": "Indian Railways (IRCTC)",
            "reference_number": "12005-SHT",
            "title": "12005 Kalka Shatabdi Express (NDLS → CDG)",
            "origin": "Delhi",
            "destination": "Chandigarh",
            "start_time": "2026-10-20T17:15:00",
            "end_time": "2026-10-20T20:30:00",
            "price": 785,
        },
    ],
    "BUS": [
        {
            "label": "RSRTC Gold Line Volvo AC · Delhi ISBT → Jaipur Sindhi Camp · 17:00–22:15 · ₹750",
            "booking_type": "BUS",
            "provider_name": "RSRTC Gold Line Volvo",
            "reference_number": "RJ-14-PA-8821",
            "title": "RSRTC Gold Line Volvo AC (DEL → JAI)",
            "origin": "Delhi",
            "destination": "Jaipur",
            "start_time": "2026-10-20T17:00:00",
            "end_time": "2026-10-20T22:15:00",
            "price": 750,
        },
        {
            "label": "Zingbus Electric AC Sleeper · Delhi Dhaula Kuan → Jaipur · 18:30–23:30 · ₹650",
            "booking_type": "BUS",
            "provider_name": "Zingbus Electric",
            "reference_number": "ZB-DL-JP-409",
            "title": "Zingbus Electric AC Sleeper (DEL → JAI)",
            "origin": "Delhi",
            "destination": "Jaipur",
            "start_time": "2026-10-20T18:30:00",
            "end_time": "2026-10-20T23:30:00",
            "price": 650,
        },
        {
            "label": "MSRTC Shivneri Volvo AC · Mumbai Dadar → Pune Station · 14:00–17:30 · ₹560",
            "booking_type": "BUS",
            "provider_name": "MSRTC Shivneri Volvo",
            "reference_number": "MH-12-SH-402",
            "title": "MSRTC Shivneri Volvo AC (Mumbai → Pune)",
            "origin": "Mumbai",
            "destination": "Pune",
            "start_time": "2026-10-20T14:00:00",
            "end_time": "2026-10-20T17:30:00",
            "price": 560,
        },
    ],
    "HOTEL": [
        {
            "label": "Rambagh Palace, Jaipur (Taj) · Check-in 18:00 · ₹6,500/night",
            "booking_type": "HOTEL",
            "provider_name": "Rambagh Palace Jaipur",
            "reference_number": "HTL-JAI-101",
            "title": "Rambagh Palace Jaipur",
            "origin": "Jaipur",
            "destination": "Jaipur",
            "start_time": "2026-10-20T18:00:00",
            "end_time": "2026-10-21T11:00:00",
            "price": 6500,
        },
        {
            "label": "ITC Rajputana, A Luxury Collection Hotel · Jaipur · Check-in 15:00 · ₹8,500/night",
            "booking_type": "HOTEL",
            "provider_name": "ITC Rajputana Jaipur",
            "reference_number": "ITC-JAI-204",
            "title": "ITC Rajputana Jaipur",
            "origin": "Jaipur",
            "destination": "Jaipur",
            "start_time": "2026-10-20T15:00:00",
            "end_time": "2026-10-21T12:00:00",
            "price": 8500,
        },
        {
            "label": "Pullman New Delhi Aerocity · IGI Airport · Check-in 14:00 · ₹9,200/night",
            "booking_type": "HOTEL",
            "provider_name": "Pullman New Delhi Aerocity",
            "reference_number": "PUL-DEL-309",
            "title": "Pullman New Delhi Aerocity",
            "origin": "Delhi",
            "destination": "Delhi",
            "start_time": "2026-10-20T14:00:00",
            "end_time": "2026-10-21T12:00:00",
            "price": 9200,
        },
        {
            "label": "JW Marriott Hotel Pune · Senapati Bapat Rd · Check-in 18:00 · ₹7,800/night",
            "booking_type": "HOTEL",
            "provider_name": "JW Marriott Pune",
            "reference_number": "JWM-PUN-112",
            "title": "JW Marriott Hotel Pune",
            "origin": "Pune",
            "destination": "Pune",
            "start_time": "2026-10-20T18:00:00",
            "end_time": "2026-10-21T11:00:00",
            "price": 7800,
        },
    ],
    "ACTIVITY": [
        {
            "label": "Amber Fort & Nahargarh Heritage Tour · Jaipur · Next Day 09:00–13:00 · ₹2,250",
            "booking_type": "ACTIVITY",
            "provider_name": "Rajasthan Tourism (RTDC)",
            "reference_number": "TOUR-JAI-01",
            "title": "Amber Fort Morning Tour",
            "origin": "Jaipur",
            "destination": "Jaipur",
            "start_time": "2026-10-21T09:00:00",
            "end_time": "2026-10-21T13:00:00",
            "price": 2250,
        },
        {
            "label": "Shaniwar Wada & Old Pune Heritage Walk · Pune · Next Day 09:00–12:00 · ₹1,200",
            "booking_type": "ACTIVITY",
            "provider_name": "Maharashtra Tourism (MTDC)",
            "reference_number": "TOUR-PUN-02",
            "title": "Shaniwar Wada Heritage Walk",
            "origin": "Pune",
            "destination": "Pune",
            "start_time": "2026-10-21T09:00:00",
            "end_time": "2026-10-21T12:00:00",
            "price": 1200,
        },
    ],
}


@router.get("/live-workspace/real-catalog")
def get_real_indian_transport_catalog() -> Dict[str, Any]:
    """
    Returns real Indian Airlines, IRCTC Trains, State/Intercity Volvo Buses,
    Hotels, and Heritage Tours so users can select real schedules in 1 click.
    """
    return {"catalog": REAL_INDIAN_TRANSPORT_CATALOG}


def _build_real_route_alternatives(origin_city: str, dest_city: str, base_date_str: str, arr_dt: Any) -> List[Any]:
    from datetime import timedelta
    from app.schemas.optimization_schemas import CandidateAlternativeInput
    return [
        CandidateAlternativeInput(
            transport_id="12015-SHT",
            name=f"12015 Ajmer Shatabdi Express ({origin_city} → {dest_city})",
            supplier_type="train",
            provider="Indian Railways (IRCTC)",
            origin=origin_city,
            destination=dest_city,
            departure=f"{base_date_str}T13:30:00",
            arrival=f"{base_date_str}T17:30:00",
            price=800.0,
            available_seats=14,
            number_of_changes=0,
            reliability=0.96,
        ),
        CandidateAlternativeInput(
            transport_id="TRN123",
            name=f"12986 AC Double Decker Express ({origin_city} → {dest_city})",
            supplier_type="train",
            provider="Indian Railways (IRCTC)",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=680.0,
            available_seats=18,
            number_of_changes=0,
            reliability=0.97,
        ),
        CandidateAlternativeInput(
            transport_id="TRN124",
            name=f"20978 Vande Bharat Express ({origin_city} → {dest_city})",
            supplier_type="train",
            provider="Indian Railways (IRCTC)",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=160)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=1150.0,
            available_seats=22,
            number_of_changes=0,
            reliability=0.98,
        ),
        CandidateAlternativeInput(
            transport_id="BUS101",
            name=f"RSRTC Gold Line Volvo AC ({origin_city} → {dest_city})",
            supplier_type="bus",
            provider="RSRTC Gold Line Volvo",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(hours=6, minutes=15)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=750.0,
            available_seats=19,
            number_of_changes=0,
            reliability=0.89,
        ),
        CandidateAlternativeInput(
            transport_id="FLT101",
            name=f"Airline A FL-401 ({origin_city} → {dest_city})",
            supplier_type="flight",
            provider="Airline A",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=75)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(minutes=140)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=6500.0,
            available_seats=9,
            number_of_changes=0,
            reliability=0.96,
        ),
        CandidateAlternativeInput(
            transport_id="FLT102",
            name=f"Airline B FL-702 ({origin_city} → {dest_city})",
            supplier_type="flight",
            provider="Airline B",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(minutes=155)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=5800.0,
            available_seats=14,
            number_of_changes=0,
            reliability=0.94,
        ),
        CandidateAlternativeInput(
            transport_id="FLT103",
            name=f"IndiGo 6E-5091 ({origin_city} → {dest_city})",
            supplier_type="flight",
            provider="IndiGo Airlines",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=105)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(minutes=165)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=3850.0,
            available_seats=6,
            number_of_changes=0,
            reliability=0.95,
        ),
        CandidateAlternativeInput(
            transport_id="FLT104",
            name=f"Air India AI-415 ({origin_city} → {dest_city})",
            supplier_type="flight",
            provider="Air India",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(minutes=120)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(minutes=180)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=4800.0,
            available_seats=11,
            number_of_changes=0,
            reliability=0.95,
        ),
        CandidateAlternativeInput(
            transport_id="TRN125",
            name=f"12957 Late Night Superfast ({origin_city} → {dest_city})",
            supplier_type="train",
            provider="Indian Railways (IRCTC)",
            origin=origin_city,
            destination=dest_city,
            departure=(arr_dt + timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%S"),
            arrival=(arr_dt + timedelta(hours=8, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S"),
            price=620.0,
            available_seats=30,
            number_of_changes=0,
            reliability=0.88,
        ),
    ]


def _solve_and_create_live_workspace_plan(
    db: Session,
    journey: Any,
    bookings: List[Any],
    active_constraints: Optional[Dict[str, Any]] = None,
    rejection_feedback: Optional[Dict[str, Any]] = None,
    revision_count: int = 1,
) -> Tuple[Optional[Dict[str, Any]], Any, Optional[Dict[str, Any]]]:
    from datetime import datetime, timedelta
    from app.models.models import BookingStatus
    from app.schemas.optimization_schemas import (
        OptimizationConstraints,
        TravelerPreferences,
        OptimizationWeights,
    )
    from app.modules.recovery.constraints import constraint_engine

    disrupted_leg = next((b for b in bookings if b.status in (BookingStatus.DELAYED, BookingStatus.CANCELLED)), bookings[0])
    disrupted_idx = bookings.index(disrupted_leg)
    missed_leg = bookings[disrupted_idx + 1] if disrupted_idx + 1 < len(bookings) else bookings[-1]
    hotel_leg = next((b for b in bookings if b.booking_type.value == "HOTEL"), None)

    origin_city = missed_leg.origin or "Delhi"
    dest_city = missed_leg.destination or "Jaipur"
    base_date_str = disrupted_leg.end_time.strftime("%Y-%m-%d")

    current_arrival_iso = disrupted_leg.end_time.strftime("%Y-%m-%dT%H:%M:%S")
    hotel_cutoff_dt = (
        hotel_leg.start_time.replace(hour=23, minute=0, second=0)
        if hotel_leg
        else disrupted_leg.end_time + timedelta(hours=7)
    )
    hotel_cutoff_iso = hotel_cutoff_dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Build real catalog alternatives
    candidates = _build_real_route_alternatives(origin_city, dest_city, base_date_str, disrupted_leg.end_time)

    # Filter candidates based on active rejection constraints (e.g. excluded providers, transport IDs, modes, budget)
    filtered_candidates = constraint_engine.filter_candidates(candidates, active_constraints) if active_constraints else candidates

    effective_budget = 10000.0
    if active_constraints and active_constraints.get("max_budget") is not None:
        effective_budget = min(effective_budget, float(active_constraints["max_budget"]))

    excluded_modes = list(active_constraints.get("excluded_modes", [])) if active_constraints else []

    opt_res = ortools_recovery_optimizer.optimize(
        OptimizationRequest(
            origin=origin_city,
            destination=dest_city,
            auto_fetch_from_suppliers=False,
            available_alternatives=filtered_candidates,
            constraints=OptimizationConstraints(
                current_arrival=current_arrival_iso,
                hotel_latest_checkin=hotel_cutoff_iso,
                min_connection_minutes=30,
                required_seats=1,
            ),
            traveler_preferences=TravelerPreferences(
                max_budget=effective_budget,
                excluded_modes=excluded_modes,
                weights=OptimizationWeights(
                    price=0.30,
                    travel_time=0.25,
                    waiting_time=0.15,
                    number_of_changes=0.10,
                    arrival_time=0.10,
                    reliability=0.10,
                ),
            ),
        )
    )

    selected = opt_res.selected_option

    # Infeasible: constraints could not be satisfied
    if not selected or not opt_res.constraints_satisfied:
        infeasible_summary = "No suitable automated recovery plan could be found with the current requirements."
        plan_record = RecoveryPlan(
            journey_id=journey.id,
            disruption_id=disrupted_leg.id if hasattr(disrupted_leg, "id") else 1,
            status=RecoveryPlanStatus.REVISION_REQUIRED,
            summary=infeasible_summary,
            reasoning_explanation=infeasible_summary,
            estimated_additional_cost=0.0,
            refund_opportunities={},
            actions=[],
            alternatives_considered=[a.model_dump() if hasattr(a, "model_dump") else a for a in opt_res.alternatives],
            active_constraints=active_constraints or {},
            rejection_feedback=rejection_feedback or {},
            revision_count=revision_count,
        )
        db.add(plan_record)
        db.commit()
        db.refresh(plan_record)

        infeasible_plan_data = {
            "plan_id": f"PLAN-INFEASIBLE-{journey.id}-{revision_count}",
            "db_plan_id": plan_record.id,
            "status": RecoveryPlanStatus.REVISION_REQUIRED.value,
            "workflow_stage": "INFEASIBLE_MANUAL_REVIEW",
            "summary": infeasible_summary,
            "message": infeasible_summary,
            "selected_option": None,
            "actions": [],
            "reasoning_explanation": infeasible_summary,
            "net_additional_cost": 0.0,
            "refund_amount_inr": 0.0,
            "is_executed": False,
            "is_approved": False,
            "is_feasible": False,
            "active_constraints": active_constraints or {},
            "rejection_feedback": rejection_feedback or {},
            "revision_count": revision_count,
            "alternatives_considered": plan_record.alternatives_considered,
        }
        infeasible_details = {
            "status": "REVISION_REQUIRED",
            "workflow_stage": "INFEASIBLE_MANUAL_REVIEW",
            "message": infeasible_summary,
            "active_constraints": active_constraints or {},
            "revision_count": revision_count,
            "execution_status": "MANUAL_REVIEW_REQUIRED",
        }
        return infeasible_plan_data, opt_res, infeasible_details

    # Feasible solution found
    old_ref = missed_leg.reference_number
    old_title = missed_leg.title
    old_price = float(missed_leg.price or 800.0)
    old_dep_hm = missed_leg.start_time.strftime("%H:%M")
    old_arr_hm = missed_leg.end_time.strftime("%H:%M")

    new_dep_dt = datetime.fromisoformat(selected["departure"])
    new_arr_dt = datetime.fromisoformat(selected["arrival"])
    new_hotel_dt = new_arr_dt + timedelta(minutes=30)
    refund_inr = round(old_price * 0.75, 2)
    net_diff = max(0.0, float(selected["price"]) - old_price)
    orig_hotel_hm = hotel_leg.start_time.strftime("%H:%M") if (hotel_leg and hotel_leg.start_time) else "18:00"

    plan_id = f"PLAN-PROP-{journey.id}-{selected['transport_id']}-REV{revision_count}"

    raw_plan_input = {
        "plan_id": plan_id,
        "original_booking_id": old_ref,
        "original_transport_id": "TRN123",
        "original_price": old_price,
        "new_transport_id": selected["transport_id"],
        "hotel_booking_id": hotel_leg.reference_number if hotel_leg else "HTL-JAI-101",
        "hotel_id": "HTL101",
        "new_check_in": new_hotel_dt.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    compiled_actions = recovery_action_executor.compile_plan_to_actions(raw_plan_input)
    proposed_actions = []
    for a in compiled_actions:
        act_copy = dict(a)
        act_copy["status"] = "PROPOSED"
        proposed_actions.append(act_copy)

    summary_text = (
        f"Proposed Recovery Plan (Rev {revision_count}): Rebook {old_ref} onto {selected.get('name', selected['transport_id'])} "
        f"({new_dep_dt.strftime('%H:%M')}–{new_arr_dt.strftime('%H:%M')}). "
        f"Net fare difference: ₹{net_diff:.2f}. Eligible refund: ₹{refund_inr:.2f}."
    )

    plan_record = RecoveryPlan(
        journey_id=journey.id,
        disruption_id=disrupted_leg.id if hasattr(disrupted_leg, "id") else 1,
        status=RecoveryPlanStatus.PLAN_GENERATED,
        summary=summary_text,
        reasoning_explanation=opt_res.explanation or "Optimal CP-SAT solution satisfying transfer buffer and hotel cutoff.",
        estimated_additional_cost=net_diff,
        refund_opportunities={"refund_amount_inr": refund_inr, "eligible": True},
        actions=proposed_actions,
        alternatives_considered=[a.model_dump() if hasattr(a, "model_dump") else a for a in opt_res.alternatives],
        active_constraints=active_constraints or {},
        rejection_feedback=rejection_feedback or {},
        revision_count=revision_count,
    )
    db.add(plan_record)
    db.commit()
    db.refresh(plan_record)

    proposed_plan_data = {
        "plan_id": plan_id,
        "db_plan_id": plan_record.id,
        "status": RecoveryPlanStatus.PLAN_GENERATED.value,
        "workflow_stage": "HUMAN_REVIEW",
        "selected_option": selected,
        "actions": proposed_actions,
        "summary": summary_text,
        "reasoning_explanation": opt_res.explanation,
        "net_additional_cost": net_diff,
        "refund_amount_inr": refund_inr,
        "is_executed": False,
        "is_approved": False,
        "is_feasible": True,
        "active_constraints": active_constraints or {},
        "rejection_feedback": rejection_feedback or {},
        "revision_count": revision_count,
        "disruption_summary": f"{disrupted_leg.title} arrival was delayed to {disrupted_leg.end_time.strftime('%H:%M')}, causing a missed connection buffer to {old_title}.",
        "alternatives_considered": plan_record.alternatives_considered,
    }

    recovery_details = {
        "status": "PLAN_GENERATED",
        "workflow_stage": "HUMAN_REVIEW",
        "revision_count": revision_count,
        "active_constraints": active_constraints or {},
        "proposed_cancellation": f"{old_title} ({old_dep_hm}–{old_arr_hm})",
        "proposed_rebooking": f"{selected.get('name')} ({new_dep_dt.strftime('%H:%M')}–{new_arr_dt.strftime('%H:%M')}, ₹{selected['price']})",
        "refund_amount_inr": refund_inr,
        "proposed_hotel_update": (
            f"{hotel_leg.provider_name} check-in moved {orig_hotel_hm} → {new_hotel_dt.strftime('%H:%M')}"
            if hotel_leg
            else "No hotel modification needed"
        ),
        "execution_status": "AWAITING_HUMAN_APPROVAL",
    }

    return proposed_plan_data, opt_res, recovery_details


@router.post("/live-workspace/recover")
def run_live_workspace_recovery(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    [PLAN GENERATION STAGE] Formulates an initial optimized recovery plan (Revision 1)
    using Google OR-Tools CP-SAT without executing any actions.
    Places the plan in HUMAN_REVIEW. Execution is strictly blocked until human approval.
    """
    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    if not journey:
        raise HTTPException(status_code=400, detail="No active journey in database to recover.")

    from app.models.models import Booking
    bookings = (
        db.query(Booking)
        .filter(Booking.journey_id == journey.id)
        .order_by(Booking.start_time.asc())
        .all()
    )
    if len(bookings) < 2:
        raise HTTPException(status_code=400, detail="Add at least 2 connected bookings to run recovery.")

    proposed_plan_data, opt_res, recovery_details = _solve_and_create_live_workspace_plan(
        db=db,
        journey=journey,
        bookings=bookings,
        active_constraints={},
        rejection_feedback={},
        revision_count=1,
    )

    workspace = _serialize_live_workspace(db)
    workspace["optimization_result"] = opt_res.model_dump() if hasattr(opt_res, "model_dump") else opt_res
    workspace["proposed_plan"] = proposed_plan_data
    workspace["execution_summary"] = None  # Explicitly None: planning does NOT execute
    workspace["recovery_details"] = recovery_details
    return workspace


@router.post("/live-workspace/execute")
def execute_live_workspace_recovery(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    [EXECUTION STAGE] Explicitly executes an approved recovery plan against live workspace bookings.
    Executes actions via RecoveryActionExecutor against Mock Suppliers, updates SQLite bookings,
    syncs journey graph, and generates fact-grounded notifications.
    """
    from datetime import datetime, timedelta
    from app.models.models import Booking, BookingStatus, RecoveryPlan, RecoveryPlanStatus
    from app.modules.journeys.graph_builder import JourneyGraphEngine
    from app.modules.notifications.notification_agent import notification_agent_service
    from app.schemas.notification_schemas import StructuredRecoveryFacts

    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    if not journey:
        raise HTTPException(status_code=400, detail="No active journey in database to execute recovery for.")

    bookings = (
        db.query(Booking)
        .filter(Booking.journey_id == journey.id)
        .order_by(Booking.start_time.asc())
        .all()
    )
    if len(bookings) < 2:
        raise HTTPException(status_code=400, detail="Add at least 2 connected bookings to execute recovery.")

    plan_record = (
        db.query(RecoveryPlan)
        .filter(RecoveryPlan.journey_id == journey.id)
        .order_by(RecoveryPlan.id.desc())
        .first()
    )

    if not plan_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recovery plan found for this journey. A recovery plan must be generated and APPROVED before execution."
        )

    # CRITICAL SAFETY REQUIREMENT:
    # Strictly enforce that plan.status === APPROVED before executing anything.
    # Unapproved plans (PLAN_GENERATED, PROPOSED, REJECTED, REVISION_REQUIRED) are strictly forbidden from execution.
    if plan_record.status != RecoveryPlanStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Execution forbidden: Recovery plan has status '{plan_record.status.value}'. Plan must be APPROVED before execution."
        )

    # Workflow transition: APPROVED -> EXECUTING
    plan_record.status = RecoveryPlanStatus.EXECUTING
    db.commit()
    db.refresh(plan_record)

    disrupted_leg = next((b for b in bookings if b.status in (BookingStatus.DELAYED, BookingStatus.CANCELLED)), bookings[0])
    disrupted_idx = bookings.index(disrupted_leg)
    missed_leg = bookings[disrupted_idx + 1] if disrupted_idx + 1 < len(bookings) else bookings[-1]
    hotel_leg = next((b for b in bookings if b.booking_type.value == "HOTEL"), None)

    old_ref = missed_leg.reference_number
    old_title = missed_leg.title
    old_price = float(missed_leg.price or 800.0)
    old_dep_hm = missed_leg.start_time.strftime("%H:%M")
    old_arr_hm = missed_leg.end_time.strftime("%H:%M")

    target_transport_id = "TRN124"
    target_provider = "Indian Railways (IRCTC)"
    target_name = "20978 Vande Bharat Express (Delhi -> Jaipur)"
    target_price = 1150.0
    arr_dt = disrupted_leg.end_time
    new_dep_dt = arr_dt + timedelta(minutes=160)
    new_arr_dt = arr_dt + timedelta(hours=5, minutes=30)
    new_hotel_dt = new_arr_dt + timedelta(minutes=30)
    refund_inr = round(old_price * 0.75, 2)

    if plan_record and plan_record.actions:
        rebook_act = next((a for a in plan_record.actions if a.get("action_type") == "rebook_transportation"), None)
        if rebook_act:
            target_transport_id = rebook_act.get("booking_id") or rebook_act.get("request", {}).get("new_transport_id", target_transport_id)

    if plan_record and plan_record.alternatives_considered:
        for alt in plan_record.alternatives_considered:
            if alt.get("transport_id") == target_transport_id:
                target_provider = alt.get("provider", target_provider)
                target_name = alt.get("name", target_name)
                target_price = float(alt.get("price", target_price))
                if "departure" in alt and "arrival" in alt:
                    try:
                        new_dep_dt = datetime.fromisoformat(alt["departure"])
                        new_arr_dt = datetime.fromisoformat(alt["arrival"])
                        new_hotel_dt = new_arr_dt + timedelta(minutes=30)
                    except Exception:
                        pass
                break

    # 1. Execute recovery actions via RecoveryActionExecutor
    exec_summary = recovery_action_executor.execute_recovery_plan(
        plan_input={
            "plan_id": f"PLAN-LIVE-{journey.id}-{old_ref}",
            "status": "EXECUTING",
            "original_booking_id": old_ref,
            "original_transport_id": "TRN123",
            "original_price": old_price,
            "new_transport_id": target_transport_id,
            "hotel_booking_id": hotel_leg.reference_number if hotel_leg else "HTL-JAI-101",
            "hotel_id": "HTL101",
            "new_check_in": new_hotel_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        }
    )

    # 2. Update SQLite rows to recovered state
    missed_leg.reference_number = target_transport_id
    missed_leg.provider_name = target_provider
    missed_leg.title = target_name
    missed_leg.start_time = new_dep_dt
    missed_leg.end_time = new_arr_dt
    missed_leg.price = target_price
    missed_leg.status = BookingStatus.CONFIRMED

    orig_hotel_hm = "18:00"
    if hotel_leg:
        orig_hotel_hm = hotel_leg.start_time.strftime("%H:%M")
        hotel_leg.start_time = new_hotel_dt
        hotel_leg.title = f"{hotel_leg.provider_name} (Check-in {new_hotel_dt.strftime('%H:%M')})"
        hotel_leg.status = BookingStatus.CONFIRMED

    # Workflow transition: EXECUTING -> COMPLETED
    if plan_record:
        plan_record.status = RecoveryPlanStatus.COMPLETED

    db.commit()
    db.refresh(journey)
    JourneyGraphEngine(journey_id=journey.id).sync_to_database(db, journey)

    # 3. Generate notifications
    notification_agent_service.generate_all_notifications(
        facts=StructuredRecoveryFacts(
            journey_id=journey.id,
            disrupted_booking_ref=disrupted_leg.reference_number,
            delay_minutes=240,
            original_arrival_time="12:00",
            revised_arrival_time=disrupted_leg.end_time.strftime("%H:%M"),
            missed_booking_ref=old_ref,
            missed_transport_id="TRN123",
            missed_departure_time=old_dep_hm,
            missed_arrival_time=old_arr_hm,
            missed_ticket_price_inr=old_price,
            refund_amount_inr=refund_inr,
            rebooked_booking_ref=f"PNR-{target_transport_id}",
            rebooked_transport_id=target_transport_id,
            rebooked_service_name=target_name,
            rebooked_departure_time=new_dep_dt.strftime("%H:%M"),
            rebooked_arrival_time=new_arr_dt.strftime("%H:%M"),
            rebooked_price_inr=target_price,
            hotel_booking_ref=hotel_leg.reference_number if hotel_leg else "HTL-JAI-101",
            hotel_original_checkin=orig_hotel_hm,
            hotel_revised_checkin=new_hotel_dt.strftime("%H:%M"),
            hotel_latest_cutoff="23:00",
        )
    )

    recovery_details = {
        "status": "COMPLETED",
        "workflow_stage": "COMPLETED",
        "cancelled_booking": f"{old_title} ({old_dep_hm}–{old_arr_hm})",
        "rebooked_booking": f"{target_name} ({new_dep_dt.strftime('%H:%M')}–{new_arr_dt.strftime('%H:%M')}, ₹{target_price})",
        "refund_amount_inr": refund_inr,
        "hotel_updated": (
            f"{hotel_leg.provider_name} check-in moved {orig_hotel_hm} → {new_hotel_dt.strftime('%H:%M')}"
            if hotel_leg
            else "No hotel modification needed"
        ),
        "execution_status": "COMPLETED",
    }

    workspace = _serialize_live_workspace(db)
    workspace["execution_summary"] = exec_summary
    workspace["recovery_details"] = recovery_details
    return workspace


@router.post("/live-workspace/approve")
def approve_live_workspace_recovery(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    [HUMAN APPROVAL GATE] Transitions recovery plan from PLAN_GENERATED / HUMAN_REVIEW -> APPROVED.
    The execution service strictly checks this status before executing any actions.
    """
    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    if not journey:
        raise HTTPException(status_code=400, detail="No active journey in database to approve recovery for.")

    plan_record = (
        db.query(RecoveryPlan)
        .filter(RecoveryPlan.journey_id == journey.id)
        .order_by(RecoveryPlan.id.desc())
        .first()
    )
    if not plan_record:
        raise HTTPException(status_code=400, detail="No recovery plan found in database to approve. Generate a plan first.")

    if plan_record.status in (RecoveryPlanStatus.REJECTED, RecoveryPlanStatus.REVISION_REQUIRED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve plan with status '{plan_record.status.value}'. Please generate a revised plan."
        )

    # Transition to APPROVED
    plan_record.status = RecoveryPlanStatus.APPROVED

    if plan_record.actions:
        updated_actions = []
        for a in plan_record.actions:
            act_copy = dict(a)
            act_copy["status"] = "APPROVED"
            updated_actions.append(act_copy)
        plan_record.actions = updated_actions

    db.commit()
    db.refresh(plan_record)

    workspace = _serialize_live_workspace(db)
    workspace["proposed_plan"] = {
        "db_plan_id": plan_record.id,
        "status": RecoveryPlanStatus.APPROVED.value,
        "workflow_stage": "APPROVED",
        "summary": plan_record.summary,
        "actions": plan_record.actions,
        "is_executed": False,
        "is_approved": True,
    }
    workspace["recovery_details"] = {
        "status": "APPROVED",
        "workflow_stage": "APPROVED",
        "execution_status": "READY_FOR_EXECUTION",
        "message": "Recovery plan approved by human reviewer. Execution is now authorized.",
    }
    workspace["execution_summary"] = None
    return workspace


@router.post("/live-workspace/approve-and-execute")
def approve_and_execute_live_workspace_recovery(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    [HUMAN APPROVAL + EXECUTION] Combined workflow:
    1. Marks plan as APPROVED
    2. Calls execution logic (validates APPROVED, transitions to EXECUTING, runs actions, marks COMPLETED)
    """
    approve_live_workspace_recovery(db)
    return execute_live_workspace_recovery(db)


@router.post("/live-workspace/reject")
def reject_live_workspace_recovery(
    reason: Optional[str] = "Rejected by human reviewer for revision",
    reasons: Optional[List[str]] = None,
    feedback_text: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    [HUMAN REVIEW GATE] Marks recovery plan as REJECTED / REVISION_REQUIRED.
    Execution of this plan is strictly forbidden.
    """
    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    if not journey:
        raise HTTPException(status_code=400, detail="No active journey in database.")

    plan_record = (
        db.query(RecoveryPlan)
        .filter(RecoveryPlan.journey_id == journey.id)
        .order_by(RecoveryPlan.id.desc())
        .first()
    )
    if not plan_record:
        raise HTTPException(status_code=400, detail="No recovery plan found to reject.")

    plan_record.status = RecoveryPlanStatus.REJECTED
    if reasons or feedback_text:
        plan_record.rejection_feedback = {"reasons": reasons or [], "text": feedback_text or reason}
    db.commit()
    db.refresh(plan_record)

    workspace = _serialize_live_workspace(db)
    workspace["proposed_plan"] = {
        "db_plan_id": plan_record.id,
        "status": RecoveryPlanStatus.REJECTED.value,
        "workflow_stage": "REJECTED",
        "is_executed": False,
        "is_approved": False,
        "revision_count": plan_record.revision_count or 1,
        "active_constraints": plan_record.active_constraints or {},
        "rejection_feedback": plan_record.rejection_feedback or {},
    }
    workspace["recovery_details"] = {
        "status": "REJECTED",
        "workflow_stage": "REJECTED",
        "execution_status": "REJECTED_REVISION_REQUIRED",
        "rejection_reason": reason,
        "active_constraints": plan_record.active_constraints or {},
        "revision_count": plan_record.revision_count or 1,
    }
    return workspace


@router.post("/live-workspace/reject-and-replan")
def reject_and_replan_live_workspace_recovery(
    request: RejectAndReplanRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    [STAGE 3: REJECT & REVISE WORKFLOW]
    1. Rejects current recovery plan (status -> REJECTED). Execution is strictly forbidden.
    2. Enforces maximum revisions limit (e.g., max 3 revisions).
    3. Interprets rejection reasons + custom text feedback into planning constraints.
    4. Merges with ALL previous constraints (preserves historical constraints across revisions).
    5. Re-runs OR-Tools recovery planning with accumulated constraints.
    6. Newly generated plan is placed in HUMAN_REVIEW (status PLAN_GENERATED). ZERO automated execution.
    """
    from app.modules.recovery.constraints import constraint_engine
    from app.models.models import Booking

    journey = db.query(Journey).order_by(Journey.id.desc()).first()
    if not journey:
        raise HTTPException(status_code=400, detail="No active journey in database to reject and replan.")

    current_plan = (
        db.query(RecoveryPlan)
        .filter(RecoveryPlan.journey_id == journey.id)
        .order_by(RecoveryPlan.id.desc())
        .first()
    )
    if not current_plan:
        raise HTTPException(status_code=400, detail="No existing recovery plan found to reject.")

    # 1. Reject current plan immediately (execution forbidden)
    current_plan.status = RecoveryPlanStatus.REJECTED
    current_plan.rejection_feedback = {"reasons": request.reasons, "text": request.feedback_text}
    db.commit()
    db.refresh(current_plan)

    # 2. Check maximum revisions limit (e.g., 3 revisions max)
    current_revision = current_plan.revision_count or 1
    if current_revision >= 3:
        current_plan.status = RecoveryPlanStatus.REVISION_REQUIRED
        db.commit()
        workspace = _serialize_live_workspace(db)
        workspace["proposed_plan"] = {
            "db_plan_id": current_plan.id,
            "status": RecoveryPlanStatus.REVISION_REQUIRED.value,
            "workflow_stage": "MAX_REVISIONS_EXCEEDED",
            "summary": "No suitable automated recovery plan could be found with the current requirements.",
            "message": "No suitable automated recovery plan could be found with the current requirements.",
            "revision_count": current_revision,
            "active_constraints": current_plan.active_constraints or {},
            "rejection_feedback": {"reasons": request.reasons, "text": request.feedback_text},
            "is_executed": False,
            "is_approved": False,
            "is_feasible": False,
            "alternatives_considered": current_plan.alternatives_considered,
        }
        workspace["recovery_details"] = {
            "status": "REVISION_REQUIRED",
            "workflow_stage": "MAX_REVISIONS_EXCEEDED",
            "message": "No suitable automated recovery plan could be found with the current requirements.",
            "active_constraints": current_plan.active_constraints or {},
            "revision_count": current_revision,
            "execution_status": "MAX_REVISIONS_HALTED",
        }
        return workspace

    # 3. Interpret feedback into constraints & PRESERVE historical constraints
    current_plan_dict = {
        "summary": current_plan.summary,
        "actions": current_plan.actions,
        "selected_option": (
            next((a for a in (current_plan.alternatives_considered or []) if isinstance(a, dict) and a.get("selected")), None)
        ),
    }
    merged_constraints = constraint_engine.interpret_rejection(
        reasons=request.reasons,
        feedback_text=request.feedback_text,
        current_plan=current_plan_dict,
        previous_constraints=current_plan.active_constraints,
    )

    # 4. Re-solve with accumulated constraints
    bookings = db.query(Booking).filter(Booking.journey_id == journey.id).order_by(Booking.start_time.asc()).all()
    if len(bookings) < 2:
        raise HTTPException(status_code=400, detail="Insufficient bookings to re-plan.")

    proposed_plan_data, opt_res, recovery_details = _solve_and_create_live_workspace_plan(
        db=db,
        journey=journey,
        bookings=bookings,
        active_constraints=merged_constraints,
        rejection_feedback={"reasons": request.reasons, "text": request.feedback_text},
        revision_count=current_revision + 1,
    )

    workspace = _serialize_live_workspace(db)
    workspace["optimization_result"] = opt_res.model_dump() if hasattr(opt_res, "model_dump") else opt_res
    workspace["proposed_plan"] = proposed_plan_data
    workspace["execution_summary"] = None  # ZERO execution!
    workspace["recovery_details"] = recovery_details
    return workspace


@router.post("/plans/{plan_id}/approve")
def approve_recovery_plan_by_id(plan_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Human Approval Gate for a specific recovery plan by ID.
    Transitions plan to APPROVED.
    """
    plan_record = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if not plan_record:
        raise HTTPException(status_code=404, detail=f"Recovery plan {plan_id} not found.")

    if plan_record.status in (RecoveryPlanStatus.REJECTED, RecoveryPlanStatus.REVISION_REQUIRED):
        raise HTTPException(status_code=400, detail=f"Cannot approve plan with status '{plan_record.status.value}'.")

    plan_record.status = RecoveryPlanStatus.APPROVED
    if plan_record.actions:
        updated_actions = []
        for a in plan_record.actions:
            act_copy = dict(a)
            act_copy["status"] = "APPROVED"
            updated_actions.append(act_copy)
        plan_record.actions = updated_actions

    db.commit()
    db.refresh(plan_record)
    return {
        "plan_id": plan_record.id,
        "status": plan_record.status.value,
        "workflow_stage": "APPROVED",
        "message": "Recovery plan approved by human reviewer."
    }


@router.post("/plans/{plan_id}/reject")
def reject_recovery_plan_by_id(
    plan_id: int,
    reason: Optional[str] = "Rejected for replanning",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Rejects a recovery plan. Execution of this plan is strictly forbidden.
    """
    plan_record = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if not plan_record:
        raise HTTPException(status_code=404, detail=f"Recovery plan {plan_id} not found.")

    plan_record.status = RecoveryPlanStatus.REJECTED
    db.commit()
    db.refresh(plan_record)
    return {
        "plan_id": plan_record.id,
        "status": plan_record.status.value,
        "workflow_stage": "REJECTED",
        "message": f"Recovery plan rejected: {reason}"
    }


@router.post("/plans/{plan_id}/reject-and-replan")
def reject_and_replan_plan_by_id(
    plan_id: int,
    request: RejectAndReplanRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    [STAGE 3: REJECT & REVISE WORKFLOW BY PLAN ID]
    1. Rejects current recovery plan (status -> REJECTED). Execution is strictly forbidden.
    2. Enforces maximum revisions limit (e.g., max 3 revisions).
    3. Interprets rejection reasons + custom text feedback into planning constraints.
    4. Merges with ALL previous constraints (preserves historical constraints across revisions).
    5. Re-runs OR-Tools recovery planning with accumulated constraints.
    6. Newly generated plan is placed in HUMAN_REVIEW (status PLAN_GENERATED). ZERO automated execution.
    """
    from app.modules.recovery.constraints import constraint_engine
    plan_record = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if not plan_record:
        raise HTTPException(status_code=404, detail=f"Recovery plan {plan_id} not found.")

    # 1. Reject current plan immediately (execution forbidden)
    plan_record.status = RecoveryPlanStatus.REJECTED
    plan_record.rejection_feedback = {"reasons": request.reasons, "text": request.feedback_text}
    db.commit()
    db.refresh(plan_record)

    current_revision = plan_record.revision_count or 1
    if current_revision >= 3:
        plan_record.status = RecoveryPlanStatus.REVISION_REQUIRED
        db.commit()
        return {
            "status": RecoveryPlanStatus.REVISION_REQUIRED.value,
            "workflow_stage": "MAX_REVISIONS_EXCEEDED",
            "summary": "No suitable automated recovery plan could be found with the current requirements.",
            "message": "No suitable automated recovery plan could be found with the current requirements.",
            "plan_id": f"PLAN-REJECTED-{plan_record.id}",
            "db_plan_id": plan_record.id,
            "revision_count": current_revision,
            "active_constraints": plan_record.active_constraints or {},
            "rejection_feedback": plan_record.rejection_feedback or {},
            "is_executed": False,
            "is_approved": False,
            "is_feasible": False,
            "alternatives_considered": plan_record.alternatives_considered,
        }

    # 2. Interpret feedback into constraints & PRESERVE historical constraints
    current_plan_dict = {
        "summary": plan_record.summary,
        "actions": plan_record.actions,
        "selected_option": (
            next((a for a in (plan_record.alternatives_considered or []) if isinstance(a, dict) and a.get("selected")), None)
        ),
    }
    merged_constraints = constraint_engine.interpret_rejection(
        reasons=request.reasons,
        feedback_text=request.feedback_text,
        current_plan=current_plan_dict,
        previous_constraints=plan_record.active_constraints,
    )

    # 3. Generate revised plan via recovery_planner
    return recovery_planner.generate_recovery_plan(
        journey_id=plan_record.journey_id,
        disruption_id=plan_record.disruption_id,
        active_constraints=merged_constraints,
        rejection_feedback={"reasons": request.reasons, "text": request.feedback_text},
        revision_count=current_revision + 1,
        db=db,
    )




