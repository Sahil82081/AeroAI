"""
Stage 12: End-to-End System Demo Orchestrator.

Executes and verifies the complete 17-step Golden Triangle Disruption Recovery Scenario:
- Initial Journey:
  1. Flight (AI-202): Mumbai -> Delhi, 10:00 AM -> 12:00 PM
  2. Train (12015-SHT / TRN123): Delhi -> Jaipur, 1:30 PM -> 5:30 PM
  3. Hotel (HTL-JAI-101): Jaipur, Check-in 6:00 PM (Latest cutoff 10:00 PM)
  4. Tour (TOUR-JAI-01): Jaipur, Next day 9:00 AM -> 1:00 PM
- Trigger:
  Flight delay of 4 hours (240 minutes) -> Flight arrives at 4:00 PM (16:00).
- Verifies all 17 expected system behaviors across:
  REAL subsystems: NetworkX Journey Graph, Impact Analysis Agent, Google OR-Tools CP-SAT,
  LangGraph 8-Node Workflow, Kafka Event Broker + WebSocket, Fact-Grounded Notification Validator.
  SIMULATED subsystems: Mock Airline, Railway, Bus, and Hotel Supplier APIs.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.models import (
    User,
    Journey,
    Booking,
    BookingType,
    BookingStatus,
)
from app.modules.journeys.graph_builder import JourneyGraphEngine
from app.schemas.disruption_schemas import DisruptionSimulationRequest
from app.modules.disruptions.disruption_engine import DisruptionSimulatorEngine
from app.schemas.optimization_schemas import (
    OptimizationRequest,
    OptimizationConstraints,
    TravelerPreferences,
    OptimizationWeights,
)
from app.modules.optimization.ortools_optimizer import ORToolsRecoveryOptimizer
from app.modules.ai_agents.recovery_graph import recovery_workflow_runner
from app.modules.recovery.action_executor import (
    recovery_action_executor,
    IdempotencyAndAuditStore,
)
from app.modules.events.pipeline_consumers import event_pipeline
from app.schemas.event_schemas import EventDrivenDisruptionRequest
from app.modules.events.kafka_engine import kafka_broker
from app.modules.notifications.notification_agent import notification_agent_service
from app.schemas.notification_schemas import StructuredRecoveryFacts
from app.modules.suppliers.service import supplier_service


REAL_VS_SIMULATED_MANIFEST = {
    "REAL": [
        "AI Reasoning & Impact Cascade Explanation (ImpactAnalysisAgent + Gemini/Heuristic)",
        "NetworkX Directed Acyclic Journey Graph & Connection Risk Engine (SAFE / TIGHT / IMPOSSIBLE)",
        "Downstream Dependency & Time-Gap Impact Analysis",
        "Mathematical Constraint Optimization using Google OR-Tools CP-SAT (0-1 Integer Linear Programming)",
        "8-Node Autonomous Recovery Agent Workflow using LangGraph (StateGraph)",
        "Event-Driven Architecture with Apache Kafka Topics, Correlation IDs, Idempotent Consumers, Retries & DLQ",
        "Real-Time WebSocket Streaming (/api/v1/events/ws) & Anti-Hallucination Fact-Grounding Validator",
    ],
    "SIMULATED": [
        "Mock Airline Supplier REST API (GET /flights/search, POST /bookings/rebook, cancel, refund)",
        "Mock Railway Supplier REST API (GET /trains/search, POST /bookings/rebook, cancel, refund)",
        "Mock Bus Supplier REST API (GET /buses/search, POST /bookings/rebook, cancel, refund)",
        "Mock Hotel Supplier REST API (GET /hotels/search, POST /hotel/modify)",
        "Simulated Travel Seat Inventory, Pricing, Refund Rules & Email Delivery Inbox",
    ],
}


class EndToEndDemoOrchestrator:
    """
    Runs the canonical 17-step Golden Triangle E2E Scenario from initial booking creation
    through 4-hour flight delay, Kafka cascade, OR-Tools optimization, mock supplier rebooking,
    graph recalculation, and complete audit trail generation.
    """

    @classmethod
    def run_golden_triangle_scenario(cls, db: Session) -> Dict[str, Any]:
        # Reset clean simulation state
        supplier_service.reset_simulation_state()
        IdempotencyAndAuditStore.clear()
        kafka_broker.reset_broker()
        event_pipeline._registered = False
        event_pipeline.register_all_consumers()
        notification_agent_service.clear_history()

        # Ensure demo user exists
        user = db.query(User).filter(User.email == "traveler@example.com").first()
        if not user:
            user = User(
                email="traveler@example.com",
                full_name="Aarav Sharma",
                hashed_password="demo_hashed_password",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create clean E2E Demo Journey
        journey = Journey(
            user_id=user.id,
            title="E2E Demo: Mumbai -> Delhi -> Jaipur Golden Triangle",
            description="Canonical Stage 12 End-to-End Verification Scenario",
            start_date=datetime(2026, 10, 20, 10, 0, 0),
            end_date=datetime(2026, 10, 21, 13, 0, 0),
            status="ACTIVE",
        )
        db.add(journey)
        db.commit()
        db.refresh(journey)

        # Create the 4 canonical bookings:
        # 1. Flight: Mumbai -> Delhi (10:00 AM -> 12:00 PM)
        flight_booking = Booking(
            journey_id=journey.id,
            reference_number="AI-202",
            booking_type=BookingType.FLIGHT,
            provider_name="Air India",
            title="Air India AI-202 (Mumbai -> Delhi)",
            status=BookingStatus.CONFIRMED,
            start_time=datetime(2026, 10, 20, 10, 0, 0),
            end_time=datetime(2026, 10, 20, 12, 0, 0),
            origin="Mumbai",
            destination="Delhi",
            price=5400.0,
            currency="INR",
        )
        # 2. Train: Delhi -> Jaipur (1:30 PM -> 5:30 PM)
        train_booking = Booking(
            journey_id=journey.id,
            reference_number="12015-SHT",
            booking_type=BookingType.TRAIN,
            provider_name="Indian Railways",
            title="Ajmer Shatabdi 12015 (Delhi -> Jaipur)",
            status=BookingStatus.CONFIRMED,
            start_time=datetime(2026, 10, 20, 13, 30, 0),
            end_time=datetime(2026, 10, 20, 17, 30, 0),
            origin="Delhi",
            destination="Jaipur",
            price=800.0,
            currency="INR",
        )
        # 3. Hotel: Jaipur Check-in 6:00 PM
        hotel_booking = Booking(
            journey_id=journey.id,
            reference_number="HTL-JAI-101",
            booking_type=BookingType.HOTEL,
            provider_name="Rambagh Heritage Palace Jaipur",
            title="Rambagh Heritage Palace Jaipur (Check-in 6:00 PM)",
            status=BookingStatus.CONFIRMED,
            start_time=datetime(2026, 10, 20, 18, 0, 0),
            end_time=datetime(2026, 10, 21, 11, 0, 0),
            origin="Jaipur",
            destination="Jaipur",
            price=6500.0,
            currency="INR",
        )
        # 4. Tour: Jaipur Next day 9:00 AM
        tour_booking = Booking(
            journey_id=journey.id,
            reference_number="TOUR-JAI-01",
            booking_type=BookingType.ACTIVITY,
            provider_name="Rajasthan Heritage Tours",
            title="Amber Fort & Pink City Guided Tour (Next Day 9:00 AM)",
            status=BookingStatus.CONFIRMED,
            start_time=datetime(2026, 10, 21, 9, 0, 0),
            end_time=datetime(2026, 10, 21, 13, 0, 0),
            origin="Jaipur",
            destination="Jaipur",
            price=2250.0,
            currency="INR",
        )
        db.add_all([flight_booking, train_booking, hotel_booking, tour_booking])
        db.commit()
        db.refresh(journey)

        # Build initial pre-disruption Journey Graph
        pre_graph_engine = JourneyGraphEngine(journey_id=journey.id)
        pre_graph_data = pre_graph_engine.build_from_bookings(journey.bookings)

        # =====================================================================
        # TRIGGER: 4-Hour Flight Delay (240 minutes) on Flight AI-202
        # =====================================================================
        impact_result = DisruptionSimulatorEngine.simulate_disruption(
            db=db,
            request=DisruptionSimulationRequest(
                booking_id=flight_booking.id,
                type="flight_delay",
                delay_minutes=240,
                title="Air India AI-202 Delayed 4 Hours (+240m)",
                description="Flight AI-202 delayed 240 minutes; revised Delhi arrival 16:00 IST.",
            ),
        )

        # Recalculated graph immediately after disruption (shows IMPOSSIBLE connection for 13:30 train)
        db.refresh(journey)
        disrupted_graph_engine = JourneyGraphEngine(journey_id=journey.id)
        disrupted_graph_data = disrupted_graph_engine.build_from_bookings(journey.bookings)

        # Step 7 & 8: Search alternative trains & run Google OR-Tools CP-SAT optimization
        optimizer = ORToolsRecoveryOptimizer()
        opt_response = optimizer.optimize(
            OptimizationRequest(
                origin="Delhi",
                destination="Jaipur",
                auto_fetch_from_suppliers=True,
                constraints=OptimizationConstraints(
                    current_arrival="2026-10-20T16:00:00",
                    hotel_latest_checkin="2026-10-20T22:00:00",
                    min_connection_minutes=30,
                    required_seats=1,
                ),
                traveler_preferences=TravelerPreferences(
                    max_budget=4500.0,
                    allowed_modes=["train"],
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

        selected_train = opt_response.selected_option

        # Step 9: Run LangGraph 8-Node Autonomous Recovery Workflow
        langgraph_state = recovery_workflow_runner.run_workflow(
            {
                "journey_id": str(journey.id),
                "disruption": {
                    "type": "flight_delay",
                    "delay_minutes": 240,
                    "origin": "Delhi",
                    "destination": "Jaipur",
                    "revised_arrival": "4:00 PM",
                    "disrupted_booking_ref": "AI-202",
                    "missed_booking_ref": "12015-SHT",
                    "hotel_booking_ref": "HTL-JAI-101",
                },
            }
        )

        # Step 10: Generate all 6 fact-grounded notifications (Traveler, Hotel, Supplier, Refund, Cancellation, Emergency Contact)
        notifications_generated = notification_agent_service.generate_all_notifications(
            facts=StructuredRecoveryFacts(
                journey_id=journey.id,
                disrupted_booking_ref="AI-202",
                delay_minutes=240,
                original_arrival_time="12:00",
                revised_arrival_time="16:00",
                missed_booking_ref="12015-SHT",
                missed_transport_id="TRN123",
                missed_departure_time="13:30",
                missed_arrival_time="17:30",
                missed_ticket_price_inr=800.0,
                refund_amount_inr=600.0,
                rebooked_booking_ref="PNR-TRN124-8821",
                rebooked_transport_id=selected_train["transport_id"],
                rebooked_service_name=selected_train.get("name", "Ashram Express 12916"),
                rebooked_departure_time="17:30",
                rebooked_arrival_time="21:00",
                rebooked_price_inr=float(selected_train["price"]),
                hotel_booking_ref="HTL-JAI-101",
                hotel_original_checkin="18:00",
                hotel_revised_checkin="21:30",
                hotel_latest_cutoff="22:00",
            )
        )

        # Step 11, 12, 13, 14: Ensure recovery actions are executed & update database bookings to reflect final recovered journey
        action_exec_summary = recovery_action_executor.execute_recovery_plan(
            plan_input={
                "plan_id": f"PLAN-E2E-JOURNEY-{journey.id}",
                "original_booking_id": "12015-SHT",
                "original_transport_id": "TRN123",
                "original_price": 800.0,
                "new_transport_id": selected_train["transport_id"],
                "hotel_booking_id": "HTL-JAI-101",
                "hotel_id": "HTL101",
                "new_check_in": "2026-10-20T22:30:00",
                "passenger_name": "Aarav Sharma",
                "traveler_email": "aarav.sharma@example.com",
                "contact_email": "frontdesk@heritagepalacejaipur.com",
            }
        )

        # Step 15 & 16: Update Train & Hotel bookings in DB while leaving Next-Day Tour unchanged, then recompute Final Journey Graph
        train_booking.reference_number = selected_train["transport_id"]
        train_booking.title = f"Rebooked: {selected_train.get('name', 'Indian Railways Special')} ({selected_train['transport_id']})"
        train_booking.start_time = datetime.fromisoformat(selected_train["departure"])
        train_booking.end_time = datetime.fromisoformat(selected_train["arrival"])
        train_booking.price = float(selected_train["price"])
        train_booking.status = BookingStatus.CONFIRMED

        hotel_booking.start_time = train_booking.end_time + timedelta(minutes=30)
        hotel_booking.title = "Rambagh Heritage Palace Jaipur (Updated Late Check-in)"
        hotel_booking.status = BookingStatus.CONFIRMED

        # Tour booking remains completely untouched (Next day 9:00 AM, CONFIRMED)
        db.commit()
        db.refresh(journey)

        final_graph_engine = JourneyGraphEngine(journey_id=journey.id)
        final_graph_engine.sync_to_database(db, journey)
        final_graph_data = final_graph_engine.build_from_bookings(journey.bookings)

        # Build the 17-step verification checklist
        affected_map = {b.reference_number: b.impact_nature for b in impact_result.affected_bookings}
        unaffected_refs = [b.reference_number for b in impact_result.unaffected_bookings]

        steps_checklist = [
            {"step": 1, "name": "Disruption detected", "passed": impact_result.severity in ("CRITICAL", "HIGH")},
            {"step": 2, "name": "Kafka event generated", "passed": len(kafka_broker.all_events_chronological) > 0},
            {"step": 3, "name": "Journey recalculated", "passed": disrupted_graph_data.risk_summary.impossible_connections >= 1},
            {"step": 4, "name": "Train identified as missed", "passed": affected_map.get("12015-SHT") == "MISSED_CONNECTION"},
            {"step": 5, "name": "Hotel identified as potentially affected", "passed": "HTL-JAI-101" in affected_map},
            {"step": 6, "name": "Tour identified as unaffected", "passed": "TOUR-JAI-01" in unaffected_refs},
            {"step": 7, "name": "Alternative trains searched", "passed": len(opt_response.alternatives) >= 3},
            {"step": 8, "name": "OR-Tools selects best feasible alternative", "passed": opt_response.constraints_satisfied and selected_train is not None},
            {"step": 9, "name": "Recovery plan generated", "passed": langgraph_state["selected_plan"].get("selected_option") is not None},
            {"step": 10, "name": "User informed", "passed": len(notifications_generated) == 6},
            {"step": 11, "name": "Mock train booking cancelled", "passed": any(a["action_type"] == "cancel_booking" and a["status"] in ("SUCCESS", "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE") for a in action_exec_summary["audit_records"])},
            {"step": 12, "name": "Alternative train booked", "passed": any(a["action_type"] == "rebook_transportation" and a["status"] in ("SUCCESS", "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE") for a in action_exec_summary["audit_records"])},
            {"step": 13, "name": "Refund request created if eligible", "passed": any(a["action_type"] == "request_refund" and a["status"] in ("SUCCESS", "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE") for a in action_exec_summary["audit_records"])},
            {"step": 14, "name": "Hotel arrival updated", "passed": any(a["action_type"] == "modify_hotel_checkin" and a["status"] in ("SUCCESS", "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE") for a in action_exec_summary["audit_records"])},
            {"step": 15, "name": "Tour remains unchanged", "passed": tour_booking.start_time == datetime(2026, 10, 21, 9, 0, 0) and tour_booking.status == BookingStatus.CONFIRMED},
            {"step": 16, "name": "Final journey graph updated", "passed": final_graph_data.risk_summary.impossible_connections == 0},
            {"step": 17, "name": "Complete audit trail displayed", "passed": len(IdempotencyAndAuditStore.get_history()) >= 6},
        ]

        return {
            "scenario_name": "Stage 12 End-to-End Golden Triangle Disruption Recovery",
            "all_17_steps_passed": all(s["passed"] for s in steps_checklist),
            "steps_checklist": steps_checklist,
            "journey_id": journey.id,
            "impact_analysis": impact_result.model_dump(),
            "pre_disruption_graph_summary": pre_graph_data.risk_summary.model_dump(),
            "disrupted_graph_summary": disrupted_graph_data.risk_summary.model_dump(),
            "final_recovered_graph_summary": final_graph_data.risk_summary.model_dump(),
            "ortools_optimization": opt_response.model_dump(),
            "langgraph_decision_explanation": langgraph_state["selected_plan"].get("decision_explanation"),
            "execution_summary": action_exec_summary,
            "kafka_events_count": len(kafka_broker.all_events_chronological),
            "notifications_count": len(notifications_generated),
            "real_vs_simulated": REAL_VS_SIMULATED_MANIFEST,
        }
