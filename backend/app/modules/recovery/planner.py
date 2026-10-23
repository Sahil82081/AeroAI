"""
Recovery Planner Module:
Responsible SOLELY for generating proposed recovery plans in response to disruptions.

Guarantees:
- Pure planning: DOES NOT execute any real-world actions.
- DOES NOT cancel bookings, rebook flights/trains, initiate refunds, submit claims,
  modify hotel reservations, or send execution-related notifications.
- Reuses Google OR-Tools CP-SAT optimizer and existing action compilation logic.
- Stores the proposed plan in the database with status PROPOSED (or returns it).
- Execution remains a strictly decoupled, separately callable operation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.optimization_schemas import (
    OptimizationRequest,
    OptimizationConstraints,
    TravelerPreferences,
    OptimizationWeights,
    CandidateAlternativeInput,
    OptimizationResponse,
)
from app.modules.optimization.ortools_optimizer import ortools_recovery_optimizer
from app.modules.recovery.action_executor import RecoveryActionExecutor
from app.models.models import RecoveryPlan, RecoveryPlanStatus, Disruption, DisruptionStatus
from app.core.logger import logger


class RecoveryPlanner:
    """
    Decoupled Recovery Planner.
    Generates proposed recovery plans without executing any actions.
    """

    def __init__(self):
        self.optimizer = ortools_recovery_optimizer

    def generate_recovery_plan(
        self,
        journey_id: int,
        disruption_id: Optional[int] = None,
        disrupted_booking_ref: str = "12015-SHT",
        original_transport_id: str = "TRN123",
        original_price: float = 800.0,
        origin: str = "Delhi",
        destination: str = "Jaipur",
        revised_arrival: str = "2026-10-20T16:00:00",
        hotel_booking_ref: str = "HTL-JAI-101",
        hotel_latest_checkin: str = "2026-10-20T22:00:00",
        available_alternatives: Optional[List[CandidateAlternativeInput]] = None,
        max_budget: float = 10000.0,
        weights: Optional[OptimizationWeights] = None,
        correlation_id: Optional[str] = None,
        passenger_name: str = "Aarav Sharma",
        traveler_email: str = "aarav.sharma@example.com",
        contact_email: str = "frontdesk@heritagepalacejaipur.com",
        active_constraints: Optional[Dict[str, Any]] = None,
        rejection_feedback: Optional[Dict[str, Any]] = None,
        revision_count: int = 0,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Generates a proposed recovery plan for a disruption and returns/stores it.
        Does NOT execute any actions against suppliers or send notifications.
        Enforces active rejection constraints (e.g. excluded providers, max budget, excluded modes)
        and tracks revision count without changing OR-Tools solver logic.
        """
        from app.modules.recovery.constraints import constraint_engine

        # 1. Filter candidate alternatives based on active rejection constraints
        raw_candidates = list(available_alternatives or [])
        filtered_candidates = constraint_engine.filter_candidates(raw_candidates, active_constraints) if active_constraints else raw_candidates

        # 2. Compute effective budget & traveler preferences
        effective_budget = float(active_constraints["max_budget"]) if (active_constraints and active_constraints.get("max_budget") is not None) else max_budget

        excluded_modes = list(active_constraints.get("excluded_modes", [])) if active_constraints else []

        # 3. Build Optimization Request
        opt_req = OptimizationRequest(
            origin=origin,
            destination=destination,
            auto_fetch_from_suppliers=(len(filtered_candidates) == 0 and (available_alternatives is None or len(available_alternatives) == 0)),
            available_alternatives=filtered_candidates,
            constraints=OptimizationConstraints(
                current_arrival=revised_arrival,
                hotel_latest_checkin=hotel_latest_checkin,
                min_connection_minutes=30,
                required_seats=1,
            ),
            traveler_preferences=TravelerPreferences(
                max_budget=effective_budget,
                excluded_modes=excluded_modes,
                weights=weights or OptimizationWeights(
                    price=0.30,
                    travel_time=0.25,
                    waiting_time=0.20,
                    number_of_changes=0.05,
                    arrival_time=0.10,
                    reliability=0.10,
                ),
            ),
        )

        # 4. Solve Multi-Criteria Optimization via OR-Tools CP-SAT
        opt_result: OptimizationResponse = self.optimizer.optimize(opt_req)
        selected_opt = opt_result.selected_option

        # Handle infeasible / no feasible alternative found
        if not selected_opt or not opt_result.constraints_satisfied:
            infeasible_summary = "No suitable automated recovery plan could be found with the current requirements."
            plan_id = f"PLAN-INFEASIBLE-{journey_id}-{revision_count}"
            recovery_plan_data: Dict[str, Any] = {
                "plan_id": plan_id,
                "journey_id": journey_id,
                "disruption_id": disruption_id,
                "status": RecoveryPlanStatus.REVISION_REQUIRED.value,
                "workflow_stage": "INFEASIBLE_MANUAL_REVIEW",
                "summary": infeasible_summary,
                "message": infeasible_summary,
                "selected_option": None,
                "objective_score": 0.0,
                "constraints_satisfied": False,
                "reasoning_explanation": infeasible_summary,
                "estimated_additional_cost": 0.0,
                "refund_opportunities": {"eligible": False, "estimated_refund_amount": 0.0},
                "actions": [],
                "alternatives_considered": [alt.model_dump() if hasattr(alt, "model_dump") else alt for alt in opt_result.alternatives],
                "active_constraints": active_constraints or {},
                "rejection_feedback": rejection_feedback or {},
                "revision_count": revision_count,
                "is_executed": False,
                "is_approved": False,
                "is_feasible": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if db:
                try:
                    plan_record = RecoveryPlan(
                        journey_id=journey_id,
                        disruption_id=disruption_id or 1,
                        status=RecoveryPlanStatus.REVISION_REQUIRED,
                        summary=infeasible_summary,
                        reasoning_explanation=infeasible_summary,
                        estimated_additional_cost=0.0,
                        refund_opportunities={},
                        actions=[],
                        alternatives_considered=recovery_plan_data["alternatives_considered"],
                        rejection_feedback=rejection_feedback,
                        active_constraints=active_constraints,
                        revision_count=revision_count,
                    )
                    db.add(plan_record)
                    db.commit()
                    db.refresh(plan_record)
                    recovery_plan_data["db_plan_id"] = plan_record.id
                except Exception as db_err:
                    logger.warning(f"Failed to persist infeasible RecoveryPlan: {db_err}")
            return recovery_plan_data

        # 3. Compute costs and refund opportunities
        new_price = float(selected_opt.get("price", 0.0))
        net_additional_cost = max(0.0, new_price - original_price)
        estimated_refund = round(original_price * 0.75, 2)

        corr_tag = correlation_id[-6:].upper() if correlation_id else str(int(datetime.now(timezone.utc).timestamp()))[-6:]
        plan_id = f"PLAN-PROP-{journey_id}-{selected_opt.get('transport_id', 'OPT')}-{corr_tag}"

        # 4. Compile proposed actions using RecoveryActionExecutor (pure compilation, NO execution)
        raw_plan_input = {
            "plan_id": plan_id,
            "original_booking_id": disrupted_booking_ref,
            "original_transport_id": original_transport_id,
            "original_price": original_price,
            "new_transport_id": selected_opt.get("transport_id", "TRN124"),
            "hotel_booking_id": hotel_booking_ref,
            "hotel_id": "HTL101",
            "new_check_in": selected_opt.get("arrival", "2026-10-20T21:30:00"),
            "passenger_name": passenger_name,
            "traveler_email": traveler_email,
            "contact_email": contact_email,
        }
        compiled_actions = RecoveryActionExecutor.compile_plan_to_actions(raw_plan_input)

        # Mark all compiled actions as PROPOSED (pure proposal)
        proposed_actions = []
        for act in compiled_actions:
            act_copy = dict(act)
            act_copy["status"] = "PROPOSED"
            proposed_actions.append(act_copy)

        summary_text = (
            f"Proposed Recovery Plan {plan_id}: Rebook {disrupted_booking_ref} onto "
            f"{selected_opt.get('name', selected_opt.get('transport_id'))} "
            f"({selected_opt.get('departure', '')} -> {selected_opt.get('arrival', '')}). "
            f"Net fare difference: INR {net_additional_cost:.2f}. "
            f"Eligible for INR {estimated_refund:.2f} refund waiver."
        )

        recovery_plan_data: Dict[str, Any] = {
            "plan_id": plan_id,
            "journey_id": journey_id,
            "disruption_id": disruption_id,
            "status": RecoveryPlanStatus.PROPOSED.value,
            "summary": summary_text,
            "selected_option": selected_opt,
            "objective_score": opt_result.objective_score,
            "constraints_satisfied": opt_result.constraints_satisfied,
            "reasoning_explanation": opt_result.explanation or "Optimal feasible alternative found via CP-SAT solver.",
            "estimated_additional_cost": net_additional_cost,
            "refund_opportunities": {
                "original_ticket_price": original_price,
                "estimated_refund_amount": estimated_refund,
                "eligible": True,
                "policy_waiver_code": "IRCTC-INV-DELAY-75PCT",
            },
            "actions": proposed_actions,
            "alternatives_considered": [alt.model_dump() if hasattr(alt, "model_dump") else alt for alt in opt_result.alternatives],
            "hotel_booking_id": hotel_booking_ref,
            "original_booking_id": disrupted_booking_ref,
            "original_transport_id": original_transport_id,
            "new_transport_id": selected_opt.get("transport_id", "TRN124"),
            "new_check_in": selected_opt.get("arrival", "2026-10-20T21:30:00"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workflow_stage": "HUMAN_REVIEW",
            "is_executed": False,
            "is_approved": False,
            "is_feasible": True,
            "active_constraints": active_constraints or {},
            "rejection_feedback": rejection_feedback or {},
            "revision_count": revision_count,
        }

        # 5. Persist to SQLite if db session is available
        if db:
            try:
                # Find matching disruption record if id was provided or query latest
                disruption_record = None
                if disruption_id:
                    disruption_record = db.query(Disruption).filter(Disruption.id == disruption_id).first()
                else:
                    disruption_record = (
                        db.query(Disruption)
                        .filter(Disruption.journey_id == journey_id)
                        .order_by(Disruption.id.desc())
                        .first()
                    )

                if disruption_record:
                    disruption_record.status = DisruptionStatus.PLAN_GENERATED
                    recovery_plan_data["disruption_id"] = disruption_record.id

                plan_record = RecoveryPlan(
                    journey_id=journey_id,
                    disruption_id=disruption_record.id if disruption_record else 1,
                    status=RecoveryPlanStatus.PLAN_GENERATED,
                    summary=summary_text,
                    reasoning_explanation=recovery_plan_data["reasoning_explanation"],
                    estimated_additional_cost=net_additional_cost,
                    refund_opportunities=recovery_plan_data["refund_opportunities"],
                    actions=proposed_actions,
                    alternatives_considered=recovery_plan_data["alternatives_considered"],
                    rejection_feedback=rejection_feedback,
                    active_constraints=active_constraints,
                    revision_count=revision_count,
                )
                db.add(plan_record)
                db.commit()
                db.refresh(plan_record)
                recovery_plan_data["db_plan_id"] = plan_record.id
                logger.info(f"Persisted proposed recovery plan ID={plan_record.id} with status=PROPOSED (no execution).")
            except Exception as db_err:
                logger.warning(f"Failed to persist RecoveryPlan to database: {db_err}")

        return recovery_plan_data


recovery_planner = RecoveryPlanner()
