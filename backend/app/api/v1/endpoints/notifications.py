from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Notification
from app.schemas.schemas import NotificationCreate, NotificationResponse
from app.schemas.notification_schemas import (
    NotificationCategory,
    CATEGORY_METADATA,
    StructuredRecoveryFacts,
    GenerateNotificationSuiteRequest,
    ValidateDraftRequest,
)
from app.modules.notifications.notification_agent import (
    notification_agent_service,
    FactGroundingValidator,
)

router = APIRouter(prefix="/notifications", tags=["Email & Notification Agent (Stage 10)"])


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.sent_at.desc())
        .all()
    )


@router.post("/", response_model=NotificationResponse)
def trigger_notification(
    notif_in: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = Notification(
        user_id=current_user.id,
        journey_id=notif_in.journey_id,
        channel=notif_in.channel,
        recipient=notif_in.recipient,
        subject=notif_in.subject,
        content=notif_in.content,
        simulated=True,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("/inbox")
def get_notification_inbox(
    category: Optional[str] = Query(None, description="Optional filter by notification category"),
    seed_if_empty: bool = Query(True, description="Automatically seed the 6 standard notifications if inbox is empty"),
) -> Dict[str, Any]:
    """
    Returns the Stage 10 Simulated Notification Inbox containing:
    Recipient, Subject, Message, Status, Timestamp, Related booking, Related disruption,
    and FactValidationReport for every generated message.
    """
    if seed_if_empty:
        notification_agent_service.ensure_seeded()

    records = [r.model_dump() for r in notification_agent_service.inbox_history]
    if category and category != "ALL":
        records = [r for r in records if r["category"] == category]

    total = len(notification_agent_service.inbox_history)
    grounded_count = sum(1 for r in notification_agent_service.inbox_history if r.validation.is_valid)
    blocked_hallucinations = sum(
        1 for r in notification_agent_service.inbox_history if r.validation.fallback_applied
    )

    return {
        "total_notifications": total,
        "grounded_count": grounded_count,
        "hallucinations_blocked_count": blocked_hallucinations,
        "categories": CATEGORY_METADATA,
        "default_facts": StructuredRecoveryFacts().model_dump(),
        "messages": records,
    }


@router.post("/generate-suite")
def generate_notification_suite(req: GenerateNotificationSuiteRequest) -> Dict[str, Any]:
    """
    Generates all 6 notification categories (Traveler, Hotel, Supplier, Refund, Cancellation,
    Emergency Contact) strictly grounded in `req.facts`, or tests the anti-hallucination guardrail.
    """
    generated = notification_agent_service.generate_all_notifications(
        facts=req.facts,
        categories=req.categories,
        simulate_hallucination_test=req.simulate_hallucination_test,
    )
    return {
        "generated_count": len(generated),
        "simulate_hallucination_test": req.simulate_hallucination_test,
        "generated": [g.model_dump() for g in generated],
    }


@router.post("/validate-draft")
def validate_and_send_draft(req: ValidateDraftRequest) -> Dict[str, Any]:
    """
    Validates a candidate AI draft against `StructuredRecoveryFacts`.
    If the draft invents any booking number, price, date/time, or policy rule,
    blocks the draft and dispatches the verified deterministic template instead.
    """
    validation = FactGroundingValidator.validate(req.draft_subject, req.draft_message, req.facts)
    record = notification_agent_service.generate_single_notification(
        category=req.category,
        facts=req.facts,
        custom_draft_subject=req.draft_subject,
        custom_draft_message=req.draft_message,
    )
    return {
        "validation": validation.model_dump(),
        "dispatched_record": record.model_dump(),
    }


@router.get("/templates")
def get_notification_templates() -> Dict[str, Any]:
    """Returns all 6 notification templates and canonical structured facts."""
    return {
        "categories": [c.value for c in NotificationCategory],
        "metadata": CATEGORY_METADATA,
        "default_facts": StructuredRecoveryFacts().model_dump(),
    }


@router.post("/clear")
def clear_notification_inbox() -> Dict[str, Any]:
    """Clears the Stage 10 notification history."""
    notification_agent_service.clear_history()
    return {"status": "CLEARED", "total_notifications": 0}
