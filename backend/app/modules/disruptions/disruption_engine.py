from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.models import (
    Booking, Journey, Disruption, DisruptionType, DisruptionSeverity, DisruptionStatus, BookingStatus
)
from app.schemas.disruption_schemas import (
    DisruptionSimulationRequest, ImpactAnalysisResult
)
from app.modules.disruptions.impact_agent import ImpactAnalysisAgent
from app.modules.events.event_bus import event_bus
from app.modules.journeys.graph_builder import JourneyGraphEngine
from app.core.logger import logger

class DisruptionSimulatorEngine:
    """
    Coordinates disruption simulation:
    1. Updates the target booking.
    2. Publishes disruption event to event bus.
    3. Recomputes journey graph.
    4. Runs ImpactAnalysisAgent to evaluate downstream dependencies.
    5. Persists the disruption and returns structured impact analysis.
    """

    DISRUPTION_MAP = {
        "flight_delay": DisruptionType.FLIGHT_DELAY,
        "flight_cancellation": DisruptionType.FLIGHT_CANCELLATION,
        "train_delay": DisruptionType.TRAIN_DELAY,
        "train_cancellation": DisruptionType.TRAIN_CANCELLATION,
        "bus_cancellation": DisruptionType.BUS_CANCELLATION,
        "strike": DisruptionType.STRIKE,
        "weather": DisruptionType.WEATHER,
    }

    @classmethod
    def simulate_disruption(
        cls,
        db: Session,
        request: DisruptionSimulationRequest
    ) -> ImpactAnalysisResult:
        # 1. Fetch target booking
        booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
        if not booking:
            raise ValueError(f"Booking with ID {request.booking_id} not found.")

        journey = db.query(Journey).filter(Journey.id == booking.journey_id).first()
        if not journey:
            raise ValueError(f"Journey for booking {booking.id} not found.")

        # Determine mapped enum type
        req_type_lower = request.type.lower().replace("-", "_").replace(" ", "_")
        mapped_type = cls.DISRUPTION_MAP.get(req_type_lower, DisruptionType.FLIGHT_DELAY)

        # 2. Update booking status & arrival times
        is_cancellation = "cancellation" in req_type_lower or mapped_type in [
            DisruptionType.FLIGHT_CANCELLATION, DisruptionType.TRAIN_CANCELLATION, DisruptionType.BUS_CANCELLATION
        ]

        if is_cancellation:
            booking.status = BookingStatus.CANCELLED
        elif request.delay_minutes and request.delay_minutes > 0:
            booking.status = BookingStatus.DELAYED
            booking.end_time = booking.end_time + timedelta(minutes=request.delay_minutes)
        db.commit()
        db.refresh(booking)

        # 3. Publish disruption event to legacy event_bus & Stage 9 Kafka broker
        event_payload = {
            "event_type": "TRAVEL_DISRUPTION_DETECTED",
            "journey_id": journey.id,
            "booking_id": booking.id,
            "booking_ref": booking.reference_number,
            "disruption_type": mapped_type.value,
            "delay_minutes": request.delay_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }
        event_bus.publish("travel.disruptions", event_payload)
        try:
            from app.modules.events.pipeline_consumers import event_pipeline
            from app.schemas.event_schemas import EventDrivenDisruptionRequest
            event_pipeline.trigger_disruption_pipeline(
                EventDrivenDisruptionRequest(
                    journey_id=journey.id,
                    booking_ref=booking.reference_number,
                    disruption_type=mapped_type.value.lower(),
                    delay_minutes=request.delay_minutes or 0,
                    reason=request.description or f"Disruption on {booking.reference_number}",
                )
            )
        except Exception as k_err:
            logger.warning(f"Kafka pipeline trigger warning: {k_err}")
        logger.info(f"Published disruption event for booking {booking.reference_number}: {mapped_type.value}")

        # 4. Run ImpactAnalysisAgent across journey bookings
        impact = ImpactAnalysisAgent.analyze_impact(
            journey_id=journey.id,
            disrupted_booking=booking,
            disruption_type_str=mapped_type.value,
            delay_minutes=request.delay_minutes or 0,
            all_journey_bookings=journey.bookings
        )

        # 5. Persist Disruption record in database
        severity_map = {
            "CRITICAL": DisruptionSeverity.CRITICAL,
            "HIGH": DisruptionSeverity.HIGH,
            "MEDIUM": DisruptionSeverity.MEDIUM,
            "LOW": DisruptionSeverity.LOW,
        }

        disruption_title = request.title or f"{booking.provider_name} {booking.reference_number}: {mapped_type.value.replace('_', ' ')}"
        disruption_desc = request.description or impact.explanation

        disruption_record = Disruption(
            journey_id=journey.id,
            booking_id=booking.id,
            disruption_type=mapped_type,
            severity=severity_map.get(impact.severity, DisruptionSeverity.HIGH),
            status=DisruptionStatus.DETECTED,
            title=disruption_title,
            description=disruption_desc,
            delay_minutes=request.delay_minutes or 0,
            affected_nodes=[a.reference_number for a in impact.affected_bookings],
            simulated=True
        )
        db.add(disruption_record)
        db.commit()
        db.refresh(disruption_record)

        impact.disruption_id = disruption_record.id

        # 6. Recompute and synchronize journey graph in DB
        engine = JourneyGraphEngine(journey_id=journey.id)
        engine.sync_to_database(db, journey)

        return impact
