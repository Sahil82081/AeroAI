"""
Stage 10: Email and Notification Agent with Strict Fact-Grounding & Anti-Hallucination Guardrails.

Generates 6 communication types:
1. Traveler notification (`traveler_notification`)
2. Hotel notification (`hotel_notification`)
3. Supplier communication (`supplier_communication`)
4. Refund request (`refund_request`)
5. Cancellation request (`cancellation_request`)
6. Emergency contact notification (`emergency_contact_notification`)

CRITICAL INVARIANT:
The LLM/generator must NEVER invent booking numbers, prices, dates, times, or policy rules.
All factual values are extracted strictly from `StructuredRecoveryFacts` and verified by
`FactGroundingValidator`. Any draft containing ungrounded tokens is blocked and replaced
by the deterministic fact-grounded template.
"""
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set
from app.schemas.notification_schemas import (
    NotificationCategory,
    CATEGORY_METADATA,
    StructuredRecoveryFacts,
    FactValidationReport,
    GeneratedNotificationRecord,
)


class FactGroundingValidator:
    """
    Validates that a generated email subject & body contain ZERO invented booking numbers,
    prices, dates, times, or policy codes outside `StructuredRecoveryFacts`.
    """

    UNGROUNDED_POLICY_PHRASES = [
        "eu261",
        "200% refund",
        "100% full cash bonus",
        "complimentary business class",
        "free presidential suite",
        "dgca-tier-9",
    ]

    @classmethod
    def build_whitelists(cls, facts: StructuredRecoveryFacts) -> Tuple[Set[str], Set[float], Set[str], Set[str]]:
        allowed_refs: Set[str] = {
            facts.disrupted_booking_ref.upper(),
            facts.disruption_id.upper(),
            facts.missed_booking_ref.upper(),
            facts.missed_transport_id.upper(),
            facts.rebooked_booking_ref.upper(),
            facts.rebooked_transport_id.upper(),
            facts.hotel_booking_ref.upper(),
            facts.hotel_id.upper(),
            facts.refund_policy_code.upper(),
            facts.hotel_policy_code.upper(),
        }
        allowed_prices: Set[float] = {
            round(float(facts.missed_ticket_price_inr), 2),
            round(float(facts.refund_amount_inr), 2),
            round(float(facts.rebooked_price_inr), 2),
        }
        allowed_dates_times: Set[str] = {
            facts.disruption_date,
            facts.original_arrival_time,
            facts.revised_arrival_time,
            facts.missed_departure_time,
            facts.missed_arrival_time,
            facts.rebooked_departure_time,
            facts.rebooked_arrival_time,
            facts.hotel_original_checkin,
            facts.hotel_revised_checkin,
            facts.hotel_latest_cutoff,
        }
        allowed_policies: Set[str] = {
            facts.refund_policy_code.upper(),
            facts.hotel_policy_code.upper(),
        }
        return allowed_refs, allowed_prices, allowed_dates_times, allowed_policies

    @classmethod
    def validate(
        cls,
        subject: str,
        message: str,
        facts: StructuredRecoveryFacts,
    ) -> FactValidationReport:
        allowed_refs, allowed_prices, allowed_dates_times, allowed_policies = cls.build_whitelists(facts)
        combined = f"{subject}\n{message}"
        hallucinations: List[str] = []

        # 1. Check booking / reference / policy code patterns (e.g. AI-202, PNR-9999, HTL-JAI-101, TRN124)
        code_tokens = set(
            re.findall(r"\b(?:[A-Z]{2,6}-[A-Z0-9-]{2,16}|(?:TRN|FLT|BUS|HTL|PNR)\d{2,8})\b", combined)
        )
        for token in sorted(code_tokens):
            if token.upper() not in allowed_refs:
                hallucinations.append(f"INVENTED_BOOKING_OR_POLICY_REF: '{token}' is not in system facts")

        # 2. Check monetary amounts & currencies (e.g. INR 800, ₹600.00, $450, EUR 600)
        foreign_currency_matches = re.findall(r"(?:\$|USD|€|EUR|£|GBP)\s*\d+(?:\.\d{1,2})?", combined)
        for fc in foreign_currency_matches:
            hallucinations.append(f"INVENTED_CURRENCY_OR_PRICE: '{fc}' (only grounded INR amounts are permitted)")

        inr_matches = re.findall(r"(?:INR|₹|Rs\.?)\s*([0-9]+(?:\.[0-9]{1,2})?)", combined)
        for amt_str in inr_matches:
            amt_val = round(float(amt_str), 2)
            if amt_val not in allowed_prices:
                hallucinations.append(
                    f"INVENTED_PRICE_AMOUNT: 'INR {amt_str}' does not match any grounded fare/refund {sorted(allowed_prices)}"
                )

        # 3. Check ISO dates (YYYY-MM-DD)
        date_matches = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", combined))
        for dt_str in sorted(date_matches):
            if dt_str not in allowed_dates_times:
                hallucinations.append(f"INVENTED_DATE: '{dt_str}' is not the grounded travel date ({facts.disruption_date})")

        # 4. Check 24-hour clock times (HH:MM)
        time_matches = set(re.findall(r"\b(?:[01]\d|2[0-3]):[0-5]\d\b", combined))
        for tm_str in sorted(time_matches):
            if tm_str not in allowed_dates_times:
                hallucinations.append(f"INVENTED_TIME: '{tm_str}' is not in grounded schedule timestamps")

        # 5. Check ungrounded policy phrases
        lower_text = combined.lower()
        for phrase in cls.UNGROUNDED_POLICY_PHRASES:
            if phrase in lower_text:
                hallucinations.append(f"INVENTED_POLICY_CLAIM: Ungrounded policy phrase '{phrase}' detected")

        return FactValidationReport(
            is_valid=len(hallucinations) == 0,
            validation_mode="STRICT_FACT_GROUNDING_V1",
            allowed_booking_refs=sorted(allowed_refs),
            allowed_prices_inr=sorted(allowed_prices),
            allowed_dates_times=sorted(allowed_dates_times),
            allowed_policy_codes=sorted(allowed_policies),
            hallucinations_detected=hallucinations,
            fallback_applied=False,
        )


