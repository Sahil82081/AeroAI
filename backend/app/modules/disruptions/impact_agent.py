from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from app.models.models import Booking, BookingStatus, DisruptionSeverity
from app.schemas.disruption_schemas import (
    ImpactAnalysisResult, BookingImpactDetail, UnaffectedBookingDetail, MissedConnectionDetail
)
from app.modules.journeys.location_matcher import LocationMatcher

class ImpactAnalysisAgent:
    """
    Intelligent agent that assesses downstream dependencies across the journey graph
    when a disruption (delay or cancellation) occurs on a specific booking leg.
    Categorizes affected vs. unaffected bookings, detects missed connections,
    and generates clear explanations.
    """

    @classmethod
    def analyze_impact(
        cls,
        journey_id: int,
        disrupted_booking: Booking,
        disruption_type_str: str,
        delay_minutes: int,
        all_journey_bookings: List[Booking]
    ) -> ImpactAnalysisResult:
        # Sort all bookings chronologically
        sorted_bookings = sorted(all_journey_bookings, key=lambda b: b.start_time)

        # Map disruption type
        is_cancellation = "cancellation" in disruption_type_str.lower()
        
        affected_list: List[BookingImpactDetail] = []
        unaffected_list: List[UnaffectedBookingDetail] = []
        missed_connections: List[MissedConnectionDetail] = []
        explanation_sentences: List[str] = []

        # Find position of disrupted booking in sequence
        disrupted_idx = -1
        for idx, b in enumerate(sorted_bookings):
            if b.id == disrupted_booking.id:
                disrupted_idx = idx
                break

        if disrupted_idx == -1:
            # Fallback if not found
            disrupted_idx = 0

        # Calculate revised times for the directly disrupted booking
        revised_start = disrupted_booking.start_time + timedelta(minutes=delay_minutes)
        revised_end = disrupted_booking.end_time + timedelta(minutes=delay_minutes)

        # 1. Add the trigger booking itself as directly disrupted
        direct_impact = BookingImpactDetail(
            booking_id=disrupted_booking.id,
            reference_number=disrupted_booking.reference_number,
            title=disrupted_booking.title,
            booking_type=disrupted_booking.booking_type.value,
            provider=disrupted_booking.provider_name,
            status="CANCELLED" if is_cancellation else "DELAYED",
            original_start_time=disrupted_booking.start_time,
            original_end_time=disrupted_booking.end_time,
            revised_start_time=None if is_cancellation else revised_start,
            revised_end_time=None if is_cancellation else revised_end,
            impact_nature="DIRECT_DISRUPTION",
            impact_description=f"Cancelled completely." if is_cancellation else f"Delayed by {delay_minutes} minutes ({delay_minutes // 60}h {delay_minutes % 60}m)."
        )
        affected_list.append(direct_impact)

        explanation_sentences.append(
            f"{disrupted_booking.provider_name} ({disrupted_booking.reference_number}) is {direct_impact.impact_description.lower()}"
        )

        # Upstream bookings occurring before the disruption are unaffected
        for i in range(0, disrupted_idx):
            b = sorted_bookings[i]
            unaffected_list.append(UnaffectedBookingDetail(
                booking_id=b.id,
                reference_number=b.reference_number,
                title=b.title,
                booking_type=b.booking_type.value,
                provider=b.provider_name,
                start_time=b.start_time,
                end_time=b.end_time,
                reason_unaffected="Completed prior to disrupted departure."
            ))

        # 2. Evaluate downstream cascade for all subsequent bookings
        current_arrival = revised_end
        cascade_broken = is_cancellation

        for i in range(disrupted_idx + 1, len(sorted_bookings)):
            downstream_b = sorted_bookings[i]
            prev_b = sorted_bookings[i - 1]

            # Next-day tours/activities with overnight buffer remain unaffected
            if (
                downstream_b.booking_type.value == "ACTIVITY"
                and downstream_b.start_time.date() > disrupted_booking.start_time.date()
            ):
                unaffected_list.append(UnaffectedBookingDetail(
                    booking_id=downstream_b.id,
                    reference_number=downstream_b.reference_number,
                    title=downstream_b.title,
                    booking_type=downstream_b.booking_type.value,
                    provider=downstream_b.provider_name,
                    start_time=downstream_b.start_time,
                    end_time=downstream_b.end_time,
                    reason_unaffected="Scheduled on the following day with full overnight recovery buffer."
                ))
                continue

            if cascade_broken:
                # Upstream leg was cancelled or impossible to catch
                affected_list.append(BookingImpactDetail(
                    booking_id=downstream_b.id,
                    reference_number=downstream_b.reference_number,
                    title=downstream_b.title,
                    booking_type=downstream_b.booking_type.value,
                    provider=downstream_b.provider_name,
                    status="THREATENED",
                    original_start_time=downstream_b.start_time,
                    original_end_time=downstream_b.end_time,
                    revised_start_time=None,
                    revised_end_time=None,
                    impact_nature="SCHEDULE_THREATENED",
                    impact_description=f"Traveler cannot reach departure location due to upstream disruption of {disrupted_booking.reference_number}."
                ))
                continue

            # Check transfer logistics and buffer
            transfer_type, min_buffer = LocationMatcher.evaluate_transfer_proximity(
                prev_b.destination or prev_b.origin or "",
                downstream_b.origin or downstream_b.destination or "",
                prev_b.booking_type.value,
                downstream_b.booking_type.value
            )

            # Available buffer after delay
            revised_buffer_seconds = (downstream_b.start_time - current_arrival).total_seconds()
            revised_buffer_minutes = int(revised_buffer_seconds / 60)

            if revised_buffer_minutes < 0:
                # Departure is BEFORE revised arrival -> Missed connection!
                deficit = abs(revised_buffer_minutes)
                missed_conn = MissedConnectionDetail(
                    from_booking_id=prev_b.id,
                    from_booking_ref=prev_b.reference_number,
                    to_booking_id=downstream_b.id,
                    to_booking_ref=downstream_b.reference_number,
                    scheduled_arrival=prev_b.end_time,
                    revised_arrival=current_arrival,
                    next_departure=downstream_b.start_time,
                    deficit_minutes=deficit,
                    explanation=(
                        f"{prev_b.title} revised arrival ({current_arrival.strftime('%H:%M')}) is {deficit} minutes "
                        f"after {downstream_b.title} departure ({downstream_b.start_time.strftime('%H:%M')})."
                    )
                )
                missed_connections.append(missed_conn)

                affected_list.append(BookingImpactDetail(
                    booking_id=downstream_b.id,
                    reference_number=downstream_b.reference_number,
                    title=downstream_b.title,
                    booking_type=downstream_b.booking_type.value,
                    provider=downstream_b.provider_name,
                    status="MISSED",
                    original_start_time=downstream_b.start_time,
                    original_end_time=downstream_b.end_time,
                    revised_start_time=None,
                    revised_end_time=None,
                    impact_nature="MISSED_CONNECTION",
                    impact_description=f"Missed connection: departure occurs {deficit}m before incoming arrival."
                ))
                explanation_sentences.append(
                    f"{disrupted_booking.reference_number} delay causes the traveler to miss the {downstream_b.title} "
                    f"because the revised arrival time is after the {downstream_b.booking_type.value.lower()} departure."
                )
                cascade_broken = True

            elif revised_buffer_minutes < min_buffer:
                # Buffer tighter than required for transfer
                affected_list.append(BookingImpactDetail(
                    booking_id=downstream_b.id,
                    reference_number=downstream_b.reference_number,
                    title=downstream_b.title,
                    booking_type=downstream_b.booking_type.value,
                    provider=downstream_b.provider_name,
                    status="TIGHT_RISK",
                    original_start_time=downstream_b.start_time,
                    original_end_time=downstream_b.end_time,
                    revised_start_time=downstream_b.start_time,
                    revised_end_time=downstream_b.end_time,
                    impact_nature="DOWNSTREAM_DELAY",
                    impact_description=f"Transit buffer reduced to {revised_buffer_minutes}m (below {min_buffer}m minimum required)."
                ))
                explanation_sentences.append(
                    f"{downstream_b.title} connection is at severe risk with only {revised_buffer_minutes}m buffer remaining."
                )

            else:
                # Safe buffer remained; downstream booking is unaffected
                unaffected_list.append(UnaffectedBookingDetail(
                    booking_id=downstream_b.id,
                    reference_number=downstream_b.reference_number,
                    title=downstream_b.title,
                    booking_type=downstream_b.booking_type.value,
                    provider=downstream_b.provider_name,
                    start_time=downstream_b.start_time,
                    end_time=downstream_b.end_time,
                    reason_unaffected=f"Sufficient connection buffer ({revised_buffer_minutes}m) preserved despite upstream delay."
                ))

        # Calculate overall severity
        if is_cancellation or len(missed_connections) > 0:
            severity = "CRITICAL"
        elif any(a.impact_nature == "DOWNSTREAM_DELAY" for a in affected_list):
            severity = "HIGH"
        elif delay_minutes > 60:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        final_reasoning = " ".join(explanation_sentences)

        return ImpactAnalysisResult(
            disruption_id=0,
            journey_id=journey_id,
            trigger_booking_id=disrupted_booking.id,
            trigger_booking_ref=disrupted_booking.reference_number,
            disruption_type=disruption_type_str,
            delay_minutes=delay_minutes,
            severity=severity,
            affected_bookings=affected_list,
            unaffected_bookings=unaffected_list,
            missed_connections=missed_connections,
            reasoning=final_reasoning,
            explanation=final_reasoning
        )
