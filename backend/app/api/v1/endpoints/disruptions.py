from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Disruption, Journey
from app.schemas.schemas import DisruptionCreate, DisruptionResponse
from app.schemas.disruption_schemas import DisruptionSimulationRequest, ImpactAnalysisResult

router = APIRouter(prefix="/disruptions", tags=["Disruptions"])

@router.get("/", response_model=List[DisruptionResponse])
def get_disruptions(journey_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Disruption).join(Journey).filter(Journey.user_id == current_user.id)
    if journey_id:
        query = query.filter(Disruption.journey_id == journey_id)
    return query.all()

@router.post("/", response_model=DisruptionResponse, status_code=status.HTTP_201_CREATED)
def trigger_disruption(disruption_in: DisruptionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    journey = db.query(Journey).filter(Journey.id == disruption_in.journey_id, Journey.user_id == current_user.id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found or unauthorized")
    
    disruption = Disruption(
        journey_id=disruption_in.journey_id,
        booking_id=disruption_in.booking_id,
        disruption_type=disruption_in.disruption_type,
        severity=disruption_in.severity,
        status=disruption_in.status,
        title=disruption_in.title,
        description=disruption_in.description,
        delay_minutes=disruption_in.delay_minutes,
        affected_nodes=disruption_in.affected_nodes,
        simulated=True
    )
    db.add(disruption)
    db.commit()
    db.refresh(disruption)
    return disruption

@router.post("/simulate", response_model=ImpactAnalysisResult, status_code=status.HTTP_201_CREATED)
def simulate_disruption(
    request: DisruptionSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers a simulated disruption (delay, cancellation, strike, weather):
    1. Updates the booking.
    2. Publishes a disruption event.
    3. Recalculates the journey graph.
    4. Identifies downstream dependencies.
    5. Returns structured affected vs. unaffected bookings, missed connections, and AI reasoning.
    """
    try:
        from app.modules.disruptions.disruption_engine import DisruptionSimulatorEngine
        return DisruptionSimulatorEngine.simulate_disruption(db=db, request=request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@router.get("/events")
def get_disruption_events(current_user: User = Depends(get_current_user)):
    """Returns real-time published disruption events log."""
    from app.modules.events.event_bus import event_bus
    return event_bus.published_events
