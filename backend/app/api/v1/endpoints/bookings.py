from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Booking, Journey
from app.schemas.schemas import BookingCreate, BookingResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("/", response_model=List[BookingResponse])
def get_bookings(journey_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Booking).join(Journey).filter(Journey.user_id == current_user.id)
    if journey_id:
        query = query.filter(Booking.journey_id == journey_id)
    return query.all()

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: BookingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    journey = db.query(Journey).filter(Journey.id == booking_in.journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found or unauthorized")
    
    booking = Booking(
        journey_id=booking_in.journey_id,
        reference_number=booking_in.reference_number,
        booking_type=booking_in.booking_type,
        provider_name=booking_in.provider_name,
        title=booking_in.title,
        description=booking_in.description,
        status=booking_in.status,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        origin=booking_in.origin,
        destination=booking_in.destination,
        price=booking_in.price,
        currency=booking_in.currency,
        raw_metadata=booking_in.raw_metadata
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Automatically recompute and sync journey graph relationships
    from app.modules.journeys.graph_builder import JourneyGraphEngine
    engine = JourneyGraphEngine(journey_id=journey.id)
    engine.sync_to_database(db, journey)

    return booking
