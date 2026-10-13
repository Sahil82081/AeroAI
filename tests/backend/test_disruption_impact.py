import pytest
from datetime import datetime, timedelta
from app.models.models import Booking, BookingType, BookingStatus
from app.modules.disruptions.impact_agent import ImpactAnalysisAgent

def test_impact_analysis_agent_delay_scenario():
    """
    Test prompt example:
    Flight: Mumbai -> Delhi arrival = 12:00
    Train: Delhi -> Jaipur departure = 13:30
    Flight delayed 4 hours (240m) -> Revised arrival = 16:00
    Result:
    - Flight = directly affected (DELAYED)
    - Train = missed connection (MISSED)
    - Hotel & subsequent = affected / threatened
    """
    base_time = datetime(2026, 10, 20, 10, 0, 0)
    
    flight = Booking(
        id=1,
        journey_id=1,
        reference_number="AI-101",
        title="Flight Mumbai -> Delhi",
        booking_type=BookingType.FLIGHT,
        provider_name="Air India",
        status=BookingStatus.CONFIRMED,
        origin="Mumbai (BOM)",
        destination="Delhi (DEL)",
        start_time=base_time,
        end_time=base_time + timedelta(hours=2) # 12:00
    )

    train = Booking(
        id=2,
        journey_id=1,
        reference_number="TR-202",
        title="Train Delhi -> Jaipur",
        booking_type=BookingType.TRAIN,
        provider_name="Indian Railways",
        status=BookingStatus.CONFIRMED,
        origin="Delhi (NDLS)",
        destination="Jaipur",
        start_time=base_time + timedelta(hours=3, minutes=30), # 13:30
        end_time=base_time + timedelta(hours=7, minutes=30)
    )

    hotel = Booking(
        id=3,
        journey_id=1,
        reference_number="HT-303",
        title="Hotel Jaipur Check-in",
        booking_type=BookingType.HOTEL,
        provider_name="ITC Rajputana",
        status=BookingStatus.CONFIRMED,
        origin="Jaipur",
        destination="Jaipur",
        start_time=base_time + timedelta(hours=8), # 18:00
        end_time=base_time + timedelta(days=2)
    )

    # Next-day tour (unaffected in original timeline if not broken)
    tour = Booking(
        id=4,
        journey_id=1,
        reference_number="ACT-404",
        title="Amber Fort Tour",
        booking_type=BookingType.ACTIVITY,
        provider_name="Jaipur Heritage Walks",
        status=BookingStatus.CONFIRMED,
        origin="Jaipur",
        destination="Jaipur",
        start_time=base_time + timedelta(days=1, hours=10),
        end_time=base_time + timedelta(days=1, hours=13)
    )

    # Run analysis for 240 minute delay
    result = ImpactAnalysisAgent.analyze_impact(
        journey_id=1,
        disrupted_booking=flight,
        disruption_type_str="FLIGHT_DELAY",
        delay_minutes=240,
        all_journey_bookings=[flight, train, hotel, tour]
    )

    assert result.severity == "CRITICAL"
    assert len(result.missed_connections) == 1
    missed = result.missed_connections[0]
    assert missed.from_booking_id == 1
    assert missed.to_booking_id == 2
    assert missed.deficit_minutes == 150  # 16:00 arrival vs 13:30 train departure = 150m late!

    # Check affected bookings list
    affected_ids = [a.booking_id for a in result.affected_bookings]
    assert 1 in affected_ids  # Flight (directly delayed)
    assert 2 in affected_ids  # Train (missed)

    # Verify structured explanation
    assert "Delhi" in result.reasoning
    assert "miss" in result.reasoning.lower()

def test_impact_analysis_agent_cancellation_scenario():
    base_time = datetime(2026, 10, 20, 10, 0, 0)
    
    flight = Booking(
        id=10,
        journey_id=2,
        reference_number="BA-11",
        title="Flight LHR -> JFK",
        booking_type=BookingType.FLIGHT,
        provider_name="British Airways",
        status=BookingStatus.CONFIRMED,
        origin="LHR",
        destination="JFK",
        start_time=base_time,
        end_time=base_time + timedelta(hours=8)
    )

    hotel = Booking(
        id=11,
        journey_id=2,
        reference_number="NY-22",
        title="Manhattan Hotel Stay",
        booking_type=BookingType.HOTEL,
        provider_name="The Plaza",
        status=BookingStatus.CONFIRMED,
        origin="New York",
        destination="New York",
        start_time=base_time + timedelta(hours=10),
        end_time=base_time + timedelta(days=3)
    )

    result = ImpactAnalysisAgent.analyze_impact(
        journey_id=2,
        disrupted_booking=flight,
        disruption_type_str="FLIGHT_CANCELLATION",
        delay_minutes=0,
        all_journey_bookings=[flight, hotel]
    )

    assert result.severity == "CRITICAL"
    assert len(result.affected_bookings) == 2
    assert result.affected_bookings[0].status == "CANCELLED"
    assert result.affected_bookings[1].impact_nature == "SCHEDULE_THREATENED"
