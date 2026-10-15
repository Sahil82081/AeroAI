"""
REST API Endpoints for the AeroAI Unified AI Agent (Stage 7).

Exposes:
- POST /agent/query: Full structured multi-tool agent execution.
- POST /agent/chat: Conversational interface for passenger queries.
- GET /agent/tools: Available tool catalog and descriptions.
- GET /agent/audit-logs: Recent sanitized agent execution traces.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.modules.ai_agents.unified_agent import aeroai_agent
from app.modules.ai_agents.tools import tool_registry
from app.modules.ai_agents.logger import agent_audit_logger

router = APIRouter(prefix="/agent", tags=["AeroAI Unified AI Agent (Stage 7)"])


class AgentQueryRequest(BaseModel):
    message: str = Field(..., description="Passenger query (e.g., 'Will flight AI202 be delayed?', 'Can I get a refund?')")
    session_id: Optional[str] = Field(None, description="Session ID for conversation history tracking")
    flight_number: Optional[str] = Field(None, description="Optional flight number context (e.g. AI202)")
    origin: Optional[str] = Field(None, description="Optional departure airport code (e.g. DEL)")
    destination: Optional[str] = Field(None, description="Optional arrival airport code (e.g. BOM)")
    airline: Optional[str] = Field(None, description="Optional carrier name")
    journey_id: Optional[int] = Field(None, description="Optional journey ID for personalization")
    date: Optional[str] = Field(None, description="Optional travel date (YYYY-MM-DD)")


class AgentQueryResponse(BaseModel):
    query: str
    answer: str
    sections: Dict[str, Any]
    selected_tools: List[str]
    tool_results: Dict[str, Any]
    tool_errors: Dict[str, str]
    audit_trace: Dict[str, Any]
    execution_duration_ms: float
    session_id: Optional[str] = "default_session"


@router.post("/query", response_model=AgentQueryResponse, summary="Execute Unified AI Agent Query")
async def execute_agent_query(request: AgentQueryRequest):
    """
    Submits a user query to the AeroAI Unified AI Agent.
    Dynamically routes to necessary tools (Flight Search, Flight Status, Weather,
    Flight Delay Prediction, Policy RAG) and returns clearly separated sections.
    """
    try:
        context = {
            "flight_number": request.flight_number,
            "origin": request.origin,
            "destination": request.destination,
            "airline": request.airline,
            "journey_id": request.journey_id,
            "date": request.date,
            "session_id": request.session_id
        }
        res = await aeroai_agent.query(
            message=request.message,
            context=context,
            session_id=request.session_id
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AeroAI Agent execution failed: {str(e)}")


@router.post("/chat", summary="Chat with AeroAI Unified Assistant")
async def chat_with_agent(request: AgentQueryRequest):
    """
    Lightweight chat endpoint suitable for frontend conversational interfaces.
    """
    try:
        context = {
            "flight_number": request.flight_number,
            "origin": request.origin,
            "destination": request.destination,
            "airline": request.airline,
            "journey_id": request.journey_id,
            "date": request.date,
            "session_id": request.session_id
        }
        res = await aeroai_agent.query(
            message=request.message,
            context=context,
            session_id=request.session_id
        )
        return {
            "session_id": res.session_id,
            "answer": res.answer,
            "sections": res.sections,
            "selected_tools": res.selected_tools,
            "duration_ms": res.execution_duration_ms,
            "audit_trace_id": res.audit_trace.get("trace_id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AeroAI chat failed: {str(e)}")


@router.get("/tools", summary="List Available Agent Tools")
def list_agent_tools():
    """
    Returns the metadata catalog of the 5 core tools available to the AeroAI agent.
    """
    return {
        "count": 5,
        "tools": tool_registry.list_tools()
    }


@router.get("/audit-logs", summary="Get Recent Agent Audit Logs")
def get_audit_logs(limit: int = Query(20, ge=1, le=100)):
    """
    Returns recent sanitized agent execution traces with secrets redacted.
    """
    traces = agent_audit_logger.get_recent_traces(limit=limit)
    return {
        "count": len(traces),
        "traces": traces
    }
