from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, IngestedEmail
from app.schemas.ingestion_schemas import (
    EmailIngestRequest, EmailIngestResponse, SampleEmailItem
)
from app.modules.ingestion.ingestion_service import EmailIngestionService
from app.datasets.sample_emails import SAMPLE_EMAILS

router = APIRouter(prefix="/ingestion", tags=["Email Ingestion & Parsing"])

@router.get("/samples", response_model=List[SampleEmailItem])
def get_sample_emails():
    """Retrieve pre-built dataset of realistic travel emails (flights, trains, hotels, imperfect forwards)."""
    return SAMPLE_EMAILS

@router.get("/inbox", response_model=List[EmailIngestResponse])
def get_inbox_emails(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all simulated inbox emails for the current user."""
    query = db.query(IngestedEmail).filter(IngestedEmail.user_id == current_user.id)
    if status:
        query = query.filter(IngestedEmail.parsing_status == status)
    return query.order_by(IngestedEmail.received_at.desc()).all()

@router.get("/inbox/{email_id}", response_model=EmailIngestResponse)
def get_email_detail(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single ingested email by ID."""
    email = db.query(IngestedEmail).filter(
        IngestedEmail.id == email_id,
        IngestedEmail.user_id == current_user.id
    ).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email record not found")
    return email

@router.post("/forward", response_model=EmailIngestResponse, status_code=status.HTTP_201_CREATED)
async def forward_booking_email(
    request: EmailIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a forwarded booking confirmation email, classify, extract structured
    fields, validate, check for duplicates, and persist as a Booking.
    """
    ingested_email = await EmailIngestionService.ingest_email(
        db=db,
        user=current_user,
        request=request
    )
    return ingested_email
