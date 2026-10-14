from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.modules.policies.policy_rag_service import policy_rag_service

router = APIRouter(prefix="/chat", tags=["Airline Policy RAG Chatbot"])

class ChatRequest(BaseModel):
    message: str = Field(..., description="Passenger question about policies, delays, refunds, baggage, etc.")
    session_id: Optional[str] = Field(None, description="Unique conversation session ID for multi-turn history")
    airline: Optional[str] = Field(None, description="Optional airline name filter (e.g. Air India, IndiGo)")
    journey_id: Optional[int] = Field(None, description="Optional active journey ID for context personalization")

class CitationModel(BaseModel):
    document_title: str
    publisher: str
    regulator: str
    region: str
    section: str
    page_number: int
    source_url: str
    effective_date: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[CitationModel]
    confidence: float
    journey_context: Optional[Dict[str, Any]] = None
    retrieved_chunk_count: int = 0

@router.post("", response_model=ChatResponse, summary="Ask Airline Policy & Passenger Rights Legal Assistant")
async def ask_policy_chat(request: ChatRequest):
    """
    Submits a passenger query to the Policy RAG Chatbot.
    Answers are grounded strictly in official regulatory documents (DGCA CAR Series M Part IV,
    EU261, US DOT 14 CFR 260) and airline Conditions of Carriage.
    """
    try:
        result = await policy_rag_service.answer_question(
            message=request.message,
            session_id=request.session_id,
            airline=request.airline,
            journey_id=request.journey_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy chat generation failed: {str(e)}")

@router.get("/history/{session_id}", summary="Get Multi-Turn Chat Conversation History")
def get_chat_history(session_id: str):
    """Retrieves previous dialogue turns for the given conversation session."""
    history = policy_rag_service.get_history(session_id)
    return {
        "session_id": session_id,
        "turns": history,
        "turn_count": len(history)
    }

@router.post("/clear/{session_id}", summary="Clear Conversation History")
def clear_chat_history(session_id: str):
    """Clears conversational memory for a given session."""
    policy_rag_service.clear_session(session_id)
    return {"status": "success", "message": f"Session {session_id} memory cleared"}

@router.get("/suggested-questions", summary="Get Pre-configured Suggested Policy Prompts")
def get_suggested_questions():
    """Returns curated official policy prompts with high real-world passenger relevance."""
    return {
        "suggested_questions": [
            {
                "category": "Flight Delay",
                "question": "What compensation or refreshments am I entitled to if my flight is delayed by 4 hours?",
                "jurisdiction": "DGCA CAR M Part IV / EU261"
            },
            {
                "category": "Cancellations & Refunds",
                "question": "Can I get a 100% full refund if the airline cancels my flight less than 24 hours before departure?",
                "jurisdiction": "DGCA / US DOT 14 CFR 260"
            },
            {
                "category": "Baggage Allowance",
                "question": "What is the free checked baggage and cabin baggage allowance on IndiGo vs Air India?",
                "jurisdiction": "Conditions of Carriage"
            },
            {
                "category": "Overbooking & Bumping",
                "question": "What compensation is mandated if I am involuntarily denied boarding due to an overbooked flight?",
                "jurisdiction": "DGCA / US DOT"
            },
            {
                "category": "Name Correction",
                "question": "Can I correct a typo in my name on my flight ticket without paying cancellation charges?",
                "jurisdiction": "DGCA Passenger Charter"
            }
        ]
    }

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Query text for FAISS semantic nearest-neighbor search")
    top_k: int = Field(5, description="Number of top semantic chunks to return")
    airline: Optional[str] = Field(None, description="Optional airline name filter")
    region: Optional[str] = Field(None, description="Optional jurisdiction / region filter")

@router.post("/semantic-search", summary="Pure Semantic Vector Search via FAISS")
def faiss_semantic_search(request: SemanticSearchRequest):
    """
    Executes pure semantic vector nearest-neighbor search powered by
    FAISS (Facebook AI Similarity Search - IndexFlatIP).
    """
    results = policy_rag_service.search_semantic_faiss(
        query=request.query,
        top_k=request.top_k,
        airline=request.airline,
        region=request.region
    )
    return {
        "query": request.query,
        "search_engine": "FAISS (Facebook AI Similarity Search - IndexFlatIP)",
        "results_count": len(results),
        "results": results
    }

