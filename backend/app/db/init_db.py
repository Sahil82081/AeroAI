from datetime import datetime, timedelta
from app.db.session import SessionLocal, Base, engine
from app.models.models import (
    User, Journey, Booking, JourneyNode, JourneyEdge, Disruption, RecoveryPlan, Notification,
    BookingType, BookingStatus, DisruptionType, DisruptionSeverity, DisruptionStatus,
    RecoveryPlanStatus, NotificationChannel, NotificationStatus
)
from app.core.security import get_password_hash
from app.core.logger import logger

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema migrated/verified.")
    
    db = SessionLocal()
    try:
        # Check if test traveler user exists
        demo_user = db.query(User).filter(User.email == "traveler@example.com").first()
        if not demo_user:
            logger.info("Creating demo user and sample journey data...")
            demo_user = User(
                email="traveler@example.com",
                hashed_password=get_password_hash("password123"),
                full_name="Sarah Connor",
                is_active=True,
                is_superuser=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            
            # Create sample Journey
            now = datetime.utcnow()
            journey = Journey(
                user_id=demo_user.id,
                title="SF to Tokyo Tech Summit",
                description="Annual AI conference with connection in Tokyo and bullet train to Kyoto",
                start_date=now + timedelta(days=2),
                end_date=now + timedelta(days=9),
                status="ACTIVE"
            )
            db.add(journey)
            db.commit()
            db.refresh(journey)
            
            # Nodes
            node_sfo = JourneyNode(journey_id=journey.id, node_key="SFO", name="San Francisco International Airport", location_type="AIRPORT", latitude=37.6213, longitude=-122.3790)
            node_hnd = JourneyNode(journey_id=journey.id, node_key="HND", name="Tokyo Haneda Airport", location_type="AIRPORT", latitude=35.5494, longitude=139.7798)
            node_hotel = JourneyNode(journey_id=journey.id, node_key="HOTEL_TYO", name="Park Hyatt Tokyo", location_type="HOTEL", latitude=35.6857, longitude=139.6912)
            node_kyoto = JourneyNode(journey_id=journey.id, node_key="KYOTO_STN", name="Kyoto Station", location_type="STATION", latitude=34.9858, longitude=135.7588)
            db.add_all([node_sfo, node_hnd, node_hotel, node_kyoto])
            db.commit()
            db.refresh(node_sfo)
            db.refresh(node_hnd)
            db.refresh(node_hotel)
            db.refresh(node_kyoto)
            
            # Bookings
            flight_b = Booking(
                journey_id=journey.id,
                reference_number="UA-875",
                booking_type=BookingType.FLIGHT,
                provider_name="United Airlines",
                title="Flight SFO -> HND",
                start_time=now + timedelta(days=2, hours=10),
                end_time=now + timedelta(days=3, hours=14),
                origin="SFO",
                destination="HND",
                price=1150.00,
                currency="USD",
                status=BookingStatus.CONFIRMED,
                raw_metadata={"flight_number": "UA875", "seat": "14A"}
            )
            hotel_b = Booking(
                journey_id=journey.id,
                reference_number="HYATT-9921",
                booking_type=BookingType.HOTEL,
                provider_name="Park Hyatt Tokyo",
                title="Tokyo Shinjuku 4-Night Stay",
                start_time=now + timedelta(days=3, hours=16),
                end_time=now + timedelta(days=7, hours=11),
                origin="Tokyo",
                destination="Tokyo",
                price=1400.00,
                currency="USD",
                status=BookingStatus.CONFIRMED,
                raw_metadata={"check_in_time": "15:00", "room_type": "Deluxe King"}
            )
            train_b = Booking(
                journey_id=journey.id,
                reference_number="SHINKANSEN-412",
                booking_type=BookingType.TRAIN,
                provider_name="JR Central",
                title="Shinkansen Nozomi Tokyo -> Kyoto",
                start_time=now + timedelta(days=7, hours=13),
                end_time=now + timedelta(days=7, hours=15, minutes=15),
                origin="Tokyo Station",
                destination="Kyoto Station",
                price=130.00,
                currency="USD",
                status=BookingStatus.CONFIRMED,
                raw_metadata={"train_name": "Nozomi 412", "car": "5", "seat": "12E"}
            )
            db.add_all([flight_b, hotel_b, train_b])
            db.commit()
            db.refresh(flight_b)
            db.refresh(hotel_b)
            db.refresh(train_b)

            # Edges
            edge_1 = JourneyEdge(
                journey_id=journey.id,
                source_node_id=node_sfo.id,
                target_node_id=node_hnd.id,
                booking_id=flight_b.id,
                transport_mode="FLIGHT",
                scheduled_departure=flight_b.start_time,
                scheduled_arrival=flight_b.end_time,
                duration_minutes=660,
                buffer_minutes=120
            )
            edge_2 = JourneyEdge(
                journey_id=journey.id,
                source_node_id=node_hnd.id,
                target_node_id=node_hotel.id,
                booking_id=None,
                transport_mode="TRANSFER",
                scheduled_departure=flight_b.end_time,
                scheduled_arrival=hotel_b.start_time,
                duration_minutes=60,
                buffer_minutes=60
            )
            edge_3 = JourneyEdge(
                journey_id=journey.id,
                source_node_id=node_hotel.id,
                target_node_id=node_kyoto.id,
                booking_id=train_b.id,
                transport_mode="TRAIN",
                scheduled_departure=train_b.start_time,
                scheduled_arrival=train_b.end_time,
                duration_minutes=135,
                buffer_minutes=90
            )
            db.add_all([edge_1, edge_2, edge_3])
            db.commit()

            # Add a sample disruption & proposed recovery plan to showcase the dashboard
            disruption = Disruption(
                journey_id=journey.id,
                booking_id=flight_b.id,
                disruption_type=DisruptionType.FLIGHT_DELAY,
                severity=DisruptionSeverity.HIGH,
                status=DisruptionStatus.PLAN_GENERATED,
                title="UA-875 Weather Ground Delay (4h 30m)",
                description="Severe storm front over Northern Pacific causing departure hold at SFO. Downstream transfer and hotel check-in threatened.",
                delay_minutes=270,
                affected_nodes=["SFO", "HND", "HOTEL_TYO"],
                simulated=True
            )
            db.add(disruption)
            db.commit()
            db.refresh(disruption)

            recovery_plan = RecoveryPlan(
                journey_id=journey.id,
                disruption_id=disruption.id,
                status=RecoveryPlanStatus.PROPOSED,
                summary="Rebook connecting transfer, notify Park Hyatt Tokyo of late check-in at 21:00, and register EU/US flight delay compensation inquiry.",
                reasoning_explanation="Delay exceeds connection buffer by 150 minutes. Modifying hotel arrival prevents no-show cancellation fee. Alternative Haneda night express limousine bus secured.",
                estimated_additional_cost=25.00,
                refund_opportunities={"potential_airline_credit": 200.0, "meal_voucher_eligible": True},
                actions=[
                    {"step": 1, "type": "HOTEL_NOTIFY", "action": "Automated email sent to Park Hyatt Tokyo confirming check-in delayed to 21:30", "status": "COMPLETED"},
                    {"step": 2, "type": "GROUND_TRANSFER", "action": "Pre-reserved Haneda Airport Limousine Bus #18 departs 20:15", "status": "READY"},
                    {"step": 3, "type": "AIRLINE_CLAIM", "action": "Prepared United Airlines compensation claim draft", "status": "PENDING_APPROVAL"}
                ],
                alternatives_considered=[
                    {"option": "Reroute via ANA SFO-NRT", "cost_delta": 450.0, "time_saved_minutes": 60, "verdict": "Rejected due to excessive rebooking fee"},
                    {"option": "Accept delay & shift arrival buffer", "cost_delta": 25.0, "time_saved_minutes": 0, "verdict": "Selected: Optimal cost-benefit trade-off"}
                ]
            )
            db.add(recovery_plan)
            
            notification = Notification(
                user_id=demo_user.id,
                journey_id=journey.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT,
                recipient=demo_user.email,
                subject="Disruption Alert & Proposed Recovery Plan for Journey: SF to Tokyo",
                content="Flight UA-875 is delayed by 4h 30m. An automated recovery plan has been generated to protect your hotel booking and ground transfers.",
                simulated=True
            )
            db.add(notification)

            # Seed an initial ingested email
            from app.models.models import IngestedEmail, EmailParsingStatus
            initial_email = IngestedEmail(
                user_id=demo_user.id,
                journey_id=journey.id,
                booking_id=flight_b.id,
                sender="reservations@united.com",
                recipient=demo_user.email,
                subject="Your United Airlines Flight Receipt - UA 875",
                raw_body="Flight Confirmation: UA875 SFO to HND. Seat: 14A. Status: Confirmed.",
                parsing_status=EmailParsingStatus.PARSED,
                booking_type="flight",
                confidence_score=0.98,
                parsed_data={
                    "type": "flight",
                    "provider": "United Airlines",
                    "booking_reference": "UA-875",
                    "origin": "SFO",
                    "destination": "HND",
                    "departure": flight_b.start_time.isoformat(),
                    "arrival": flight_b.end_time.isoformat()
                },
                parser_used="heuristic",
                received_at=now,
                processed_at=now
            )
            db.add(initial_email)
            db.commit()
            logger.info("Demo user, journey, bookings, disruption, and plan successfully seeded.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
