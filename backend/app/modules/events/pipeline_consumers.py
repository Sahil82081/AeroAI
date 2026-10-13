"""
Stage 9: Kafka Event-Driven Multi-Agent Consumers & Disruption Pipeline Orchestrator.

Event Flow:
Disruption API
      ↓
    Kafka (`booking.updated`, `disruption.detected`) -> "Flight delay detected"
      ↓
Impact Agent (`impact-agent-group`)
      ↓
    Kafka (`journey.affected`, `recovery.requested`) -> "Train connection affected", "Searching alternatives"
      ↓
Recovery Agent (`recovery-agent-group`)
      ↓
    Kafka (`recovery.planned`, `action.requested`) -> "Optimization completed"
      ↓
Action Agent (`action-agent-group`)
      ↓
    Kafka (`action.completed` / `action.failed`, `notification.requested`) -> "Train rebooked", "Hotel updated"
      ↓
Notification Agent (`notification-agent-group`)
      ↓
    Real-Time WebSocket Completion -> "Traveler notified"
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.schemas.event_schemas import (
    KafkaTopic,
    KafkaEventEnvelope,
    EventDrivenDisruptionRequest,
)
from app.modules.events.kafka_engine import kafka_broker, KafkaConsumerGroup
from app.modules.optimization.ortools_optimizer import ORToolsRecoveryOptimizer
from app.schemas.optimization_schemas import (
    OptimizationRequest,
    OptimizationConstraints,
    TravelerPreferences,
    OptimizationWeights,
)
from app.modules.recovery.action_executor import recovery_action_executor
from app.core.logger import logger


class EventDrivenRecoveryPipeline:
    """
    Registers the 4 specialized Kafka Consumer Groups (Impact Agent, Recovery Agent,
    Action Agent, Notification Agent) plus Booking Lifecycle Consumer Group, and provides
    the entry point for the Disruption API to trigger the event-driven cascade.
    """

    def __init__(self):
        self._registered = False
        self.completed_notifications: List[Dict[str, Any]] = []

    def register_all_consumers(self):
        if self._registered:
            return

        # 1. Impact Agent Consumer Group -> subscribes to `disruption.detected`
        impact_consumer = KafkaConsumerGroup(
            group_id="impact-agent-group",
            agent_name="Impact Agent",
            subscribed_topics=[KafkaTopic.DISRUPTION_DETECTED.value],
            handler=self._handle_disruption_detected,
            default_max_retries=3,
        )

        # 2. Recovery Agent Consumer Group -> subscribes to `recovery.requested`
        recovery_consumer = KafkaConsumerGroup(
            group_id="recovery-agent-group",
            agent_name="Recovery Agent",
            subscribed_topics=[KafkaTopic.RECOVERY_REQUESTED.value],
            handler=self._handle_recovery_requested,
            default_max_retries=3,
        )

        # 3. Action Agent Consumer Group -> subscribes to `action.requested`
        action_consumer = KafkaConsumerGroup(
            group_id="action-agent-group",
            agent_name="Action Agent",
            subscribed_topics=[KafkaTopic.ACTION_REQUESTED.value],
            handler=self._handle_action_requested,
            default_max_retries=3,
        )

        # 4. Notification Agent Consumer Group -> subscribes to `notification.requested`
        notification_consumer = KafkaConsumerGroup(
            group_id="notification-agent-group",
            agent_name="Notification Agent",
            subscribed_topics=[KafkaTopic.NOTIFICATION_REQUESTED.value],
            handler=self._handle_notification_requested,
            default_max_retries=3,
        )

        # 5. Booking Lifecycle Consumer Group -> subscribes to `booking.created`, `booking.updated`
        booking_consumer = KafkaConsumerGroup(
            group_id="booking-lifecycle-group",
            agent_name="Journey Graph Sync Agent",
            subscribed_topics=[KafkaTopic.BOOKING_CREATED.value, KafkaTopic.BOOKING_UPDATED.value],
            handler=self._handle_booking_lifecycle,
            default_max_retries=2,
        )

        kafka_broker.register_consumer_group(impact_consumer)
        kafka_broker.register_consumer_group(recovery_consumer)
        kafka_broker.register_consumer_group(action_consumer)
        kafka_broker.register_consumer_group(notification_consumer)
        kafka_broker.register_consumer_group(booking_consumer)

        self._registered = True

    def _handle_booking_lifecycle(self, envelope: KafkaEventEnvelope):
        logger.info(
            f"[Booking Lifecycle Consumer] Synchronized {envelope.topic} for booking "
            f"{envelope.payload.get('booking_ref', 'UNKNOWN')} (corr={envelope.correlation_id})"
        )

    def _handle_disruption_detected(self, envelope: KafkaEventEnvelope):
        """
        Impact Agent Consumer:
        Consumes `disruption.detected` -> evaluates downstream journey dependencies
        -> publishes `journey.affected` ("Train connection affected")
        -> publishes `recovery.requested` ("Searching alternatives")
        """
        payload = envelope.payload
        delay_minutes = int(payload.get("delay_minutes", 240))
        disruption_type = payload.get("disruption_type", "flight_delay")
        step_delay_ms = int(payload.get("step_delay_ms", 0))
        inject_failure = payload.get("inject_consumer_failure")

        is_cancelled = "cancel" in disruption_type.lower()
        effective_delay = 300 if is_cancelled else delay_minutes
        base_arr_min = 12 * 60
        new_arr_min = base_arr_min + effective_delay
        revised_arrival_iso = f"2026-10-20T{min(23, new_arr_min // 60):02d}:{new_arr_min % 60:02d}:00"

        affected_bookings = [
            {
                "booking_ref": "AI-202",
                "booking_type": "flight",
                "title": "Air India AI-202 (Mumbai -> Delhi)",
                "impact_status": "CANCELLED" if is_cancelled else f"DELAYED_+{delay_minutes}M",
                "revised_arrival": revised_arrival_iso,
            },
            {
                "booking_ref": "12015-SHT",
                "booking_type": "train",
                "title": "Ajmer Shatabdi 12015 (Delhi -> Jaipur)",
                "impact_status": "MISSED_CONNECTION",
                "scheduled_departure": "2026-10-20T13:30:00",
                "connection_gap_minutes": (13 * 60 + 30) - new_arr_min,
            },
            {
                "booking_ref": "HTL-JAI-101",
                "booking_type": "hotel",
                "title": "Rambagh Heritage Palace Jaipur",
                "impact_status": "LATE_CHECKIN_AT_RISK",
                "latest_checkin": "2026-10-20T22:00:00",
            },
        ]

        # 1. Publish `journey.affected` -> "Train connection affected"
        journey_affected_env = kafka_broker.publish_event(
            topic=KafkaTopic.JOURNEY_AFFECTED.value,
            event_type="JOURNEY_DOWNSTREAM_AFFECTED",
            producer="impact-agent",
            correlation_id=envelope.correlation_id,
            causation_id=envelope.event_id,
            ui_message="Train connection affected",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "journey_id": payload.get("journey_id", 1),
                "booking_ref": payload.get("booking_ref", "AI-202"),
                "revised_arrival": revised_arrival_iso,
                "affected_bookings": affected_bookings,
                "missed_connections": ["AI-202 -> 12015-SHT (Delhi -> Jaipur)"],
                "severity": "CRITICAL",
                "reasoning": (
                    f"Flight {payload.get('booking_ref', 'AI-202')} revised arrival ({revised_arrival_iso[-8:-3]}) "
                    f"violates the 13:30 departure of train 12015-SHT at New Delhi."
                ),
                "step_delay_ms": step_delay_ms,
                "inject_consumer_failure": inject_failure,
            },
        )

        # 2. Publish `recovery.requested` -> "Searching alternatives"
        kafka_broker.publish_event(
            topic=KafkaTopic.RECOVERY_REQUESTED.value,
            event_type="AUTONOMOUS_RECOVERY_REQUESTED",
            producer="impact-agent",
            correlation_id=envelope.correlation_id,
            causation_id=journey_affected_env.event_id,
            ui_message="Searching alternatives",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "journey_id": payload.get("journey_id", 1),
                "disrupted_booking_ref": "12015-SHT",
                "origin": "Delhi",
                "destination": "Jaipur",
                "revised_arrival": revised_arrival_iso,
                "hotel_booking_ref": "HTL-JAI-101",
                "hotel_latest_checkin": "2026-10-20T22:00:00",
                "step_delay_ms": step_delay_ms,
                "inject_consumer_failure": inject_failure,
            },
        )

    def _handle_recovery_requested(self, envelope: KafkaEventEnvelope):
        """
        Recovery Agent Consumer:
        Consumes `recovery.requested` -> searches mock supplier adapters & runs Google OR-Tools CP-SAT
        -> publishes `recovery.planned` ("Optimization completed")
        -> publishes `action.requested`
        """
        payload = envelope.payload
        inject_failure = payload.get("inject_consumer_failure")
        step_delay_ms = int(payload.get("step_delay_ms", 0))

        # Support transient failure simulation on attempt 1 (retry_count == 0)
        if inject_failure == "recovery_agent_transient" and envelope.retry_count < 1:
            raise ConnectionResetError(
                "Simulated transient supplier/OR-Tools worker timeout on first attempt (will succeed on retry #1)"
            )

        origin = payload.get("origin", "Delhi")
        destination = payload.get("destination", "Jaipur")
        revised_arrival = payload.get("revised_arrival", "2026-10-20T16:00:00")
        hotel_latest_checkin = payload.get("hotel_latest_checkin", "2026-10-20T22:00:00")

        opt_req = OptimizationRequest(
            origin=origin,
            destination=destination,
            auto_fetch_from_suppliers=True,
            constraints=OptimizationConstraints(
                current_arrival=revised_arrival,
                hotel_latest_checkin=hotel_latest_checkin,
                min_connection_minutes=30,
                required_seats=1,
            ),
            traveler_preferences=TravelerPreferences(
                max_budget=4500.0,
                weights=OptimizationWeights(
                    price=0.30,
                    travel_time=0.25,
                    waiting_time=0.20,
                    number_of_changes=0.05,
                    arrival_time=0.10,
                    reliability=0.10,
                ),
            ),
        )

        opt_result = ORToolsRecoveryOptimizer().optimize(opt_req)
        selected_opt = opt_result.selected_option or {
            "transport_id": "TRN124",
            "supplier_type": "train",
            "provider": "Indian Railways",
            "name": "Ashram Express 12916",
            "origin": "Delhi",
            "destination": "Jaipur",
            "departure": "2026-10-20T17:30:00",
            "arrival": "2026-10-20T21:00:00",
            "price": 750.0,
        }

        recovery_plan = {
            "plan_id": f"PLAN-KAFKA-{envelope.correlation_id[-6:].upper()}",
            "selected_option": selected_opt,
            "objective_score": opt_result.objective_score,
            "constraints_satisfied": opt_result.constraints_satisfied,
            "explanation": opt_result.explanation,
            "hotel_booking_id": payload.get("hotel_booking_ref", "HTL-JAI-101"),
            "original_booking_id": payload.get("disrupted_booking_ref", "12015-SHT"),
            "original_transport_id": "TRN123",
            "new_transport_id": selected_opt.get("transport_id", "TRN124"),
            "new_check_in": selected_opt.get("arrival", "2026-10-20T21:30:00"),
        }

        # 1. Publish `recovery.planned` -> "Optimization completed"
        planned_env = kafka_broker.publish_event(
            topic=KafkaTopic.RECOVERY_PLANNED.value,
            event_type="RECOVERY_PLAN_OPTIMIZED",
            producer="recovery-agent",
            correlation_id=envelope.correlation_id,
            causation_id=envelope.event_id,
            ui_message="Optimization completed",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "journey_id": payload.get("journey_id", 1),
                "recovery_plan": recovery_plan,
                "candidates_evaluated": len(opt_result.alternatives),
                "step_delay_ms": step_delay_ms,
                "inject_consumer_failure": inject_failure,
            },
        )

        # 2. Publish `action.requested` -> dispatches to Action Agent
        kafka_broker.publish_event(
            topic=KafkaTopic.ACTION_REQUESTED.value,
            event_type="RECOVERY_ACTIONS_REQUESTED",
            producer="recovery-agent",
            correlation_id=envelope.correlation_id,
            causation_id=planned_env.event_id,
            ui_message=f"Executing recovery plan {recovery_plan['plan_id']} ({selected_opt.get('transport_id', 'TRN124')})",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "journey_id": payload.get("journey_id", 1),
                "recovery_plan": recovery_plan,
                "step_delay_ms": step_delay_ms,
                "inject_consumer_failure": inject_failure,
            },
        )

    def _handle_action_requested(self, envelope: KafkaEventEnvelope):
        """
        Action Agent Consumer:
        Consumes `action.requested` -> executes supplier actions via `RecoveryActionExecutor`
        -> publishes `action.completed` ("Train rebooked" and "Hotel updated")
        -> publishes `notification.requested`
        """
        payload = envelope.payload
        inject_failure = payload.get("inject_consumer_failure")
        step_delay_ms = int(payload.get("step_delay_ms", 0))

        # Support poison-pill failure simulation that exhausts retries and routes to `recovery.dlq`
        if inject_failure == "action_agent_poison_pill":
            raise RuntimeError(
                "Simulated Poison-Pill Supplier Gateway Contract Error: Action execution rejected on all attempts"
            )

        plan_data = payload.get("recovery_plan", {})
        selected_opt = plan_data.get("selected_option", {})
        plan_id = plan_data.get("plan_id", f"PLAN-{envelope.correlation_id[-6:].upper()}")

        exec_result = recovery_action_executor.execute_recovery_plan(
            plan_input={
                "plan_id": plan_id,
                "original_booking_id": plan_data.get("original_booking_id", "12015-SHT"),
                "original_transport_id": plan_data.get("original_transport_id", "TRN123"),
                "new_transport_id": plan_data.get("new_transport_id", selected_opt.get("transport_id", "TRN124")),
                "hotel_booking_id": plan_data.get("hotel_booking_id", "HTL-JAI-101"),
                "hotel_id": "HTL101",
                "new_check_in": plan_data.get("new_check_in", selected_opt.get("arrival", "2026-10-20T21:30:00")),
                "passenger_name": "Aarav Sharma",
                "traveler_email": "aarav.sharma@example.com",
                "contact_email": "frontdesk@heritagepalacejaipur.com",
            },
            max_retries=2,
            timeout_ms=3000,
        )

        # 1. Publish `action.completed` for transport rebooking -> "Train rebooked"
        rebook_env = kafka_broker.publish_event(
            topic=KafkaTopic.ACTION_COMPLETED.value,
            event_type="TRANSPORT_REBOOKED",
            producer="action-agent",
            correlation_id=envelope.correlation_id,
            causation_id=envelope.event_id,
            idempotency_key=f"ACT-REBOOK-{envelope.correlation_id}",
            ui_message="Train rebooked",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "plan_id": plan_id,
                "action_type": "rebook_transportation",
                "transport_id": selected_opt.get("transport_id", "TRN124"),
                "carrier_name": selected_opt.get("provider", "Indian Railways"),
                "departure_time": selected_opt.get("departure"),
                "arrival_time": selected_opt.get("arrival"),
                "execution_status": exec_result.get("execution_status"),
                "step_tag": "rebook_transport",
            },
        )

        # 2. Publish `action.completed` for hotel arrival modification -> "Hotel updated"
        hotel_env = kafka_broker.publish_event(
            topic=KafkaTopic.ACTION_COMPLETED.value,
            event_type="HOTEL_ARRIVAL_UPDATED",
            producer="action-agent",
            correlation_id=envelope.correlation_id,
            causation_id=rebook_env.event_id,
            idempotency_key=f"ACT-HOTEL-{envelope.correlation_id}",
            ui_message="Hotel updated",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "plan_id": plan_id,
                "action_type": "modify_hotel_checkin",
                "hotel_booking_ref": plan_data.get("hotel_booking_id", "HTL-JAI-101"),
                "new_expected_arrival": selected_opt.get("arrival", "2026-10-20T21:30:00"),
                "late_checkin_guaranteed": True,
                "step_tag": "modify_hotel",
            },
        )

        # 3. Publish `notification.requested` -> dispatches to Notification Agent
        kafka_broker.publish_event(
            topic=KafkaTopic.NOTIFICATION_REQUESTED.value,
            event_type="TRAVELER_NOTIFICATION_REQUESTED",
            producer="action-agent",
            correlation_id=envelope.correlation_id,
            causation_id=hotel_env.event_id,
            ui_message="Dispatching traveler & hotel notifications",
            max_retries=envelope.max_retries,
            step_delay_ms=step_delay_ms,
            payload={
                "journey_id": payload.get("journey_id", 1),
                "plan_id": plan_id,
                "selected_option": selected_opt,
                "hotel_booking_ref": plan_data.get("hotel_booking_id", "HTL-JAI-101"),
                "recipient_traveler": "Aarav Sharma <aarav.sharma@example.com>",
                "recipient_hotel": "Heritage Palace Front Desk <frontdesk@heritagepalacejaipur.com>",
                "audit_records_count": len(exec_result.get("audit_records", [])),
            },
        )

    def _handle_notification_requested(self, envelope: KafkaEventEnvelope):
        """
        Notification Agent Consumer:
        Consumes `notification.requested` -> finalizes traveler & hotel notifications
        -> broadcasts final WebSocket milestone "Traveler notified"
        """
        payload = envelope.payload
        selected_opt = payload.get("selected_option", {})
        notification_summary = {
            "notification_id": f"NOTIF-{envelope.correlation_id[-6:].upper()}",
            "correlation_id": envelope.correlation_id,
            "event_id": envelope.event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recipient": payload.get("recipient_traveler", "Aarav Sharma"),
            "status": "DELIVERED",
            "message": (
                f"Recovery complete: Rebooked onto {selected_opt.get('provider', 'Indian Railways')} "
                f"({selected_opt.get('transport_id', 'TRN124')}) departing {str(selected_opt.get('departure', ''))[-8:-3]} "
                f"and arriving {str(selected_opt.get('arrival', ''))[-8:-3]}. "
                f"Heritage Palace Jaipur check-in updated."
            ),
        }
        self.completed_notifications.append(notification_summary)

        # Emit final WebSocket milestone frame: "Traveler notified"
        from app.modules.events.ws_manager import ws_manager
        ws_manager.broadcast_event({
            "event_id": f"evt-notif-ack-{envelope.event_id[-6:]}",
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.event_id,
            "topic": KafkaTopic.NOTIFICATION_REQUESTED.value,
            "event_type": "TRAVELER_NOTIFIED_ACK",
            "producer": "notification-agent",
            "timestamp": notification_summary["timestamp"],
            "partition": envelope.partition,
            "offset": envelope.offset,
            "retry_count": 0,
            "ui_message": "Traveler notified",
            "payload": notification_summary,
        })

    def trigger_disruption_pipeline(self, req: EventDrivenDisruptionRequest) -> Dict[str, Any]:
        """
        Entry point for the Disruption API:
        1. Publishes `booking.updated`
        2. Publishes `disruption.detected` ("Flight delay detected")
        Which triggers the autonomous Kafka consumer cascade across:
        Impact Agent -> Recovery Agent -> Action Agent -> Notification Agent
        """
        self.register_all_consumers()

        corr_id = req.correlation_id or f"corr-{datetime.now(timezone.utc).strftime('%H%M%S')}-{req.booking_ref.lower()}"

        # 1. Publish `booking.updated`
        booking_updated_env = kafka_broker.publish_event(
            topic=KafkaTopic.BOOKING_UPDATED.value,
            event_type="BOOKING_STATUS_UPDATED",
            producer="disruption-api",
            correlation_id=corr_id,
            ui_message=f"Booking {req.booking_ref} updated ({req.disruption_type}, +{req.delay_minutes}m)",
            max_retries=req.max_retries,
            step_delay_ms=req.step_delay_ms,
            payload={
                "journey_id": req.journey_id,
                "booking_ref": req.booking_ref,
                "new_status": "CANCELLED" if "cancel" in req.disruption_type.lower() else "DELAYED",
                "delay_minutes": req.delay_minutes,
                "step_tag": "booking_updated",
            },
        )

        # 2. Publish `disruption.detected` -> "Flight delay detected"
        disruption_label = (
            "Flight cancellation detected"
            if "cancel" in req.disruption_type.lower()
            else "Flight delay detected"
        )
        disruption_env = kafka_broker.publish_event(
            topic=KafkaTopic.DISRUPTION_DETECTED.value,
            event_type="DISRUPTION_DETECTED",
            producer="disruption-api",
            correlation_id=corr_id,
            causation_id=booking_updated_env.event_id,
            event_id=req.event_id,
            idempotency_key=req.idempotency_key,
            ui_message=disruption_label,
            max_retries=req.max_retries,
            step_delay_ms=req.step_delay_ms,
            payload={
                "journey_id": req.journey_id,
                "booking_ref": req.booking_ref,
                "disruption_type": req.disruption_type,
                "delay_minutes": req.delay_minutes,
                "reason": req.reason,
                "step_delay_ms": req.step_delay_ms,
                "inject_consumer_failure": req.inject_consumer_failure,
                "step_tag": "disruption_detected",
            },
        )

        # Gather all events emitted under this correlation_id
        cascade_events = [
            e for e in kafka_broker.all_events_chronological
            if e.get("correlation_id") == corr_id
        ]
        ws_milestones = [
            m.get("ui_message")
            for m in cascade_events
            if m.get("ui_message")
        ]
        # Include the final "Traveler notified" milestone from ws_manager if present
        from app.modules.events.ws_manager import ws_manager
        all_ws_for_corr = [
            m.get("ui_message")
            for m in ws_manager.live_milestones
            if m.get("correlation_id") == corr_id and m.get("ui_message")
        ]

        dlq_for_corr = [
            d.model_dump() for d in kafka_broker.dlq_records
            if d.original_event.correlation_id == corr_id
        ]
        skips_for_corr = [
            s for s in kafka_broker.idempotent_skip_records
            if s.get("correlation_id") == corr_id
        ]

        return {
            "correlation_id": corr_id,
            "root_event_id": disruption_env.event_id,
            "idempotency_key": disruption_env.idempotency_key,
            "total_events_emitted": len(cascade_events),
            "topics_traversed": list(dict.fromkeys(e["topic"] for e in cascade_events)),
            "realtime_milestones": all_ws_for_corr or ws_milestones,
            "events": cascade_events,
            "dlq_events": dlq_for_corr,
            "idempotent_skips": skips_for_corr,
            "consumer_groups": [g.to_status_dict() for g in kafka_broker.consumer_groups.values()],
        }


event_pipeline = EventDrivenRecoveryPipeline()
event_pipeline.register_all_consumers()
