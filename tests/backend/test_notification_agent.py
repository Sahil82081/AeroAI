"""
Stage 10 Tests: Email and Notification Agent with Strict Fact-Grounding & Anti-Hallucination Validation.
Covers:
1. Generation of all 6 communication types:
   - Traveler notification (`traveler_notification`)
   - Hotel notification (`hotel_notification`)
   - Supplier communication (`supplier_communication`)
   - Refund request (`refund_request`)
   - Cancellation request (`cancellation_request`)
   - Emergency contact notification (`emergency_contact_notification`)
2. Notification Inbox fields: Recipient, Subject, Message, Status, Timestamp, Related booking, Related disruption
3. Strict fact-grounding verification (zero invented booking refs, prices, dates/times, or policy rules)
4. Anti-Hallucination Guardrail blocking invented booking numbers, prices, dates, and policy claims and applying fallback template
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def setup_function():
    client.post("/api/v1/notifications/clear")


def test_generate_all_six_notification_types_and_inbox_fields():
    """
    Verifies that the Notification Agent generates all 6 required communication types
    from structured recovery data and populates all required inbox fields with 100% grounded facts.
    """
    res = client.post(
        "/api/v1/notifications/generate-suite",
        json={"simulate_hallucination_test": False},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["generated_count"] == 6

    categories = [m["category"] for m in data["generated"]]
    assert categories == [
        "traveler_notification",
        "hotel_notification",
        "supplier_communication",
        "refund_request",
        "cancellation_request",
        "emergency_contact_notification",
    ]

    # Verify required Notification Inbox fields on every record
    for msg in data["generated"]:
        assert msg["recipient"]
        assert msg["subject"]
        assert msg["message"]
        assert msg["status"] == "SENT_SIMULATED"
        assert "T" in msg["timestamp"]
        assert msg["related_booking"]
        assert msg["related_disruption"]
        assert msg["validation"]["is_valid"] is True
        assert msg["validation"]["hallucinations_detected"] == []
        assert msg["validation"]["fallback_applied"] is False

    # Check GET /api/v1/notifications/inbox
    inbox_res = client.get("/api/v1/notifications/inbox")
    assert inbox_res.status_code == 200
    inbox_data = inbox_res.json()
    assert inbox_data["total_notifications"] == 6
    assert inbox_data["grounded_count"] == 6
    assert inbox_data["hallucinations_blocked_count"] == 0


def test_anti_hallucination_guardrail_blocks_invented_facts():
    """
    Verifies that if an AI draft invents a booking reference, price, date/time, or policy rule,
    FactGroundingValidator detects each violation, blocks the ungrounded draft, and substitutes
    the verified deterministic template.
    """
    draft_res = client.post(
        "/api/v1/notifications/validate-draft",
        json={
            "category": "refund_request",
            "draft_subject": "Refund Request for PNR-INVENTED-777 ($350.00)",
            "draft_message": (
                "Please refund booking PNR-INVENTED-777 for flight on 2026-12-25 at 04:15. "
                "The ticket cost INR 9999.00 ($350.00) and qualifies for a 200% refund under EU261."
            ),
        },
    )
    assert draft_res.status_code == 200
    result = draft_res.json()

    val = result["validation"]
    assert val["is_valid"] is False
    violations = " | ".join(val["hallucinations_detected"])
    assert "PNR-INVENTED-777" in violations
    assert "INR 9999.00" in violations
    assert "$350.00" in violations
    assert "2026-12-25" in violations
    assert "04:15" in violations
    assert "eu261" in violations.lower()

    dispatched = result["dispatched_record"]
    assert dispatched["status"] == "HALLUCINATION_BLOCKED_TEMPLATE_SENT"
    assert dispatched["validation"]["fallback_applied"] is True
    assert dispatched["ungrounded_draft_blocked"] is not None

    # Dispatched message must contain ONLY the grounded booking ref (12015-SHT) and grounded refund (INR 600.00)
    assert "12015-SHT" in dispatched["message"]
    assert "INR 600.00" in dispatched["message"]
    assert "PNR-INVENTED-777" not in dispatched["message"]
    assert "9999.00" not in dispatched["message"]


def test_simulate_hallucination_suite_endpoint():
    """
    Verifies the `simulate_hallucination_test=True` mode on `/api/v1/notifications/generate-suite`
    and filtering by category on `/api/v1/notifications/inbox`.
    """
    res = client.post(
        "/api/v1/notifications/generate-suite",
        json={
            "categories": ["traveler_notification", "hotel_notification"],
            "simulate_hallucination_test": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["generated_count"] == 2
    for rec in data["generated"]:
        assert rec["status"] == "HALLUCINATION_BLOCKED_TEMPLATE_SENT"
        assert rec["validation"]["fallback_applied"] is True
        assert len(rec["validation"]["hallucinations_detected"]) >= 4

    # Filter inbox by category
    filtered = client.get("/api/v1/notifications/inbox?category=hotel_notification")
    assert filtered.status_code == 200
    assert len(filtered.json()["messages"]) == 1
    assert filtered.json()["messages"][0]["category"] == "hotel_notification"
