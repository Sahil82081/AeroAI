"""
Stage 7: Autonomous Recovery Agent Workflow using LangGraph.
Implements an 8-node stateful multi-agent workflow:
    1. Disruption Analysis Agent
    2. Journey Impact Agent
    3. Alternative Search Agent
    4. Constraint/Optimization Agent (Google OR-Tools CP-SAT)
    5. Recovery Decision Agent (Confidence, Validation, Action Approval Rules, Reasoning)
    6. Action Agent (Supplier Adapter Execution with Retry & Fallback Logic)
    7. Verification Agent (Post-Execution Audit & Conditional Retry Routing)
    8. Notification Agent (Traveler & Stakeholder Alerts)
"""
from datetime import datetime, UTC
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from app.schemas.optimization_schemas import (
    OptimizationRequest,
    OptimizationConstraints,
    TravelerPreferences,
    OptimizationWeights,
    CandidateAlternativeInput
)
from app.modules.optimization.ortools_optimizer import ortools_recovery_optimizer
from app.modules.suppliers.service import supplier_service
from app.modules.suppliers.interfaces import SupplierAdapterException
from app.modules.events.event_bus import event_bus


class RecoveryAgentState(TypedDict, total=False):
    """Structured state passed between all 8 specialized LangGraph agents."""
    journey_id: str
    disruption: Dict[str, Any]
    affected_bookings: List[Dict[str, Any]]
    unaffected_bookings: List[Dict[str, Any]]
    missed_connections: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    constraints_config: Dict[str, Any]
    preferences_config: Dict[str, Any]
    optimization_result: Dict[str, Any]
    selected_plan: Dict[str, Any]
    confidence_score: float
    validation: Dict[str, Any]
    approval_rules: Dict[str, Any]
    approval_required: bool
    actions: List[Dict[str, Any]]
    verification: Dict[str, Any]
    notifications: List[Dict[str, Any]]
    agent_trace: List[Dict[str, Any]]
    retry_count: int
    max_retries: int
    simulate_transient_failures: int
    errors: List[str]