class NotificationTemplateEngine:
    """
    Deterministic, 100% fact-grounded email templates for all 6 notification categories.
    """

    @staticmethod
    def render(category: str, facts: StructuredRecoveryFacts) -> Dict[str, str]:
        if category == NotificationCategory.TRAVELER_NOTIFICATION.value:
            recipient_name = facts.passenger_name
            recipient_email = facts.passenger_email
            related_booking = f"{facts.disrupted_booking_ref}, {facts.missed_booking_ref} -> {facts.rebooked_booking_ref} ({facts.rebooked_transport_id}), {facts.hotel_booking_ref}"
            subject = (
                f"[Recovery Confirmed] Updated Itinerary for {facts.disruption_date} — "
                f"Rebooked onto {facts.rebooked_service_name} ({facts.rebooked_booking_ref})"
            )
            message = (
                f"Dear {facts.passenger_name},\n\n"
                f"We detected a disruption on your {facts.disrupted_provider} flight {facts.disrupted_booking_ref} "
                f"({facts.disrupted_route}) on {facts.disruption_date} (Disruption Ref: {facts.disruption_id}). "
                f"Your flight arrival shifted by +{facts.delay_minutes} minutes from {facts.original_arrival_time} to {facts.revised_arrival_time}, "
                f"causing a missed connection for {facts.missed_provider} train {facts.missed_booking_ref} ({facts.missed_transport_id}) "
                f"scheduled at {facts.missed_departure_time}.\n\n"
                f"AUTONOMOUS RECOVERY SUMMARY:\n"
                f"1. Replacement Transport Confirmed: {facts.rebooked_provider} — {facts.rebooked_service_name} "
                f"(Transport ID: {facts.rebooked_transport_id}, Booking Ref: {facts.rebooked_booking_ref})\n"
                f"   - Route: {facts.missed_route} on {facts.disruption_date}\n"
                f"   - Departure: {facts.rebooked_departure_time} | Arrival: {facts.rebooked_arrival_time}\n"
                f"   - Confirmed Fare: INR {facts.rebooked_price_inr:.2f}\n\n"
                f"2. Original Segment Cancelled & Refund Claim Filed:\n"
                f"   - Cancelled Booking Ref: {facts.missed_booking_ref} (Original Fare: INR {facts.missed_ticket_price_inr:.2f})\n"
                f"   - Eligible Refund Requested: INR {facts.refund_amount_inr:.2f} under Policy {facts.refund_policy_code}\n"
                f"   - Policy Rule: {facts.refund_policy_summary}\n\n"
                f"3. Hotel Check-In Updated:\n"
                f"   - Property: {facts.hotel_name} (Booking Ref: {facts.hotel_booking_ref})\n"
                f"   - Updated Check-In Time: {facts.hotel_revised_checkin} (Prior to {facts.hotel_latest_cutoff} cutoff under Policy {facts.hotel_policy_code})\n\n"
                f"Safe travels,\n"
                f"Autonomous Disruption Recovery Agent"
            )

        elif category == NotificationCategory.HOTEL_NOTIFICATION.value:
            recipient_name = f"{facts.hotel_name} Front Desk"
            recipient_email = facts.hotel_email
            related_booking = f"{facts.hotel_booking_ref} ({facts.hotel_id})"
            subject = (
                f"[Late Check-In Notice] Booking {facts.hotel_booking_ref} — Guest {facts.passenger_name} "
                f"Revised Arrival {facts.hotel_revised_checkin} on {facts.disruption_date}"
            )
            message = (
                f"Dear Reservations & Front Desk Team at {facts.hotel_name},\n\n"
                f"Please update the expected arrival window for guest {facts.passenger_name} holding confirmed reservation "
                f"{facts.hotel_booking_ref} (Property ID: {facts.hotel_id}) on {facts.disruption_date}.\n\n"
                f"VERIFIED DISRUPTION & TRANSIT DETAILS:\n"
                f"- Disruption Reference: {facts.disruption_id} ({facts.disrupted_provider} {facts.disrupted_booking_ref} delayed +{facts.delay_minutes}m, "
                f"revised hub arrival {facts.revised_arrival_time})\n"
                f"- Rebooked Connecting Train: {facts.rebooked_provider} {facts.rebooked_service_name} "
                f"(Transport ID: {facts.rebooked_transport_id}, PNR: {facts.rebooked_booking_ref})\n"
                f"- Train Schedule: Departs {facts.rebooked_departure_time}, Arrives Jaipur at {facts.rebooked_arrival_time} on {facts.disruption_date}\n"
                f"- Original Check-In Time: {facts.hotel_original_checkin}\n"
                f"- Revised Expected Check-In Time: {facts.hotel_revised_checkin} (Before {facts.hotel_latest_cutoff} cutoff)\n"
                f"- Applicable Protection Policy: {facts.hotel_policy_code} — {facts.hotel_policy_summary}\n\n"
                f"Kindly hold the room for {facts.passenger_name} and confirm late check-in registration.\n\n"
                f"Sincerely,\n"
                f"Autonomous Disruption Recovery Agent"
            )

        elif category == NotificationCategory.SUPPLIER_COMMUNICATION.value:
            recipient_name = f"{facts.missed_provider} Operations Desk"
            recipient_email = facts.supplier_support_email
            related_booking = f"{facts.missed_booking_ref} ({facts.missed_transport_id}) -> {facts.rebooked_booking_ref} ({facts.rebooked_transport_id})"
            subject = (
                f"[Operational Disruption Link] Involuntary Missed Connection on {facts.missed_booking_ref} "
                f"Due to Inbound {facts.disrupted_booking_ref} Delay ({facts.disruption_id})"
            )
            message = (
                f"To: {facts.missed_provider} Operations & Passenger Protection Desk,\n\n"
                f"This dispatch records an involuntary inter-modal missed connection for passenger {facts.passenger_name} on {facts.disruption_date}.\n\n"
                f"STRUCTURED INCIDENT RECORD:\n"
                f"- Upstream Disruption ID: {facts.disruption_id}\n"
                f"- Upstream Carrier & Booking: {facts.disrupted_provider} {facts.disrupted_booking_ref} ({facts.disrupted_route})\n"
                f"- Verified Arrival Shift: Scheduled {facts.original_arrival_time} -> Revised {facts.revised_arrival_time} (+{facts.delay_minutes} minutes)\n"
                f"- Affected Downstream Booking: {facts.missed_booking_ref} (Transport ID: {facts.missed_transport_id}, Scheduled Departure: {facts.missed_departure_time})\n"
                f"- Rebooked Replacement Segment: {facts.rebooked_booking_ref} (Transport ID: {facts.rebooked_transport_id}, "
                f"Departure: {facts.rebooked_departure_time}, Arrival: {facts.rebooked_arrival_time}, Fare: INR {facts.rebooked_price_inr:.2f})\n"
                f"- Applicable Tariff Rule: {facts.refund_policy_code}\n\n"
                f"Please link PNR {facts.missed_booking_ref} and {facts.rebooked_booking_ref} in your manifest.\n\n"
                f"Regards,\n"
                f"Autonomous Disruption Recovery Agent"
            )

        elif category == NotificationCategory.REFUND_REQUEST.value:
            recipient_name = f"{facts.missed_provider} Refunds & Claims Department"
            recipient_email = facts.refund_dept_email
            related_booking = f"{facts.missed_booking_ref} ({facts.missed_transport_id})"
            subject = (
                f"[Refund Claim {facts.refund_policy_code}] Booking {facts.missed_booking_ref} — "
                f"Requesting INR {facts.refund_amount_inr:.2f} Refund on INR {facts.missed_ticket_price_inr:.2f} Fare"
            )
            message = (
                f"To: {facts.missed_provider} Refunds & Claims Department,\n\n"
                f"Please process an involuntary missed-connection refund for booking {facts.missed_booking_ref} "
                f"(Transport ID: {facts.missed_transport_id}) on {facts.disruption_date}.\n\n"
                f"VERIFIED CLAIM PARTICULARS:\n"
                f"- Passenger Name: {facts.passenger_name}\n"
                f"- Cancelled Booking Reference: {facts.missed_booking_ref} (Transport ID: {facts.missed_transport_id})\n"
                f"- Scheduled Segment: {facts.missed_route} departing {facts.missed_departure_time}, arriving {facts.missed_arrival_time} on {facts.disruption_date}\n"
                f"- Cause of Missed Connection: {facts.disruption_id} — {facts.disrupted_provider} {facts.disrupted_booking_ref} "
                f"arrived at {facts.revised_arrival_time} instead of {facts.original_arrival_time} (+{facts.delay_minutes}m delay)\n"
                f"- Original Ticket Price Paid: INR {facts.missed_ticket_price_inr:.2f}\n"
                f"- Refund Amount Requested: INR {facts.refund_amount_inr:.2f}\n"
                f"- Governing Policy Code: {facts.refund_policy_code} ({facts.refund_policy_summary})\n\n"
                f"Kindly credit INR {facts.refund_amount_inr:.2f} to the original payment instrument.\n\n"
                f"Regards,\n"
                f"Autonomous Disruption Recovery Agent"
            )

        elif category == NotificationCategory.CANCELLATION_REQUEST.value:
            recipient_name = f"{facts.missed_provider} Cancellations Desk"
            recipient_email = facts.cancellation_dept_email
            related_booking = f"{facts.missed_booking_ref} ({facts.missed_transport_id})"
            subject = (
                f"[Cancellation Confirmation] Release Seat for Booking {facts.missed_booking_ref} "
                f"({facts.missed_transport_id}) on {facts.disruption_date}"
            )
            message = (
                f"To: {facts.missed_provider} Cancellations & Inventory Control,\n\n"
                f"Please record the formal cancellation of booking {facts.missed_booking_ref} (Transport ID: {facts.missed_transport_id}) "
                f"for passenger {facts.passenger_name} on {facts.disruption_date}.\n\n"
                f"CANCELLATION METADATA:\n"
                f"- Booking Reference: {facts.missed_booking_ref}\n"
                f"- Transport ID & Route: {facts.missed_transport_id} ({facts.missed_route})\n"
                f"- Scheduled Departure / Arrival: {facts.missed_departure_time} -> {facts.missed_arrival_time} on {facts.disruption_date}\n"
                f"- Original Fare: INR {facts.missed_ticket_price_inr:.2f}\n"
                f"- Cancellation Reason: Involuntary missed connection caused by {facts.disruption_id} "
                f"({facts.disrupted_booking_ref} arrival delayed from {facts.original_arrival_time} to {facts.revised_arrival_time})\n"
                f"- Applicable Policy: {facts.refund_policy_code}\n\n"
                f"Regards,\n"
                f"Autonomous Disruption Recovery Agent"
            )

        else:  # EMERGENCY_CONTACT_NOTIFICATION
            recipient_name = f"{facts.emergency_contact_name} (Emergency Contact)"
            recipient_email = facts.emergency_contact_email
            related_booking = f"{facts.disrupted_booking_ref}, {facts.rebooked_booking_ref} ({facts.rebooked_transport_id}), {facts.hotel_booking_ref}"
            subject = (
                f"[Family/Emergency Travel Update] {facts.passenger_name}'s Revised Schedule on {facts.disruption_date} "
                f"(Arriving Jaipur at {facts.rebooked_arrival_time})"
            )
            message = (
                f"Hello {facts.emergency_contact_name},\n\n"
                f"You are listed as the designated emergency contact for {facts.passenger_name}. "
                f"We are writing to let you know that {facts.passenger_name}'s flight {facts.disrupted_booking_ref} on {facts.disruption_date} "
                f"experienced a +{facts.delay_minutes} minute delay (Disruption ID: {facts.disruption_id}, arriving at {facts.revised_arrival_time} instead of {facts.original_arrival_time}), "
                f"and their onward journey has been automatically re-arranged:\n\n"
                f"- Rebooked Train: {facts.rebooked_provider} {facts.rebooked_service_name} "
                f"(Transport ID: {facts.rebooked_transport_id}, Booking Ref: {facts.rebooked_booking_ref})\n"
                f"- Revised Departure: {facts.rebooked_departure_time} | Revised Jaipur Arrival: {facts.rebooked_arrival_time} on {facts.disruption_date}\n"
                f"- Confirmed Hotel: {facts.hotel_name} (Booking Ref: {facts.hotel_booking_ref}, Updated Check-In: {facts.hotel_revised_checkin})\n\n"
                f"No action is needed on your part.\n\n"
                f"Warm regards,\n"
                f"Autonomous Disruption Recovery Agent"
            )

        return {
            "recipient_name": recipient_name,
            "recipient_email": recipient_email,
            "recipient": f"{recipient_name} <{recipient_email}>",
            "subject": subject,
            "message": message,
            "related_booking": related_booking,
            "related_disruption": f"{facts.disruption_id} ({facts.disruption_type})",
        }


