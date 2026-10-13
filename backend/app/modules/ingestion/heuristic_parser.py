import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from app.schemas.ingestion_schemas import NormalizedBooking, ParserExtractionResult
from app.models.models import EmailParsingStatus
from app.modules.ingestion.classifier import BookingClassifier
from app.modules.ingestion.validator import BookingValidator

class HeuristicEmailParser:
    """
    Robust regex/heuristic parser that extracts structured travel data from emails
    for flights, trains, buses, hotels, and activities.
    """

    @classmethod
    def parse(cls, subject: str, body: str) -> ParserExtractionResult:
        full_text = f"{subject}\n{body}"
        
        # 1. Classify type
        b_type, initial_confidence = BookingClassifier.classify(subject, body)
        if not b_type:
            return ParserExtractionResult(
                success=False,
                status=EmailParsingStatus.UNCERTAIN,
                confidence=0.2,
                booking_type=None,
                missing_fields=["type", "booking_reference", "provider"],
                clarification_prompt="Could not identify the travel booking category from this message.",
                error_message="Travel type could not be classified",
                parser_used="heuristic"
            )

        # 2. Extract common fields
        booking_ref = cls._extract_reference(full_text)
        passenger = cls._extract_passenger(full_text)
        price, currency = cls._extract_price(full_text)

        # 3. Extract type-specific fields
        if b_type == "flight":
            normalized = cls._parse_flight(full_text, booking_ref, passenger, price, currency)
        elif b_type == "train":
            normalized = cls._parse_train(full_text, booking_ref, passenger, price, currency)
        elif b_type == "bus":
            normalized = cls._parse_bus(full_text, booking_ref, passenger, price, currency)
        elif b_type == "hotel":
            normalized = cls._parse_hotel(full_text, booking_ref, passenger, price, currency)
        elif b_type == "activity":
            normalized = cls._parse_activity(full_text, booking_ref, passenger, price, currency)
        else:
            normalized = None

        if not normalized:
            return ParserExtractionResult(
                success=False,
                status=EmailParsingStatus.FAILED,
                confidence=0.3,
                booking_type=b_type,
                missing_fields=["booking_reference"],
                error_message="Failed to structure booking data",
                parser_used="heuristic"
            )

        # 4. Validate and score confidence
        is_valid, missing, confidence, clarification = BookingValidator.validate(normalized)
        status = EmailParsingStatus.PARSED if is_valid else EmailParsingStatus.UNCERTAIN

        return ParserExtractionResult(
            success=True,
            status=status,
            confidence=confidence,
            booking_type=b_type,
            normalized_booking=normalized,
            missing_fields=missing,
            clarification_prompt=clarification,
            parser_used="heuristic"
        )

    # ----------------- Field Extractors -----------------
    @staticmethod
    def _extract_reference(text: str) -> Optional[str]:
        # Try explicit labeled references first
        patterns = [
            r"(?:confirmation\s*(?:number|#|no\.?)|booking\s*reference(?:\s*\(pnr\))?|ticket\s*(?:number|no\.?)|pnr(?:\s*number)?|reservation\s*#|ref(?:\.|erence)?(?:\s*code)?)\s*[:#-]\s*([A-Za-z0-9\-]{5,20})",
            r"(?:confirmation\s*number|booking\s*reference|reservation\s*#)\s*[:#]?\s*([0-9A-Za-z\-]{5,20})",
            r"(?:PNR\s*Number\s*:\s*)([0-9]{10})",
            r"#([0-9]{6,12})\b",
            r"\b([A-Z0-9]{2,4}-[A-Z0-9]{5,12})\b"
        ]
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                ref = match.group(1).strip()
                # filter out false words and ISO date fragments
                if ref.lower() not in ["confirmed", "number", "booking", "details", "status", "reference"]:
                    if not re.match(r"^\d{2}-\d{2}T", ref):
                        return ref
        return None

    @staticmethod
    def _extract_passenger(text: str) -> Optional[str]:
        match = re.search(r"(?:passenger(?:s)?|dear\s*traveler|lead\s*traveler|dear)\s*[:\-]?\s*([A-Za-z\s]{3,30})(?:,|\n|\|)", text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val.lower() not in ["traveler", "customer", "guest", "sir", "madam"]:
                return val
        return None

    @staticmethod
    def _extract_price(text: str) -> Tuple[float, str]:
        # Currency & amount
        match = re.search(r"(inr|usd|eur|gbp|\$|€|₹)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if match:
            curr_str = match.group(1).upper()
            curr_map = {"$": "USD", "€": "EUR", "₹": "INR"}
            curr = curr_map.get(curr_str, curr_str)
            amt_str = match.group(2).replace(",", "")
            try:
                return float(amt_str), curr
            except ValueError:
                pass
        return 0.0, "USD"

    @classmethod
    def _parse_flight(cls, text: str, ref: Optional[str], passenger: Optional[str], price: float, currency: str) -> NormalizedBooking:
        # Provider
        provider = "Airline"
        for airline in ["IndiGo", "Air India", "United Airlines", "Emirates", "Delta", "Lufthansa", "Singapore Airlines", "British Airways", "Vistara", "SpiceJet"]:
            if airline.lower() in text.lower():
                provider = airline
                break

        # Flight Number
        fn_match = re.search(r"(?:flight(?:\s*number)?\s*[:#-]?\s*(?:[A-Za-z]+\s+)?)([A-Z0-9]{2}\s*[-]?\s*\d{3,4})", text, re.IGNORECASE)
        if not fn_match:
            fn_match = re.search(r"\b([0-9][A-Z]|[A-Z][0-9]|[A-Z]{2})\s*[-]?\s*(\d{3,4})\b", text)
            flight_number = f"{fn_match.group(1)}-{fn_match.group(2)}" if fn_match else None
        else:
            flight_number = fn_match.group(1).strip()
            if " " in flight_number and "-" not in flight_number:
                flight_number = flight_number.replace(" ", "-")

        # Origin / Destination
        origin = None
        orig_match = re.search(r"origin\s*:\s*([A-Za-z\s\(\)]+?)(?:-|\n|destination|departure|$)", text, re.IGNORECASE)
        if orig_match and len(orig_match.group(1).strip()) > 1:
            origin = orig_match.group(1).strip()
        else:
            code_match = re.search(r"\b([A-Z]{3})\s*(?:to|->|–)\s*([A-Z]{3})\b", text)
            if code_match:
                origin = code_match.group(1)

        destination = None
        dest_match = re.search(r"destination\s*:\s*([A-Za-z\s\(\)]+?)(?:-|\n|departure|arrival|$)", text, re.IGNORECASE)
        if dest_match and len(dest_match.group(1).strip()) > 1:
            destination = dest_match.group(1).strip()
        elif orig_match and not destination:
            code_match = re.search(r"\b([A-Z]{3})\s*(?:to|->|–)\s*([A-Z]{3})\b", text)
            if code_match:
                destination = code_match.group(2)

        # Cities heuristic fallback
        if not origin or not destination:
            cities_match = re.search(r"\b(Mumbai|Delhi|Bangalore|Singapore|London|New York|San Francisco|Tokyo)\s*(?:to|->|–)\s*(Mumbai|Delhi|Bangalore|Singapore|London|New York|San Francisco|Tokyo)\b", text, re.IGNORECASE)
            if cities_match:
                origin = origin or cities_match.group(1)
                destination = destination or cities_match.group(2)

        # Datetimes
        dep_match = re.search(r"departure\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        departure = dep_match.group(1) if dep_match else None

        arr_match = re.search(r"arrival\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        arrival = arr_match.group(1) if arr_match else None

        seat_match = re.search(r"seat\s*[:#-]?\s*([0-9]{1,2}[A-Z])", text, re.IGNORECASE)
        seat = seat_match.group(1) if seat_match else None

        return NormalizedBooking(
            type="flight",
            provider=provider,
            booking_reference=ref or "",
            title=f"{provider} {flight_number or ''} {origin or ''} -> {destination or ''}".strip(),
            passenger=passenger,
            origin=origin,
            destination=destination,
            departure=departure,
            arrival=arrival,
            flight_number=flight_number,
            seat=seat,
            price=price,
            currency=currency,
            raw_metadata={"parsed_by": "HeuristicEmailParser"}
        )

    @classmethod
    def _parse_train(cls, text: str, ref: Optional[str], passenger: Optional[str], price: float, currency: str) -> NormalizedBooking:
        provider = "Indian Railways (IRCTC)" if "irctc" in text.lower() or "railway" in text.lower() else "Rail Operator"
        
        train_match = re.search(r"train(?:\s*number\s*(?:&|\/)?\s*name)?\s*:\s*([A-Za-z0-9\s\/]+?)(?:\n|class|$)", text, re.IGNORECASE)
        train_number = train_match.group(1).strip() if train_match else None

        orig_match = re.search(r"(?:from\s*station|from)\s*:\s*([A-Za-z0-9\s\(\)]+?)(?:\n|to|$)", text, re.IGNORECASE)
        origin = orig_match.group(1).strip() if orig_match else None

        dest_match = re.search(r"(?:to\s*station|to)\s*:\s*([A-Za-z0-9\s\(\)]+?)(?:\n|date|$)", text, re.IGNORECASE)
        destination = dest_match.group(1).strip() if dest_match else None

        dep_match = re.search(r"(?:date\s*of\s*journey|departure)\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        departure = dep_match.group(1) if dep_match else None

        arr_match = re.search(r"(?:scheduled\s*arrival|arrival)\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        arrival = arr_match.group(1) if arr_match else None

        seat_match = re.search(r"(?:seat|berth)\s*[:#-]?\s*([0-9]{1,2}\s*(?:\([A-Za-z\s]+\))?)", text, re.IGNORECASE)
        seat = seat_match.group(1) if seat_match else None

        return NormalizedBooking(
            type="train",
            provider=provider,
            booking_reference=ref or "",
            title=f"{train_number or 'Train'} {origin or ''} -> {destination or ''}".strip(),
            passenger=passenger,
            origin=origin,
            destination=destination,
            departure=departure,
            arrival=arrival,
            train_number=train_number,
            seat=seat,
            price=price,
            currency=currency,
            raw_metadata={"parsed_by": "HeuristicEmailParser"}
        )

    @classmethod
    def _parse_bus(cls, text: str, ref: Optional[str], passenger: Optional[str], price: float, currency: str) -> NormalizedBooking:
        provider = "redBus" if "redbus" in text.lower() else "Intercity Bus"
        op_match = re.search(r"operator\s*:\s*([A-Za-z0-9\s\(\)\+]+?)(?:\n|passenger|$)", text, re.IGNORECASE)
        if op_match:
            provider = op_match.group(1).strip()

        orig_match = re.search(r"boarding\s*point\s*:\s*([A-Za-z0-9\s,]+?)(?:\n|drop|$)", text, re.IGNORECASE)
        origin = orig_match.group(1).strip() if orig_match else None

        dest_match = re.search(r"drop-off\s*point\s*:\s*([A-Za-z0-9\s,]+?)(?:\n|departure|$)", text, re.IGNORECASE)
        destination = dest_match.group(1).strip() if dest_match else None

        dep_match = re.search(r"departure\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        departure = dep_match.group(1) if dep_match else None

        arr_match = re.search(r"arrival\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        arrival = arr_match.group(1) if arr_match else None

        seat_match = re.search(r"seat(?:\s*number)?\s*[:#-]?\s*([0-9]{1,2}[A-Za-z]*)", text, re.IGNORECASE)
        seat = seat_match.group(1) if seat_match else None

        return NormalizedBooking(
            type="bus",
            provider=provider,
            booking_reference=ref or "",
            title=f"{provider} {origin or ''} -> {destination or ''}".strip(),
            passenger=passenger,
            origin=origin,
            destination=destination,
            departure=departure,
            arrival=arrival,
            seat=seat,
            price=price,
            currency=currency,
            raw_metadata={"parsed_by": "HeuristicEmailParser"}
        )

    @classmethod
    def _parse_hotel(cls, text: str, ref: Optional[str], passenger: Optional[str], price: float, currency: str) -> NormalizedBooking:
        hotel_match = re.search(r"hotel\s*:\s*([A-Za-z0-9\s]+?)(?:\n|location|$)", text, re.IGNORECASE)
        hotel_name = hotel_match.group(1).strip() if hotel_match else "Hotel"
        if hotel_name == "Hotel":
            for brand in ["JW Marriott Mumbai Sahar", "Park Hyatt Tokyo", "Taj MG Road", "Marriott", "Hyatt", "Hilton", "Taj", "Radisson"]:
                if brand.lower() in text.lower():
                    hotel_name = brand
                    break

        loc_match = re.search(r"location\s*:\s*([A-Za-z0-9\s,]+?)(?:\n|phone|$)", text, re.IGNORECASE)
        location = loc_match.group(1).strip() if loc_match else "Hotel Location"

        checkin_match = re.search(r"check-in\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        checkin = checkin_match.group(1) if checkin_match else None

        checkout_match = re.search(r"check-out\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        checkout = checkout_match.group(1) if checkout_match else None

        room_match = re.search(r"(?:room\s*details|room)\s*:\s*([A-Za-z0-9\s,]+?)(?:\n|rate|$)", text, re.IGNORECASE)
        room_type = room_match.group(1).strip() if room_match else None

        return NormalizedBooking(
            type="hotel",
            provider=hotel_name,
            booking_reference=ref or "",
            title=f"{hotel_name} Stay",
            passenger=passenger,
            origin=location,
            destination=location,
            departure=checkin,
            arrival=checkout,
            hotel_name=hotel_name,
            room_type=room_type,
            price=price,
            currency=currency,
            raw_metadata={"parsed_by": "HeuristicEmailParser"}
        )

    @classmethod
    def _parse_activity(cls, text: str, ref: Optional[str], passenger: Optional[str], price: float, currency: str) -> NormalizedBooking:
        act_match = re.search(r"activity\s*:\s*([A-Za-z0-9\s&]+?)(?:\n|booking|$)", text, re.IGNORECASE)
        activity_title = act_match.group(1).strip() if act_match else "Tour Experience"

        prov_match = re.search(r"provider\s*:\s*([A-Za-z0-9\s&]+?)(?:\n|tour|$)", text, re.IGNORECASE)
        provider = prov_match.group(1).strip() if prov_match else "Tour Provider"

        meet_match = re.search(r"meeting\s*point\s*:\s*([A-Za-z0-9\s,.]+?)(?:\n|tour|$)", text, re.IGNORECASE)
        meeting_point = meet_match.group(1).strip() if meet_match else "Meeting Point"

        time_match = re.search(r"(?:tour\s*date\s*&?\s*start\s*time|start\s*time)\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        departure = time_match.group(1) if time_match else None

        end_match = re.search(r"end\s*time\s*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
        arrival = end_match.group(1) if end_match else None

        return NormalizedBooking(
            type="activity",
            provider=provider,
            booking_reference=ref or "",
            title=activity_title,
            passenger=passenger,
            origin=meeting_point,
            destination=meeting_point,
            departure=departure,
            arrival=arrival,
            price=price,
            currency=currency,
            raw_metadata={"parsed_by": "HeuristicEmailParser"}
        )