def _append_trace(state: RecoveryAgentState, agent_name: str, step_number: int, summary: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    trace = list(state.get("agent_trace") or [])
    trace.append({
        "step": step_number,
        "agent": agent_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "summary": summary,
        "metadata": metadata or {}
    })
    return trace


# ============================================================================
# 1. DISRUPTION ANALYSIS AGENT
# ============================================================================
def disruption_analysis_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 1: Validates and classifies the incoming disruption event,
    extracting delay magnitude, root cause, and revised arrival times.
    """
    disruption = dict(state.get("disruption") or {})
    dtype = str(disruption.get("type", "flight_delay")).lower()
    delay_min = int(disruption.get("delay_minutes", 240))
    origin = disruption.get("origin", "Delhi")
    destination = disruption.get("destination", "Jaipur")
    revised_arrival = disruption.get("revised_arrival") or state.get("constraints_config", {}).get("current_arrival", "4:30 PM")

    if "cancel" in dtype or delay_min >= 240:
        severity = "CRITICAL"
    elif delay_min >= 120:
        severity = "HIGH"
    elif delay_min >= 45:
        severity = "MODERATE"
    else:
        severity = "LOW"

    disruption.update({
        "classified_severity": severity,
        "delay_minutes": delay_min,
        "origin": origin,
        "destination": destination,
        "revised_arrival": revised_arrival,
        "is_carrier_fault": dtype in ("flight_delay", "flight_cancellation", "train_delay", "train_cancellation", "bus_cancellation", "delay", "cancellation"),
        "analyzed_at": datetime.now(UTC).isoformat()
    })

    summary = (
        f"Classified {dtype.upper()} ({delay_min}m delay) as {severity} severity. "
        f"Hub arrival shifted to {revised_arrival} for corridor {origin} -> {destination}."
    )
    trace = _append_trace(state, "1. Disruption Analysis Agent", 1, summary, {"severity": severity, "delay_minutes": delay_min})

    return {
        "disruption": disruption,
        "agent_trace": trace
    }


# ============================================================================
# 2. JOURNEY IMPACT AGENT
# ============================================================================
def journey_impact_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 2: Evaluates how the disruption cascades across downstream bookings
    (missed train/flight connections, threatened hotel check-ins, unaffected next-day activities).
    """
    disruption = state.get("disruption") or {}
    existing_affected = state.get("affected_bookings")
    existing_unaffected = state.get("unaffected_bookings")
    existing_missed = state.get("missed_connections")

    origin = disruption.get("origin", "Delhi")
    destination = disruption.get("destination", "Jaipur")
    revised_arrival = disruption.get("revised_arrival", "4:30 PM")
    c_cfg = state.get("constraints_config") or {}
    hotel_cutoff = c_cfg.get("hotel_latest_checkin", "10:00 PM")

    if existing_affected is None:
        affected_bookings = [
            {
                "booking_id": disruption.get("disrupted_booking_ref", "6E-205"),
                "type": "flight",
                "title": f"Inbound Flight to {origin}",
                "status": "DELAYED",
                "revised_arrival": revised_arrival,
                "original_price": 5850.0
            },
            {
                "booking_id": disruption.get("missed_booking_ref", "12015-SHT"),
                "type": "train",
                "title": f"Original {origin} -> {destination} Train",
                "status": "MISSED_CONNECTION",
                "scheduled_departure": "1:30 PM",
                "original_price": 800.0
            },
            {
                "booking_id": disruption.get("hotel_booking_ref", "HTL-JAI-101"),
                "type": "hotel",
                "hotel_id": "HTL101",
                "title": f"The Heritage Palace {destination}",
                "status": "LATE_CHECKIN_AT_RISK",
                "latest_checkin": hotel_cutoff,
                "original_price": 5400.0
            }
        ]
    else:
        affected_bookings = list(existing_affected)

    if existing_unaffected is None:
        unaffected_bookings = [
            {
                "booking_id": "GYG-77412",
                "type": "activity",
                "title": f"Next-Day {destination} Heritage Guided Tour",
                "status": "UNAFFECTED"
            }
        ]
    else:
        unaffected_bookings = list(existing_unaffected)

    if existing_missed is None:
        missed_connections = [
            {
                "from_booking": disruption.get("disrupted_booking_ref", "6E-205"),
                "to_booking": disruption.get("missed_booking_ref", "12015-SHT"),
                "reason": f"Inbound arrival at {revised_arrival} misses scheduled departure of {origin}->{destination} connection."
            }
        ]
    else:
        missed_connections = list(existing_missed)

    summary = (
        f"Identified {len(affected_bookings)} affected bookings, {len(missed_connections)} missed connection(s), "
        f"and {len(unaffected_bookings)} unaffected downstream segment(s). Hotel latest check-in constraint: {hotel_cutoff}."
    )
    trace = _append_trace(state, "2. Journey Impact Agent", 2, summary, {
        "affected_count": len(affected_bookings),
        "missed_connections": len(missed_connections)
    })

    return {
        "affected_bookings": affected_bookings,
        "unaffected_bookings": unaffected_bookings,
        "missed_connections": missed_connections,
        "agent_trace": trace
    }


# ============================================================================
# 3. ALTERNATIVE SEARCH AGENT
# ============================================================================
def alternative_search_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 3: Queries the decoupled SupplierIntegrationService (or uses supplied scenario options)
    with automatic retry on transient supplier errors.
    """
    provided_alternatives = state.get("alternatives")
    disruption = state.get("disruption") or {}
    origin = disruption.get("origin", "Delhi")
    destination = disruption.get("destination", "Jaipur")

    if provided_alternatives and len(provided_alternatives) > 0:
        alternatives = list(provided_alternatives)
        source = "scenario_candidates"
    else:
        # Query Mock Supplier Ecosystem via SupplierIntegrationService with retry logic
        alternatives = []
        source = "mock_supplier_ecosystem"
        last_err = None
        for attempt in range(1, 4):
            try:
                multimodal = supplier_service.search_multimodal_alternatives(
                    origin=origin,
                    destination=destination,
                    min_seats=1
                )
                for item in multimodal.get("alternatives", []):
                    alternatives.append({
                        "transport_id": item["transport_id"],
                        "name": f"{item['provider']} ({item.get('vehicle_number', item['transport_id'])})",
                        "supplier_type": item.get("supplier_type", "train"),
                        "provider": item["provider"],
                        "vehicle_number": item.get("vehicle_number", item["transport_id"]),
                        "origin": item["origin"],
                        "destination": item["destination"],
                        "departure": item["departure"],
                        "arrival": item["arrival"],
                        "price": float(item["price"]),
                        "currency": item.get("currency", "INR"),
                        "available_seats": int(item.get("available_seats", 10)),
                        "number_of_changes": 0,
                        "reliability": 0.94 if item.get("supplier_type") == "train" else 0.89,
                        "duration_minutes": item.get("duration_minutes")
                    })
                break
            except Exception as exc:
                last_err = str(exc)

        if not alternatives and last_err:
            errors = list(state.get("errors") or [])
            errors.append(f"AlternativeSearchAgent supplier error: {last_err}")
            return {"alternatives": [], "errors": errors}

    summary = f"Retrieved {len(alternatives)} candidate transport options for {origin} -> {destination} (source: {source})."
    trace = _append_trace(state, "3. Alternative Search Agent", 3, summary, {"candidates_found": len(alternatives), "source": source})

    return {
        "alternatives": alternatives,
        "agent_trace": trace
    }


# ============================================================================
# 4. CONSTRAINT / OPTIMIZATION AGENT (Google OR-Tools CP-SAT)
# ============================================================================
def constraint_optimization_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 4: Formulates the recovery constraints and invokes the Google OR-Tools CP-SAT
    mathematical optimizer to find the globally optimal feasible alternative.
    """
    c_cfg = state.get("constraints_config") or {}
    p_cfg = state.get("preferences_config") or {}
    disruption = state.get("disruption") or {}

    current_arrival = c_cfg.get("current_arrival") or disruption.get("revised_arrival") or "4:30 PM"
    hotel_latest_checkin = c_cfg.get("hotel_latest_checkin", "10:00 PM")
    min_connection_minutes = int(c_cfg.get("min_connection_minutes", 45))
    required_seats = int(c_cfg.get("required_seats", 1))
    max_budget = p_cfg.get("max_budget", 1000.0)

    weights_dict = p_cfg.get("weights") or {}
    weights = OptimizationWeights(
        price=float(weights_dict.get("price", 0.30)),
        travel_time=float(weights_dict.get("travel_time", 0.25)),
        waiting_time=float(weights_dict.get("waiting_time", 0.15)),
        number_of_changes=float(weights_dict.get("number_of_changes", 0.10)),
        arrival_time=float(weights_dict.get("arrival_time", 0.10)),
        reliability=float(weights_dict.get("reliability", 0.10))
    )

    candidate_inputs = [
        CandidateAlternativeInput(
            transport_id=alt["transport_id"],
            name=alt.get("name") or f"{alt.get('provider', 'Carrier')} ({alt['transport_id']})",
            supplier_type=alt.get("supplier_type", "train"),
            provider=alt.get("provider", "Indian Railways"),
            vehicle_number=alt.get("vehicle_number"),
            origin=alt.get("origin", "Delhi"),
            destination=alt.get("destination", "Jaipur"),
            departure=alt["departure"],
            arrival=alt["arrival"],
            price=float(alt["price"]),
            currency=alt.get("currency", "INR"),
            available_seats=int(alt.get("available_seats", 10)),
            number_of_changes=int(alt.get("number_of_changes", 0)),
            reliability=float(alt.get("reliability", 0.92)),
            duration_minutes=alt.get("duration_minutes")
        )
        for alt in (state.get("alternatives") or [])
    ]

    opt_request = OptimizationRequest(
        origin=disruption.get("origin", "Delhi"),
        destination=disruption.get("destination", "Jaipur"),
        available_alternatives=candidate_inputs,
        constraints=OptimizationConstraints(
            current_arrival=current_arrival,
            hotel_latest_checkin=hotel_latest_checkin,
            min_connection_minutes=min_connection_minutes,
            required_seats=required_seats
        ),
        traveler_preferences=TravelerPreferences(
            max_budget=float(max_budget) if max_budget is not None else None,
            allowed_modes=p_cfg.get("allowed_modes"),
            excluded_modes=p_cfg.get("excluded_modes") or [],
            max_changes=p_cfg.get("max_changes"),
            min_reliability=p_cfg.get("min_reliability"),
            weights=weights
        )
    )

    opt_response = ortools_recovery_optimizer.optimize(opt_request)
    opt_dict = opt_response.model_dump()

    structured_constraints = [
        {"constraint": "departure_after_arrival", "rule": f"Departure >= {current_arrival}"},
        {"constraint": "connection_time_feasible", "rule": f"Wait time >= {min_connection_minutes} minutes"},
        {"constraint": "arrival_before_hotel_checkin", "rule": f"Arrival <= {hotel_latest_checkin}"},
        {"constraint": "transport_has_availability", "rule": f"Available seats >= {required_seats}"},
        {"constraint": "passenger_preferences_respected", "rule": f"Price <= {max_budget}"}
    ]

    selected = opt_dict.get("selected_option")
    summary = (
        f"OR-Tools CP-SAT status: {opt_dict['solver_metadata'].get('status')}. "
        + (
            f"Selected {selected['name']} ({selected['transport_id']}) with objective score {opt_dict['objective_score']}."
            if selected else "No feasible option satisfied all constraints."
        )
    )
    trace = _append_trace(state, "4. Constraint/Optimization Agent", 4, summary, {
        "solver": "Google OR-Tools CP-SAT",
        "constraints_satisfied": opt_dict["constraints_satisfied"],
        "objective_score": opt_dict["objective_score"],
        "selected_transport_id": selected["transport_id"] if selected else None
    })

    return {
        "constraints": structured_constraints,
        "alternatives": opt_dict["alternatives"],
        "optimization_result": opt_dict,
        "agent_trace": trace
    }


# ============================================================================
# 5. RECOVERY DECISION AGENT (Confidence, Validation, Approval Rules & Reasoning)
# ============================================================================
def recovery_decision_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 5: Evaluates the OR-Tools mathematical solution, computes confidence,
    validates policy guardrails, enforces action approval rules (so the AI never
    blindly executes high-cost or low-confidence actions), and generates a natural-language
    decision explanation.
    """
    opt_result = state.get("optimization_result") or {}
    selected = opt_result.get("selected_option")
    constraints_satisfied = bool(opt_result.get("constraints_satisfied", False))
    c_cfg = state.get("constraints_config") or {}
    p_cfg = state.get("preferences_config") or {}

    hotel_cutoff = c_cfg.get("hotel_latest_checkin", "10:00 PM")
    max_budget = p_cfg.get("max_budget", 1000.0)
    approval_cfg = state.get("approval_rules") or {}
    auto_approve_cost_limit = float(approval_cfg.get("auto_approve_max_cost", max_budget or 1500.0))
    min_confidence_threshold = float(approval_cfg.get("min_confidence_threshold", 0.75))
    force_manual_approval = bool(approval_cfg.get("require_human_approval", False))

    if not selected or not constraints_satisfied:
        confidence = 0.25
        validation = {
            "is_valid": False,
            "constraints_verified": False,
            "reason": "No candidate option satisfied all hard OR-Tools constraints."
        }
        selected_plan = {
            "status": "ESCALATED_TO_HUMAN",
            "selected_option": None,
            "why_selected": (
                "No automated recovery option could satisfy all hard constraints "
                f"(arrival before hotel check-in {hotel_cutoff}, feasible transfer buffer, and budget limit {max_budget}). "
                "Escalating to traveler for manual constraint relaxation."
            ),
            "confidence_score": confidence,
            "approval_required": True
        }
        trace = _append_trace(state, "5. Recovery Decision Agent", 5, "Escalated to human: no feasible option.", {"confidence": confidence})
        return {
            "selected_plan": selected_plan,
            "confidence_score": confidence,
            "validation": validation,
            "approval_required": True,
            "agent_trace": trace
        }

    # Compute confidence score based on seat availability, reliability, buffer margin, and constraint satisfaction
    rel = float(selected.get("reliability", 0.92))
    seats = int(selected.get("available_seats", 5))
    wait_min = int(selected.get("waiting_time_minutes", 45))
    min_conn = int(c_cfg.get("min_connection_minutes", 45))
    buffer_margin_bonus = 0.04 if (wait_min - min_conn) >= 15 else 0.01
    seat_bonus = 0.03 if seats >= 5 else 0.0
    confidence = round(min(0.99, 0.85 * rel + 0.12 + buffer_margin_bonus + seat_bonus), 2)

    # Allow test override of confidence if specified in approval_rules
    if "override_confidence" in approval_cfg and approval_cfg["override_confidence"] is not None:
        confidence = float(approval_cfg["override_confidence"])

    price = float(selected.get("price", 0.0))
    exceeds_auto_cost = price > auto_approve_cost_limit
    below_confidence = confidence < min_confidence_threshold
    approval_required = force_manual_approval or exceeds_auto_cost or below_confidence

    approval_reasons = []
    if force_manual_approval:
        approval_reasons.append("Traveler policy requires explicit human approval before rebooking.")
    if exceeds_auto_cost:
        approval_reasons.append(f"Option price ({selected.get('currency', 'INR')} {price}) exceeds autonomous spend limit ({auto_approve_cost_limit}).")
    if below_confidence:
        approval_reasons.append(f"Decision confidence ({confidence}) is below autonomous execution threshold ({min_confidence_threshold}).")

    # Build explicit human-readable explanation of WHY this recovery plan was selected
    opt_name = selected.get("name", selected["transport_id"])
    why_selected = (
        f"{opt_name} was selected because it is the earliest feasible {selected.get('supplier_type', 'transport')} "
        f"(departing {selected.get('departure')} after the {selected.get('waiting_time_minutes')}m connection buffer) "
        f"that arrives at {selected.get('arrival')} before the hotel's latest check-in time ({hotel_cutoff}) "
        f"while keeping the cost ({selected.get('currency', 'INR')} {price}) within the traveler's configured limit ({max_budget})."
    )

    # Also summarize why other alternatives were rejected
    rejected_summaries = []
    for alt in (state.get("alternatives") or []):
        if alt["transport_id"] == selected["transport_id"]:
            continue
        if not alt.get("feasible", False):
            rejected_summaries.append(f"{alt.get('name', alt['transport_id'])} was rejected ({'; '.join(alt.get('violation_reasons', []))})")
        else:
            rejected_summaries.append(
                f"{alt.get('name', alt['transport_id'])} was feasible but had a worse OR-Tools objective penalty ({alt.get('objective_score')} vs {opt_result.get('objective_score')})"
            )

    if rejected_summaries:
        why_selected += " Rejected alternatives: " + "; ".join(rejected_summaries) + "."

    validation = {
        "is_valid": True,
        "constraints_verified": True,
        "confidence_score": confidence,
        "min_confidence_threshold": min_confidence_threshold,
        "auto_approve_max_cost": auto_approve_cost_limit,
        "approval_required": approval_required,
        "approval_reasons": approval_reasons
    }

    selected_plan = {
        "status": "PENDING_TRAVELER_APPROVAL" if approval_required else "APPROVED_FOR_AUTONOMOUS_EXECUTION",
        "selected_option": selected,
        "objective_score": opt_result.get("objective_score", 0.0),
        "confidence_score": confidence,
        "approval_required": approval_required,
        "approval_reasons": approval_reasons,
        "why_selected": why_selected,
        "detailed_solver_explanation": opt_result.get("explanation", "")
    }

    summary = (
        f"Decision validated (confidence={confidence}). "
        f"Status: {selected_plan['status']}. {why_selected}"
    )
    trace = _append_trace(state, "5. Recovery Decision Agent", 5, summary, {
        "confidence_score": confidence,
        "approval_required": approval_required,
        "selected_transport_id": selected["transport_id"]
    })

    return {
        "selected_plan": selected_plan,
        "confidence_score": confidence,
        "validation": validation,
        "approval_required": approval_required,
        "agent_trace": trace
    }


# ============================================================================
# 6. ACTION AGENT (Execution with Approval Guardrails, Retry & Fallback)
# ============================================================================
def action_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 6: Executes recovery actions via the decoupled SupplierIntegrationService.
    - Respects approval rules: if approval_required is True, stages rebooking as AWAITING_APPROVAL
      instead of blindly charging the traveler.
    - Implements retry & fallback logic for transient supplier API errors.
    """
    selected_plan = state.get("selected_plan") or {}
    selected_opt = selected_plan.get("selected_option")
    approval_required = bool(state.get("approval_required", False))
    retry_count = int(state.get("retry_count", 0))
    sim_failures_remaining = int(state.get("simulate_transient_failures", 0))

    actions: List[Dict[str, Any]] = []
    errors: List[str] = list(state.get("errors") or [])

    if not selected_opt:
        actions.append({
            "action_type": "MANUAL_ESCALATION",
            "status": "ESCALATED",
            "description": "No feasible option found; escalated to human travel desk."
        })
        trace = _append_trace(state, "6. Action Agent", 6, "No feasible option to execute; staged manual escalation.")
        return {"actions": actions, "agent_trace": trace}

    # Check if a transient supplier error is being simulated on this attempt
    if sim_failures_remaining > 0:
        sim_failures_remaining -= 1
        errors.append(f"Transient supplier timeout on attempt #{retry_count + 1} for {selected_opt['transport_id']}.")
        actions.append({
            "action_type": "REBOOK_TRANSPORT",
            "target_id": selected_opt["transport_id"],
            "status": "FAILED_TRANSIENT",
            "attempt": retry_count + 1,
            "error": "MOCK_SUPPLIER_GATEWAY_TIMEOUT (504)"
        })
        trace = _append_trace(
            state,
            "6. Action Agent",
            6,
            f"Transient supplier error on attempt #{retry_count + 1}; delegating to Verification Agent for retry.",
            {"attempt": retry_count + 1, "status": "FAILED_TRANSIENT"}
        )
        return {
            "actions": actions,
            "simulate_transient_failures": sim_failures_remaining,
            "errors": errors,
            "agent_trace": trace
        }

    # Action 1: Rebook alternative transport (or stage for approval if approval_required=True)
    if approval_required:
        actions.append({
            "action_type": "REBOOK_TRANSPORT",
            "target_id": selected_opt["transport_id"],
            "provider": selected_opt.get("provider"),
            "price": selected_opt.get("price"),
            "currency": selected_opt.get("currency", "INR"),
            "status": "AWAITING_TRAVELER_APPROVAL",
            "description": (
                f"Staged rebooking onto {selected_opt.get('name')} ({selected_opt['transport_id']}) "
                f"departing {selected_opt.get('departure')} — awaiting traveler approval."
            ),
            "approval_reasons": selected_plan.get("approval_reasons", [])
        })
    else:
        # Execute via SupplierIntegrationService (if transport_id is in mock dataset, else record simulated confirmation)
        tid = selected_opt["transport_id"]
        try:
            conf = supplier_service.rebook_booking({
                "original_booking_ref": "12015-SHT",
                "transport_id": tid,
                "passenger_name": "Sahil Sharma",
                "seats": 1,
                "reason": "AUTONOMOUS_DISRUPTION_RECOVERY",
                "waive_change_fee": True
            })
        except SupplierAdapterException:
            # Scenario uses custom IDs like TRAIN-B not in default mock store; rebook against TRN124 or issue mock confirmation
            conf = {
                "confirmation_number": f"MOCK-AUT-{tid.upper()}",
                "transport_id": tid,
                "provider": selected_opt.get("provider", "Indian Railways"),
                "departure": selected_opt.get("departure"),
                "arrival": selected_opt.get("arrival"),
                "total_charged": selected_opt.get("price"),
                "currency": selected_opt.get("currency", "INR"),
                "status": "CONFIRMED",
                "is_mock_api": True,
                "simulated": True
            }

        actions.append({
            "action_type": "REBOOK_TRANSPORT",
            "target_id": tid,
            "status": "EXECUTED",
            "confirmation": conf,
            "description": (
                f"Rebooked traveler onto {selected_opt.get('name')} ({tid}) "
                f"with confirmation {conf.get('confirmation_number')}."
            )
        })

    # Action 2: Generate Refund / Waiver Claim for Missed Connection
    refund_res = supplier_service.request_refund({
        "booking_reference": "12015-SHT",
        "transport_id": "TRN123",
        "supplier_type": "train",
        "original_price": 800.0,
        "currency": selected_opt.get("currency", "INR"),
        "reason": "INVOLUNTARY_MISSED_CONNECTION_DISRUPTION",
        "is_disruption_waiver": True
    })
    actions.append({
        "action_type": "CLAIM_REFUND",
        "target_id": "12015-SHT",
        "status": "EXECUTED",
        "refund_details": refund_res,
        "description": (
            f"Submitted involuntary disruption refund claim ({refund_res.get('refund_transaction_id')}) "
            f"for missed connection — {refund_res.get('currency')} {refund_res.get('refund_amount')} approved."
        )
    })

    # Action 3: Update Downstream Hotel Check-in Time
    hotel_mod = supplier_service.modify_hotel({
        "booking_reference": "HTL-JAI-101",
        "hotel_id": "HTL101",
        "new_check_in": selected_opt.get("arrival", "9:00 PM"),
        "late_arrival_notice": True,
        "notes": f"Updated arrival to {selected_opt.get('arrival')} via {selected_opt.get('name')}."
    })
    actions.append({
        "action_type": "MODIFY_HOTEL_CHECKIN",
        "target_id": "HTL-JAI-101",
        "status": "EXECUTED",
        "hotel_confirmation": hotel_mod,
        "description": (
            f"Notified {hotel_mod.get('hotel_name')} to update check-in to {selected_opt.get('arrival')} "
            f"(no-show penalty waived)."
        )
    })

    summary = (
        f"Processed {len(actions)} recovery actions "
        f"(rebook={'AWAITING_APPROVAL' if approval_required else 'EXECUTED'}, refund=EXECUTED, hotel_modify=EXECUTED)."
    )
    trace = _append_trace(state, "6. Action Agent", 6, summary, {
        "actions_count": len(actions),
        "attempt": retry_count + 1
    })

    return {
        "actions": actions,
        "simulate_transient_failures": sim_failures_remaining,
        "agent_trace": trace
    }


# ============================================================================
# 7. VERIFICATION AGENT (Post-Action Audit & Retry Trigger)
# ============================================================================
def verification_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 7: Audits the executed or staged actions, checks whether a transient supplier
    failure occurred that requires retrying the Action Agent, and verifies journey consistency.
    """
    actions = state.get("actions") or []
    retry_count = int(state.get("retry_count", 0))
    max_retries = int(state.get("max_retries", 2))

    has_transient_failure = any(a.get("status") == "FAILED_TRANSIENT" for a in actions)

    if has_transient_failure and retry_count < max_retries:
        new_retry_count = retry_count + 1
        verification = {
            "verified": False,
            "status": "RETRY_SCHEDULED",
            "retry_count": new_retry_count,
            "max_retries": max_retries,
            "reason": f"Detected transient supplier failure; scheduling automatic retry #{new_retry_count} of {max_retries}."
        }
        trace = _append_trace(state, "7. Verification Agent", 7, verification["reason"], verification)
        return {
            "verification": verification,
            "retry_count": new_retry_count,
            "agent_trace": trace
        }

    checks = [
        {"check": "transport_rebooking_or_approval_staged", "passed": any(a["action_type"] in ("REBOOK_TRANSPORT", "MANUAL_ESCALATION") and a["status"] != "FAILED_TRANSIENT" for a in actions)},
        {"check": "hotel_late_arrival_protected", "passed": any(a["action_type"] == "MODIFY_HOTEL_CHECKIN" for a in actions) or any(a["action_type"] == "MANUAL_ESCALATION" for a in actions)},
        {"check": "refund_opportunity_captured", "passed": any(a["action_type"] == "CLAIM_REFUND" for a in actions) or any(a["action_type"] == "MANUAL_ESCALATION" for a in actions)},
        {"check": "downstream_hotel_cutoff_respected", "passed": bool(state.get("optimization_result", {}).get("constraints_satisfied", False))}
    ]
    all_passed = all(c["passed"] for c in checks)

    verification = {
        "verified": all_passed,
        "status": "VERIFIED_CONSISTENT" if all_passed else "VERIFIED_WITH_ESCALATION",
        "retries_used": retry_count,
        "checks": checks,
        "verified_at": datetime.now(UTC).isoformat()
    }
    summary = f"Verification complete: status={verification['status']}, retries_used={retry_count}."
    trace = _append_trace(state, "7. Verification Agent", 7, summary, verification)

    return {
        "verification": verification,
        "agent_trace": trace
    }


def _should_retry_or_notify(state: RecoveryAgentState) -> str:
    """Conditional routing edge out of Verification Agent."""
    ver = state.get("verification") or {}
    if ver.get("status") == "RETRY_SCHEDULED":
        return "action_agent"
    return "notification_agent"


# ============================================================================
# 8. NOTIFICATION AGENT
# ============================================================================
def notification_agent(state: RecoveryAgentState) -> Dict[str, Any]:
    """
    Node 8: Dispatches structured notifications to the traveler and affected stakeholders
    summarizing the disruption, selected recovery plan, decision reasoning, and refund status.
    """
    selected_plan = state.get("selected_plan") or {}
    selected_opt = selected_plan.get("selected_option")
    approval_required = bool(state.get("approval_required", False))
    why_selected = selected_plan.get("why_selected", "")

    notifications: List[Dict[str, Any]] = []

    if selected_opt:
        subject = (
            f"[Action Required] Approve Recovery Plan: {selected_opt.get('name')}"
            if approval_required
            else f"[Recovered] Itinerary Updated: Rebooked onto {selected_opt.get('name')}"
        )
        notifications.append({
            "recipient": "traveler@example.com",
            "channel": "EMAIL_AND_WEBSOCKET",
            "status": "SENT",
            "subject": subject,
            "message": (
                f"{why_selected} "
                + (
                    "Please review and approve the staged rebooking in your dashboard."
                    if approval_required
                    else "Your ticket, refund claim, and hotel arrival window have been updated automatically."
                )
            ),
            "sent_at": datetime.now(UTC).isoformat(),
            "simulated": True
        })
        notifications.append({
            "recipient": "frontdesk@heritagepalacejaipur.com",
            "channel": "SUPPLIER_CRS_NOTICE",
            "status": "SENT",
            "subject": f"Late Check-In Hold Notice for Guest Sahil Sharma (Arrival {selected_opt.get('arrival')})",
            "message": f"Guest arriving via {selected_opt.get('name')} at {selected_opt.get('arrival')}. Room hold confirmed.",
            "sent_at": datetime.now(UTC).isoformat(),
            "simulated": True
        })
    else:
        notifications.append({
            "recipient": "traveler@example.com",
            "channel": "EMAIL_AND_WEBSOCKET",
            "status": "SENT",
            "subject": "[Urgent] Disruption Recovery Requires Manual Review",
            "message": why_selected,
            "sent_at": datetime.now(UTC).isoformat(),
            "simulated": True
        })

    trace = _append_trace(
        state,
        "8. Notification Agent",
        8,
        f"Dispatched {len(notifications)} notifications to traveler and downstream hospitality providers.",
        {"notifications_sent": len(notifications)}
    )

    event_bus.publish("LANGGRAPH_RECOVERY_WORKFLOW_COMPLETED", {
        "journey_id": state.get("journey_id"),
        "status": selected_plan.get("status"),
        "selected_transport_id": selected_opt["transport_id"] if selected_opt else None,
        "confidence_score": state.get("confidence_score"),
        "approval_required": approval_required,
        "retries_used": state.get("retry_count", 0)
    })

    return {
        "notifications": notifications,
        "agent_trace": trace
    }


# ============================================================================
# BUILD & COMPILE THE LANGGRAPH STATE MACHINE
# ============================================================================
def build_recovery_langgraph():
    workflow = StateGraph(RecoveryAgentState)

    workflow.add_node("disruption_analysis_agent", disruption_analysis_agent)
    workflow.add_node("journey_impact_agent", journey_impact_agent)
    workflow.add_node("alternative_search_agent", alternative_search_agent)
    workflow.add_node("constraint_optimization_agent", constraint_optimization_agent)
    workflow.add_node("recovery_decision_agent", recovery_decision_agent)
    workflow.add_node("action_agent", action_agent)
    workflow.add_node("verification_agent", verification_agent)
    workflow.add_node("notification_agent", notification_agent)

    workflow.add_edge(START, "disruption_analysis_agent")
    workflow.add_edge("disruption_analysis_agent", "journey_impact_agent")
    workflow.add_edge("journey_impact_agent", "alternative_search_agent")
    workflow.add_edge("alternative_search_agent", "constraint_optimization_agent")
    workflow.add_edge("constraint_optimization_agent", "recovery_decision_agent")
    workflow.add_edge("recovery_decision_agent", "action_agent")
    workflow.add_edge("action_agent", "verification_agent")

    # Conditional edge for automatic retry loop if Verification Agent detects transient supplier error
    workflow.add_conditional_edges(
        "verification_agent",
        _should_retry_or_notify,
        {
            "action_agent": "action_agent",
            "notification_agent": "notification_agent"
        }
    )
    workflow.add_edge("notification_agent", END)

    return workflow.compile()


compiled_recovery_graph = build_recovery_langgraph()


LANGGRAPH_MERMAID_DIAGRAM = """flowchart TD
    START(["Disruption Event Trigger"]) --> N1["1. Disruption Analysis Agent"]
    N1 --> N2["2. Journey Impact Agent"]
    N2 --> N3["3. Alternative Search Agent"]
    N3 --> N4["4. Constraint / Optimization Agent (Google OR-Tools CP-SAT)"]
    N4 --> N5["5. Recovery Decision Agent (Confidence & Approval Guardrails)"]
    N5 --> N6["6. Action Agent (Rebook / Refund / Hotel Modify)"]
    N6 --> N7{"7. Verification Agent"}
    N7 -- "Transient Error & Retry < Max" --> N6
    N7 -- "Verified Consistent" --> N8["8. Notification Agent"]
    N8 --> END_NODE(["Updated Journey & Notifications"])
"""


class AutonomousRecoveryWorkflowRunner:
    """High-level runner for executing and inspecting the 8-agent LangGraph recovery workflow."""

    @staticmethod
    def run_workflow(initial_state: Dict[str, Any]) -> Dict[str, Any]:
        defaults: RecoveryAgentState = {
            "journey_id": str(initial_state.get("journey_id", "JRN-101")),
            "disruption": initial_state.get("disruption") or {
                "type": "flight_delay",
                "delay_minutes": 240,
                "origin": "Delhi",
                "destination": "Jaipur",
                "revised_arrival": "4:30 PM"
            },
            "alternatives": initial_state.get("alternatives") or [],
            "constraints_config": initial_state.get("constraints_config") or {
                "current_arrival": "4:30 PM",
                "hotel_latest_checkin": "10:00 PM",
                "min_connection_minutes": 45,
                "required_seats": 1
            },
            "preferences_config": initial_state.get("preferences_config") or {
                "max_budget": 1000.0,
                "weights": {
                    "price": 0.30,
                    "travel_time": 0.25,
                    "waiting_time": 0.15,
                    "number_of_changes": 0.10,
                    "arrival_time": 0.10,
                    "reliability": 0.10
                }
            },
            "approval_rules": initial_state.get("approval_rules") or {
                "auto_approve_max_cost": 1000.0,
                "min_confidence_threshold": 0.75,
                "require_human_approval": False
            },
            "retry_count": 0,
            "max_retries": int(initial_state.get("max_retries", 2)),
            "simulate_transient_failures": int(initial_state.get("simulate_transient_failures", 0)),
            "agent_trace": [],
            "errors": []
        }
        if "affected_bookings" in initial_state and initial_state["affected_bookings"] is not None:
            defaults["affected_bookings"] = initial_state["affected_bookings"]

        final_state = compiled_recovery_graph.invoke(defaults)
        return dict(final_state)

    @staticmethod
    def get_graph_documentation() -> Dict[str, Any]:
        return {
            "framework": "LangGraph StateGraph",
            "nodes": [
                {"id": "disruption_analysis_agent", "step": 1, "name": "Disruption Analysis Agent", "role": "Classifies disruption type, delay magnitude, carrier fault, and severity."},
                {"id": "journey_impact_agent", "step": 2, "name": "Journey Impact Agent", "role": "Determines downstream missed connections, affected bookings, and unaffected segments."},
                {"id": "alternative_search_agent", "step": 3, "name": "Alternative Search Agent", "role": "Queries decoupled Flight, Train, and Bus Supplier Adapters for candidate options."},
                {"id": "constraint_optimization_agent", "step": 4, "name": "Constraint/Optimization Agent", "role": "Solves 0-1 Integer Program via Google OR-Tools CP-SAT under hard time/seat/budget constraints."},
                {"id": "recovery_decision_agent", "step": 5, "name": "Recovery Decision Agent", "role": "Computes confidence score, checks action approval guardrails, and explains WHY the plan was selected."},
                {"id": "action_agent", "step": 6, "name": "Action Agent", "role": "Executes approved rebooking, refund claim, and hotel late check-in notice (or stages for approval)."},
                {"id": "verification_agent", "step": 7, "name": "Verification Agent", "role": "Verifies post-action consistency and triggers conditional retry loop on transient supplier failures."},
                {"id": "notification_agent", "step": 8, "name": "Notification Agent", "role": "Sends structured alerts to the traveler and downstream hotel/transport providers."}
            ],
            "mermaid_diagram": LANGGRAPH_MERMAID_DIAGRAM
        }


recovery_workflow_runner = AutonomousRecoveryWorkflowRunner()
