from typing import Tuple, List, Optional
from app.schemas.ingestion_schemas import NormalizedBooking

class BookingValidator:
    """
    Validates normalized bookings. Checks for mandatory fields per booking type,
    identifies missing fields, and evaluates uncertainty without inventing data.
    """

    MANDATORY_FIELDS = {
        "flight": ["provider", "booking_reference", "origin", "destination", "departure", "arrival"],
        "train": ["provider", "booking_reference", "origin", "destination", "departure", "arrival"],
        "bus": ["provider", "booking_reference", "origin", "destination", "departure", "arrival"],
        "hotel": ["provider", "booking_reference", "origin", "departure", "arrival"], # origin is location, departure is check-in, arrival is check-out
        "activity": ["provider", "booking_reference", "origin", "departure"] # origin is meeting point, departure is start time
    }

    DESIRABLE_FIELDS = {
        "flight": ["flight_number", "seat", "passenger", "price"],
        "train": ["train_number", "seat", "passenger", "price"],
        "bus": ["bus_number", "seat", "passenger", "price"],
        "hotel": ["room_type", "price"],
        "activity": ["duration", "passenger", "price"]
    }

    @classmethod
    def validate(cls, booking: NormalizedBooking) -> Tuple[bool, List[str], float, Optional[str]]:
        """
        Returns:
            (is_valid, missing_mandatory_fields, final_confidence, clarification_prompt)
        """
        b_type = booking.type
        mandatory = cls.MANDATORY_FIELDS.get(b_type, ["provider", "booking_reference"])
        
        missing = []
        data = booking.model_dump()

        for field in mandatory:
            val = data.get(field)
            if val is None or str(val).strip() == "":
                missing.append(field)

        # Calculate completeness ratio
        total_mandatory = len(mandatory)
        present_mandatory = total_mandatory - len(missing)
        completeness_ratio = present_mandatory / max(1, total_mandatory)

        # Baseline confidence scaling
        confidence = round(0.4 + (0.55 * completeness_ratio), 2)
        if missing:
            confidence = min(confidence, 0.75) # Cap confidence if mandatory fields are missing

        clarification_prompt = None
        if missing:
            readable_fields = ", ".join([f.replace("_", " ") for f in missing])
            clarification_prompt = (
                f"We received your {b_type.capitalize()} booking forward (Ref: {booking.booking_reference or 'Unknown'}), "
                f"but could not confirm critical details: {readable_fields}. "
                f"Please verify or provide these details so we can safeguard downstream connections."
            )

        is_valid = len(missing) == 0
        return is_valid, missing, confidence, clarification_prompt
