from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class NotificationCategory(str, Enum):
    TRAVELER_NOTIFICATION = "traveler_notification"
    HOTEL_NOTIFICATION = "hotel_notification"
    SUPPLIER_COMMUNICATION = "supplier_communication"
    REFUND_REQUEST = "refund_request"
    CANCELLATION_REQUEST = "cancellation_request"
    EMERGENCY_CONTACT_NOTIFICATION = "emergency_contact_notification"


CATEGORY_METADATA: Dict[str, Dict[str, str]] = {
    NotificationCategory.TRAVELER_NOTIFICATION.value: {
        "label": "1. Traveler Notification",
        "template_id": "TPL-TRAVELER-RECOVERY-V1",
        "description": "Comprehensive itinerary update with rebooked transport, hotel check-in, and refund summary.",
    },
    NotificationCategory.HOTEL_NOTIFICATION.value: {
        "label": "2. Hotel Notification",
        "template_id": "TPL-HOTEL-LATE-CHECKIN-V1",
        "description": "Front-desk alert updating guest expected arrival time and guaranteeing late check-in.",
    },
    NotificationCategory.SUPPLIER_COMMUNICATION.value: {
        "label": "3. Supplier Communication",
        "template_id": "TPL-SUPPLIER-DISRUPTION-V1",
        "description": "Operational notice to transport supplier documenting involuntary connection disruption.",
    },
    NotificationCategory.REFUND_REQUEST.value: {
        "label": "4. Refund Request",
        "template_id": "TPL-SUPPLIER-REFUND-CLAIM-V1",
        "description": "Structured refund claim citing exact ticket price, refund amount, and supplier policy code.",
    },
    NotificationCategory.CANCELLATION_REQUEST.value: {
        "label": "5. Cancellation Request",
        "template_id": "TPL-SUPPLIER-CANCEL-V1",
        "description": "Formal cancellation dispatch for missed/disrupted transport segment.",
    },
    NotificationCategory.EMERGENCY_CONTACT_NOTIFICATION.value: {
        "label": "6. Emergency Contact Notification",
        "template_id": "TPL-EMERGENCY-CONTACT-V1",
        "description": "Safety and revised schedule update for the traveler's designated emergency contact.",
    },
}


class StructuredRecoveryFacts(BaseModel):
    """
    Canonical ground-truth system data used to populate templates and validate AI drafts.
    The LLM is strictly prohibited from inventing any booking ref, price, date/time, or policy outside this object.
    """
    journey_id: int = 1
    passenger_name: str = "Aarav Sharma"
    passenger_email: str = "aarav.sharma@example.com"
    emergency_contact_name: str = "Priya Sharma"
    emergency_contact_email: str = "priya.sharma.family@example.com"

    disruption_id: str = "DISR-AI202-240M"
    disruption_type: str = "Flight Delay (+240 minutes)"
    disrupted_booking_ref: str = "AI-202"
    disrupted_provider: str = "Air India"
    disrupted_route: str = "Mumbai (BOM) -> Delhi (DEL)"
    delay_minutes: int = 240
    disruption_date: str = "2026-10-20"
    original_arrival_time: str = "12:00"
    revised_arrival_time: str = "16:00"

    missed_booking_ref: str = "12015-SHT"
    missed_transport_id: str = "TRN123"
    missed_provider: str = "Indian Railways"
    missed_route: str = "Delhi -> Jaipur"
    missed_departure_time: str = "13:30"
    missed_arrival_time: str = "17:30"
    missed_ticket_price_inr: float = 800.0

    refund_amount_inr: float = 600.0
    refund_policy_code: str = "IRCTC-INV-DELAY-75PCT"
    refund_policy_summary: str = "75% Refundable under IRCTC Missed Connection Protection Policy (INR 600.00 of INR 800.00)"

    rebooked_booking_ref: str = "PNR-TRN124-8821"
    rebooked_transport_id: str = "TRN124"
    rebooked_provider: str = "Indian Railways"
    rebooked_service_name: str = "Ashram Express 12916"
    rebooked_departure_time: str = "17:30"
    rebooked_arrival_time: str = "21:00"
    rebooked_price_inr: float = 750.0

    hotel_booking_ref: str = "HTL-JAI-101"
    hotel_id: str = "HTL101"
    hotel_name: str = "Rambagh Heritage Palace Jaipur"
    hotel_email: str = "frontdesk@heritagepalacejaipur.com"
    hotel_original_checkin: str = "18:00"
    hotel_revised_checkin: str = "21:30"
    hotel_latest_cutoff: str = "22:00"
    hotel_policy_code: str = "HTL-LATE-HOLD-2200"
    hotel_policy_summary: str = "Room held without penalty when revised arrival is registered prior to 22:00 cutoff"

    supplier_support_email: str = "ops.support@indianrailways.mock.in"
    refund_dept_email: str = "refunds.claims@irctc.mock.in"
    cancellation_dept_email: str = "cancellations@irctc.mock.in"


class FactValidationReport(BaseModel):
    """Validation report verifying that no booking numbers, prices, dates, or policies were invented."""
    is_valid: bool = True
    validation_mode: str = "STRICT_FACT_GROUNDING_V1"
    allowed_booking_refs: List[str] = Field(default_factory=list)
    allowed_prices_inr: List[float] = Field(default_factory=list)
    allowed_dates_times: List[str] = Field(default_factory=list)
    allowed_policy_codes: List[str] = Field(default_factory=list)
    hallucinations_detected: List[str] = Field(default_factory=list)
    fallback_applied: bool = False


class GeneratedNotificationRecord(BaseModel):
    """
    Simulated Email & Notification Inbox Record with all required fields:
    Recipient, Subject, Message, Status, Timestamp, Related booking, Related disruption.
    """
    notification_id: str
    category: str
    category_label: str
    recipient_name: str
    recipient_email: str
    recipient: str = Field(..., description="Formatted Recipient display string")
    subject: str = Field(..., description="Email subject line")
    message: str = Field(..., description="Validated email body")
    status: str = Field(..., description="Delivery and validation status")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    related_booking: str = Field(..., description="Primary related booking reference(s)")
    related_disruption: str = Field(..., description="Related disruption ID and description")
    template_id: str
    generator_used: str
    validation: FactValidationReport
    ungrounded_draft_blocked: Optional[str] = None
    simulated: bool = True


class GenerateNotificationSuiteRequest(BaseModel):
    """Request to generate all 6 notification types (or a specific subset) from structured recovery data."""
    facts: StructuredRecoveryFacts = Field(default_factory=StructuredRecoveryFacts)
    categories: Optional[List[str]] = None
    simulate_hallucination_test: bool = Field(
        default=False,
        description="When True, simulates an ungrounded LLM draft attempting to invent booking refs, prices, dates, and policy rules to test the FactGroundingValidator."
    )


class ValidateDraftRequest(BaseModel):
    """Request to validate a custom AI-generated draft against structured recovery facts."""
    category: str = NotificationCategory.REFUND_REQUEST.value
    draft_subject: str
    draft_message: str
    facts: StructuredRecoveryFacts = Field(default_factory=StructuredRecoveryFacts)
