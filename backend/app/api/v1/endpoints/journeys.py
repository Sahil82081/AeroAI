from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Journey, JourneyNode, JourneyEdge, Booking
from app.schemas.schemas import JourneyCreate, JourneyResponse, JourneyNodeBase, JourneyEdgeBase
from app.schemas.graph_schemas import (
    JourneyGraphResponse, JourneyNodeDetail, JourneyEdgeDetail, JourneyRiskSummary
)
from app.modules.journeys.graph_builder import JourneyGraphEngine

router = APIRouter(prefix="/journeys", tags=["Journeys"])

@router.get("/", response_model=List[JourneyResponse])
def get_journeys(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Journey).filter(Journey.user_id == current_user.id).all()

@router.post("/", response_model=JourneyResponse)
def create_journey(journey_in: JourneyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    journey = Journey(
        user_id=current_user.id,
        title=journey_in.title,
        description=journey_in.description,
        start_date=journey_in.start_date,
        end_date=journey_in.end_date,
        status=journey_in.status
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)
    return journey

@router.get("/{journey_id}", response_model=JourneyResponse)
def get_journey(journey_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey

@router.get("/{journey_id}/graph", response_model=JourneyGraphResponse)
def get_journey_graph(
    journey_id: int,
    sync_db: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes NetworkX Directed Acyclic Graph for the journey, calculates
    time gaps between bookings, analyzes connection risks, and syncs graph nodes/edges to the database.
    """
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    engine = JourneyGraphEngine(journey_id=journey.id)
    if sync_db:
        return engine.sync_to_database(db, journey)
    else:
        resp = engine.build_from_bookings(journey.bookings)
        resp.journey_title = journey.title
        return resp

@router.get("/{journey_id}/nodes", response_model=List[JourneyNodeDetail])
def get_journey_nodes(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns all graph nodes (flights, trains, hotels, activities, locations)."""
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    engine = JourneyGraphEngine(journey_id=journey.id)
    graph_resp = engine.build_from_bookings(journey.bookings)
    return graph_resp.nodes

@router.get("/{journey_id}/dependencies", response_model=List[JourneyEdgeDetail])
def get_journey_dependencies(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns all graph edges representing sequential connections and downstream dependencies."""
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    engine = JourneyGraphEngine(journey_id=journey.id)
    graph_resp = engine.build_from_bookings(journey.bookings)
    return graph_resp.edges

@router.get("/{journey_id}/risks", response_model=JourneyRiskSummary)
def get_journey_risks(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns connection risk summary (safe vs tight vs impossible connections)."""
    journey = db.query(Journey).filter(Journey.id == journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    engine = JourneyGraphEngine(journey_id=journey.id)
    graph_resp = engine.build_from_bookings(journey.bookings)
    return graph_resp.risk_summary
