import pytest
from datetime import datetime, timedelta
from app.models.models import Booking, BookingType, BookingStatus
from app.modules.journeys.graph_builder import JourneyGraphEngine
from app.modules.journeys.location_matcher import LocationMatcher
from app.modules.journeys.risk_evaluator import ConnectionRiskEvaluator

def create_mock_booking(id: int, b_type: BookingType, ref: str, provider: str, origin: str, dest: str, start: datetime, end: datetime):
    return Booking(
        id=id,
        journey_id=1,
        reference_number=ref,
        booking_type=b_type,
        provider_name=provider,
        title=f"{provider} {ref}",
        status=BookingStatus.CONFIRMED,
        origin=origin,
        destination=dest,
        start_time=start,
        end_time=end,
        price=100.0,
        currency="USD"
    )

def test_location_matcher():
    # Test airport normalization
    assert LocationMatcher.normalize_city("Mumbai (BOM) Terminal 2") == "mumbai"
    assert LocationMatcher.normalize_city("Indira Gandhi Intl (DEL)") == "delhi"
    assert LocationMatcher.normalize_city("New Delhi Railway Station") == "delhi"

    # Test airport to railway transfer proximity
    trans_type, min_buf = LocationMatcher.evaluate_transfer_proximity("Delhi Airport (DEL)", "New Delhi Railway Station", "FLIGHT", "TRAIN")
    assert trans_type == "airport_to_station_transfer"
    assert min_buf == 120

    # Test inter-city mismatch
    mismatch_type, mismatch_buf = LocationMatcher.evaluate_transfer_proximity("Mumbai", "Jaipur", "FLIGHT", "TRAIN")
    assert mismatch_type == "inter_city_transfer"
    assert mismatch_buf >= 180

def test_connection_risk_evaluator():
    # Safe connection
    risk, reason = ConnectionRiskEvaluator.evaluate(buffer_minutes=180, min_required_buffer=60, transfer_type="intra_city_transfer")
    assert risk == "SAFE"

    # Tight connection (e.g., 90m available vs 120m min required)
    risk, reason = ConnectionRiskEvaluator.evaluate(buffer_minutes=90, min_required_buffer=120, transfer_type="airport_to_station_transfer")
    assert risk == "TIGHT"

    # Impossible connection (< 0 or severe time deficit)
    risk, reason = ConnectionRiskEvaluator.evaluate(buffer_minutes=-15, min_required_buffer=60, transfer_type="same_terminal")
    assert risk == "IMPOSSIBLE"

def test_journey_graph_engine_user_prompt_scenario():
    """
    Tests exact scenario from prompt:
    Flight: Mumbai -> Delhi (10:00 -> 12:00)
    Train: Delhi -> Jaipur (13:30 -> 17:30) [Connection buffer: 90 mins]
    Hotel: Jaipur Check-in (18:00) [Connection buffer: 30 mins]
    """
    base_date = datetime(2026, 11, 10, 10, 0, 0)
    
    flight = create_mock_booking(
        id=1,
        b_type=BookingType.FLIGHT,
        ref="FL-BOM-DEL",
        provider="IndiGo",
        origin="Mumbai (BOM)",
        dest="Delhi (DEL)",
        start=base_date,
        end=base_date + timedelta(hours=2) # 12:00
    )

    train = create_mock_booking(
        id=2,
        b_type=BookingType.TRAIN,
        ref="TR-DEL-JAI",
        provider="Indian Railways",
        origin="New Delhi (NDLS)",
        dest="Jaipur Junction",
        start=base_date + timedelta(hours=3, minutes=30), # 13:30 (Buffer: 90m)
        end=base_date + timedelta(hours=7, minutes=30)   # 17:30
    )

    hotel = create_mock_booking(
        id=3,
        b_type=BookingType.HOTEL,
        ref="HT-JAIPUR",
        provider="Rambagh Palace",
        origin="Jaipur",
        dest="Jaipur",
        start=base_date + timedelta(hours=8), # 18:00 (Buffer: 30m)
        end=base_date + timedelta(days=2)
    )

    engine = JourneyGraphEngine(journey_id=99)
    resp = engine.build_from_bookings([flight, train, hotel])

    assert resp.total_nodes == 3
    assert resp.total_edges == 2
    assert resp.is_dag is True
    assert resp.topological_sequence == ["booking_1", "booking_2", "booking_3"]

    # Verify Edge 1 (Flight -> Train)
    edge_1 = resp.edges[0]
    assert edge_1.from_booking_id == 1
    assert edge_1.to_booking_id == 2
    assert edge_1.buffer_minutes == 90
    assert edge_1.transfer_type == "airport_to_station_transfer"
    assert edge_1.risk_level == "TIGHT"  # 90m is tight when transferring from Airport to Railway Station (120m recommended)

    # Verify Edge 2 (Train -> Hotel)
    edge_2 = resp.edges[1]
    assert edge_2.from_booking_id == 2
    assert edge_2.to_booking_id == 3
    assert edge_2.buffer_minutes == 30
    assert edge_2.transfer_type == "station_to_hotel_transfer"
    assert edge_2.risk_level == "TIGHT"

    # Risk summary
    assert resp.risk_summary.tight_connections == 2
    assert resp.risk_summary.highest_risk == "TIGHT"