class NotificationAgentService:
    """
    Coordinates generation, anti-hallucination validation, simulated dispatch,
    and inbox history persistence for all 6 notification categories.
    """

    def __init__(self):
        self.inbox_history: List[GeneratedNotificationRecord] = []

    def generate_single_notification(
        self,
        category: str,
        facts: StructuredRecoveryFacts,
        simulate_hallucination_test: bool = False,
        custom_draft_subject: Optional[str] = None,
        custom_draft_message: Optional[str] = None,
    ) -> GeneratedNotificationRecord:
        meta = CATEGORY_METADATA.get(category, CATEGORY_METADATA[NotificationCategory.TRAVELER_NOTIFICATION.value])
        grounded = NotificationTemplateEngine.render(category, facts)

        ungrounded_blocked_preview: Optional[str] = None
        generator_used = "deterministic_fact_grounded_template"
        status = "SENT_SIMULATED"

        if custom_draft_subject is not None or custom_draft_message is not None:
            candidate_subject = custom_draft_subject or grounded["subject"]
            candidate_message = custom_draft_message or grounded["message"]
            validation = FactGroundingValidator.validate(candidate_subject, candidate_message, facts)
            if validation.is_valid:
                final_subject = candidate_subject
                final_message = candidate_message
                generator_used = "validated_custom_ai_draft"
            else:
                validation.fallback_applied = True
                ungrounded_blocked_preview = f"Subject: {candidate_subject}\n\n{candidate_message}"
                final_subject = grounded["subject"]
                final_message = grounded["message"]
                generator_used = "hallucination_guardrail_fallback"
                status = "HALLUCINATION_BLOCKED_TEMPLATE_SENT"
        elif simulate_hallucination_test:
            # Simulate a hallucinating LLM draft that invents a fake booking ref, price, date, and policy
            hallucinated_subject = (
                f"[URGENT] Booking PNR-FAKE-99999 Refund of $450.00 under EU261 on 2026-12-31"
            )
            hallucinated_message = (
                f"Dear {facts.passenger_name},\n"
                f"Your train PNR-FAKE-99999 on 2026-12-31 at 03:45 has been refunded for $450.00 (INR 19500.00) "
                f"with a 200% refund bonus under EU261 and complimentary business class upgrade."
            )
            validation = FactGroundingValidator.validate(hallucinated_subject, hallucinated_message, facts)
            validation.fallback_applied = True
            ungrounded_blocked_preview = f"Subject: {hallucinated_subject}\n\n{hallucinated_message}"
            final_subject = grounded["subject"]
            final_message = grounded["message"]
            generator_used = "hallucination_guardrail_fallback"
            status = "HALLUCINATION_BLOCKED_TEMPLATE_SENT"
        else:
            final_subject = grounded["subject"]
            final_message = grounded["message"]
            validation = FactGroundingValidator.validate(final_subject, final_message, facts)

        record = GeneratedNotificationRecord(
            notification_id=f"MSG-{uuid.uuid4().hex[:8].upper()}",
            category=category,
            category_label=meta["label"],
            recipient_name=grounded["recipient_name"],
            recipient_email=grounded["recipient_email"],
            recipient=grounded["recipient"],
            subject=final_subject,
            message=final_message,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            related_booking=grounded["related_booking"],
            related_disruption=grounded["related_disruption"],
            template_id=meta["template_id"],
            generator_used=generator_used,
            validation=validation,
            ungrounded_draft_blocked=ungrounded_blocked_preview,
            simulated=True,
        )

        self.inbox_history.insert(0, record)
        return record

    def generate_all_notifications(
        self,
        facts: Optional[StructuredRecoveryFacts] = None,
        categories: Optional[List[str]] = None,
        simulate_hallucination_test: bool = False,
    ) -> List[GeneratedNotificationRecord]:
        resolved_facts = facts or StructuredRecoveryFacts()
        target_categories = categories or [c.value for c in NotificationCategory]
        generated: List[GeneratedNotificationRecord] = []

        # Generate in reverse so item #1 (Traveler Notification) ends up at top of inbox
        for cat in reversed(target_categories):
            rec = self.generate_single_notification(
                category=cat,
                facts=resolved_facts,
                simulate_hallucination_test=simulate_hallucination_test,
            )
            generated.insert(0, rec)

        return generated

    def ensure_seeded(self):
        if not self.inbox_history:
            self.generate_all_notifications(StructuredRecoveryFacts())

    def clear_history(self):
        self.inbox_history.clear()


notification_agent_service = NotificationAgentService()
