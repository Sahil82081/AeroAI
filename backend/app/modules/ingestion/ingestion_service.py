from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.models import (
    User, Journey, Booking, IngestedEmail, BookingType, BookingStatus, EmailParsingStatus
)
from app.schemas.ingestion_schemas import (
    EmailIngestRequest, EmailIngestResponse, NormalizedBooking, ParserExtractionResult
)
from app.modules.ingestion.heuristic_parser import HeuristicEmailParser
from app.modules.ingestion.gemini_parser import GeminiEmailParser

class EmailIngestionService:
    """
    Coordinates email reception, duplicate detection, parsing, validation,
    and automatic booking creation / journey association.
    """

    @classmethod
    async def ingest_email(
        cls,
        db: Session,
        user: User,
        request: EmailIngestRequest
    ) -> IngestedEmail:
        logger.info(f"Ingesting email from {request.sender} with subject: {request.subject}")

        # 1. Parse content
        if request.force_parser == "heuristic":
            result = HeuristicEmailParser.parse(request.subject, request.body)
        elif request.force_parser == "gemini":
            result = await GeminiEmailParser.parse(request.subject, request.body)
        else: # auto
            # If Gemini is configured, use it, else heuristic
            result = await GeminiEmailParser.parse(request.subject, request.body)

        # 2. Check duplicate booking in the database
        booking_ref = result.normalized_booking.booking_reference if result.normalized_booking else None
        duplicate_booking = None
        if booking_ref:
            duplicate_booking = db.query(Booking).filter(
                Booking.reference_number == booking_ref
            ).first()

        # 3. Create IngestedEmail record
        ingested = IngestedEmail(
            user_id=user.id,
            journey_id=request.journey_id,
            sender=request.sender,
            recipient=request.recipient,
            subject=request.subject,
            raw_body=request.body,
            parsing_status=EmailParsingStatus.DUPLICATE if duplicate_booking else result.status,
            booking_type=result.booking_type,
            confidence_score=result.confidence,
            parsed_data=result.normalized_booking.model_dump() if result.normalized_booking else None,
            missing_fields=result.missing_fields,
            clarification_prompt=result.clarification_prompt,
            error_message="Duplicate booking reference detected in system." if duplicate_booking else result.error_message,
            parser_used=result.parser_used,
            received_at=datetime.utcnow(),
            processed_at=datetime.utcnow()
        )
        db.add(ingested)
        db.commit()
        db.refresh(ingested)

        # 4. If parsed successfully and not duplicate, persist as structured Booking
        if result.success and not duplicate_booking and result.normalized_booking:
            norm = result.normalized_booking
            
            # Map booking type
            type_map = {
                "flight": BookingType.FLIGHT,
                "train": BookingType.TRAIN,
                "bus": BookingType.BUS,
                "hotel": BookingType.HOTEL,
                "activity": BookingType.ACTIVITY
            }
            mapped_type = type_map.get(norm.type, BookingType.ACTIVITY)

            # Determine journey
            journey = None
            if request.journey_id:
                journey = db.query(Journey).filter(
                    Journey.id == request.journey_id, Journey.user_id == user.id
                ).first()

            if not journey:
                # Find active journey or create default
                journey = db.query(Journey).filter(Journey.user_id == user.id).first()
                if not journey:
                    journey = Journey(
                        user_id=user.id,
                        title="My Travel Journey",
                        description="Auto-created from email ingestion",
                        start_date=datetime.utcnow(),
                        end_date=datetime.utcnow(),
                        status="ACTIVE"
                    )
                    db.add(journey)
                    db.commit()
                    db.refresh(journey)

            # Parse start / end times with safe fallback
            start_dt = datetime.utcnow()
            if norm.departure:
                try:
                    start_dt = datetime.fromisoformat(norm.departure)
                except Exception:
                    pass

            end_dt = start_dt
            if norm.arrival:
                try:
                    end_dt = datetime.fromisoformat(norm.arrival)
                except Exception:
                    pass

            # Only create booking if reference number is available
            if norm.booking_reference:
                booking = Booking(
                    journey_id=journey.id,
                    reference_number=norm.booking_reference,
                    booking_type=mapped_type,
                    provider_name=norm.provider,
                    title=norm.title or f"{norm.provider} Booking",
                    description=f"Ingested from email: {request.subject}",
                    status=BookingStatus.CONFIRMED if result.status == EmailParsingStatus.PARSED else BookingStatus.PENDING,
                    start_time=start_dt,
                    end_time=end_dt,
                    origin=norm.origin,
                    destination=norm.destination,
                    price=norm.price or 0.0,
                    currency=norm.currency or "USD",
                    raw_metadata=norm.raw_metadata or {}
                )
                db.add(booking)
                db.commit()
                db.refresh(booking)

                # Link email to booking and journey
                ingested.booking_id = booking.id
                ingested.journey_id = journey.id
                db.commit()
                db.refresh(ingested)

                # Recompute journey graph
                try:
                    from app.modules.journeys.graph_builder import JourneyGraphEngine
                    engine = JourneyGraphEngine(journey_id=journey.id)
                    engine.sync_to_database(db, journey)
                except Exception as g_err:
                    logger.warning(f"Graph sync warning after email ingestion: {g_err}")

                # Publish booking.created event to Kafka
                try:
                    from app.modules.events.kafka_engine import kafka_broker
                    from app.schemas.event_schemas import KafkaTopic
                    kafka_broker.publish_event(
                        topic=KafkaTopic.BOOKING_CREATED.value,
                        event_type="BOOKING_CREATED_FROM_EMAIL",
                        producer="email-ingestion-service",
                        ui_message=f"Booking created: {booking.provider_name} ({booking.reference_number})",
                        payload={
                            "journey_id": journey.id,
                            "booking_id": booking.id,
                            "booking_ref": booking.reference_number,
                            "booking_type": booking.booking_type.value,
                            "provider_name": booking.provider_name,
                            "origin": booking.origin,
                            "destination": booking.destination,
                        },
                    )
                except Exception as k_err:
                    logger.warning(f"Kafka booking.created publish warning: {k_err}")

        return ingested
