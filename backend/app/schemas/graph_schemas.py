from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class JourneyNodeDetail(BaseModel):
    id: str  # e.g., 'booking_1', 'loc_delhi'
    key: str
    name: str
    type: Literal["flight", "train", "bus", "hotel", "activity", "location", "airport", "station"]
    booking_id: Optional[int] = None
    provider: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

class ConnectionRiskLevel:
    SAFE = "SAFE"
    TIGHT = "TIGHT"
    IMPOSSIBLE = "IMPOSSIBLE"

class JourneyEdgeDetail(BaseModel):
    id: str
    source: str
    target: str
    edge_type: Literal["connection", "dependency", "chronological_sequence", "transfer"]
    from_booking_id: Optional[int] = None
    to_booking_id: Optional[int] = None
    buffer_minutes: int = Field(..., description="Available connection time in minutes")
    transfer_type: str = "same_city"  # same_terminal, intra_city, inter_city, impossible
    risk_level: Literal["SAFE", "TIGHT", "IMPOSSIBLE"]
    risk_reason: str
    recommended_min_buffer: int = 60
    properties: Optional[Dict[str, Any]] = None

class JourneyRiskSummary(BaseModel):
    total_connections: int
    safe_connections: int
    tight_connections: int
    impossible_connections: int
    highest_risk: Literal["SAFE", "TIGHT", "IMPOSSIBLE", "NONE"]
    critical_dependencies: List[str] = []

class JourneyGraphResponse(BaseModel):
    journey_id: int
    journey_title: str
    total_nodes: int
    total_edges: int
    nodes: List[JourneyNodeDetail]
    edges: List[JourneyEdgeDetail]
    risk_summary: JourneyRiskSummary
    is_dag: bool
    topological_sequence: List[str]
