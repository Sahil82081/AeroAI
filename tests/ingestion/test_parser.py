import pytest
from app.modules.ingestion.heuristic_parser import HeuristicEmailParser
from app.modules.ingestion.classifier import BookingClassifier
from app.modules.ingestion.validator import BookingValidator
from app.schemas.ingestion_schemas import NormalizedBooking
from app.models.models import EmailParsingStatus
from app.datasets.sample_emails import SAMPLE_EMAILS

def test_booking_classifier_all_types():
    for item in SAMPLE_EMAILS:
        category, confidence = BookingClassifier.classify(item["subject"], item["body"])
        assert category == item["expected_type"], f"Failed classification for {item['id']}: got {category}, expected {item['expected_type']}"
        assert confidence > 0.0

def test_heuristic_parser_flight():
    flight_sample = next(e for e in SAMPLE_EMAILS if e["id"] == "flight-indigo-6e")
    result = HeuristicEmailParser.parse(flight_sample["subject"], flight_sample["body"])
    
    assert result.success is True
    assert result.status == EmailParsingStatus.PARSED
    assert result.booking_type == "flight"
    assert result.confidence >= 0.8
    assert result.normalized_booking.booking_reference == "6E-IND789"
    assert result.normalized_booking.provider == "IndiGo"
    assert "Mumbai" in result.normalized_booking.origin
    assert "Delhi" in result.normalized_booking.destination
    assert result.normalized_booking.flight_number == "6E-205"
    assert result.normalized_booking.price == 5850.0

def test_heuristic_parser_train():
    train_sample = next(e for e in SAMPLE_EMAILS if e["id"] == "train-irctc-rajdhani")
    result = HeuristicEmailParser.parse(train_sample["subject"], train_sample["body"])

    assert result.success is True
    assert result.status == EmailParsingStatus.PARSED
    assert result.booking_type == "train"
    assert result.normalized_booking.booking_reference == "2458901234"
    assert "IRCTC" in result.normalized_booking.provider
    assert "Mumbai" in result.normalized_booking.origin
    assert "New Delhi" in result.normalized_booking.destination

def test_heuristic_parser_hotel():
    hotel_sample = next(e for e in SAMPLE_EMAILS if e["id"] == "hotel-marriott-mumbai")
    result = HeuristicEmailParser.parse(hotel_sample["subject"], hotel_sample["body"])

    assert result.success is True
    assert result.status == EmailParsingStatus.PARSED
    assert result.booking_type == "hotel"
    assert result.normalized_booking.booking_reference == "92834110"
    assert "Marriott" in result.normalized_booking.provider

def test_heuristic_parser_bus():
    bus_sample = next(e for e in SAMPLE_EMAILS if e["id"] == "bus-redbus-express")
    result = HeuristicEmailParser.parse(bus_sample["subject"], bus_sample["body"])

    assert result.success is True
    assert result.status == EmailParsingStatus.PARSED
    assert result.booking_type == "bus"
    assert result.normalized_booking.booking_reference == "TIN-9823487"

def test_heuristic_parser_activity():
    act_sample = next(e for e in SAMPLE_EMAILS if e["id"] == "activity-getyourguide-tour")
    result = HeuristicEmailParser.parse(act_sample["subject"], act_sample["body"])

    assert result.success is True
    assert result.status == EmailParsingStatus.PARSED
    assert result.booking_type == "activity"
    assert result.normalized_booking.booking_reference == "GYG-77412"

def test_imperfect_email_validation_and_uncertainty():
    imperfect_sample = next(e for e in SAMPLE_EMAILS if e["id"] == "imperfect-flight-forward")
    result = HeuristicEmailParser.parse(imperfect_sample["subject"], imperfect_sample["body"])

    assert result.success is True
    assert result.status == EmailParsingStatus.UNCERTAIN
    assert len(result.missing_fields) > 0
    assert result.clarification_prompt is not None
    assert "Air India" in result.normalized_booking.provider
    assert result.normalized_booking.booking_reference == "AI-REF90021"

def test_booking_validator_identifies_missing_mandatory_fields():
    # Construct an incomplete flight booking lacking arrival and destination
    incomplete_booking = NormalizedBooking(
        type="flight",
        provider="Delta Air Lines",
        booking_reference="DL-9999",
        origin="JFK",
        destination=None,
        departure="2026-11-01T10:00:00",
        arrival=None
    )
    is_valid, missing, confidence, clarification = BookingValidator.validate(incomplete_booking)

    assert is_valid is False
    assert "destination" in missing
    assert "arrival" in missing
    assert confidence <= 0.75
    assert clarification is not None
    assert "destination" in clarification
