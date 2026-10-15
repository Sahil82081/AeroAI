"""
Test Suite for Stage 7: AeroAI Unified AI Agent.

Tests:
1. Simple prediction question ("Will flight AI202 be delayed?") -> selective tool execution
2. Policy question ("If my flight is delayed by 4 hours, can I get a refund?") -> Policy RAG only
3. Combined question ("My flight tomorrow AI202 has high delay risk. What should I do?") -> all relevant tools
4. Tool failure -> isolated failure, graceful explanation of unavailable data
5. Missing flight -> non-existent flight reports not found, no invented status
6. Missing weather -> graceful fallback without fabricated weather observations
7. Insufficient RAG evidence -> out-of-scope query cleanly refused without hallucination
8. Flight search tool -> queries flight inventory between cities
9. Audit logging -> scrubs sensitive secrets, API keys, and passwords
10. API endpoints -> /api/v1/agent/query, /api/v1/agent/chat, /api/v1/agent/tools, /api/v1/agent/audit-logs
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.ai_agents.unified_agent import aeroai_agent, AgentResponse
from app.modules.ai_agents.router import intent_router
from app.modules.ai_agents.tools import tool_registry
from app.modules.ai_agents.logger import scrub_sensitive_text, agent_audit_logger

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Simple Prediction Question
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_simple_prediction_question():
    """
    Prompt: 'Will my flight be delayed?'
    Required behavior:
    - Selects: Flight Status + Weather + Delay Prediction
    - Does NOT call: Policy RAG or Flight Search
    - Clearly reports delay probability and non-causal SHAP model factors
    """
    query = "Will flight AI202 be delayed?"
    response: AgentResponse = await aeroai_agent.query(query)

    assert "delay_prediction" in response.selected_tools
    assert "flight_status" in response.selected_tools
    assert "weather" in response.selected_tools
    assert "policy_rag" not in response.selected_tools
    assert "flight_search" not in response.selected_tools

    # Verify separated sections
    assert "ml_prediction" in response.sections
    pred = response.sections["ml_prediction"]
    assert "delay_probability" in pred
    assert pred["data_source"] == "PREDICTED"
    assert "explanation" in pred

    # Verify non-causal explanation wording
    assert "These features contributed most to the model's prediction" in response.answer
    assert "Delay probability:" in response.answer
    assert "Current flight status:" in response.answer
    assert "Weather:" in response.answer


# ---------------------------------------------------------------------------
# 2. Policy Question
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_policy_question():
    """
    Prompt: 'If my flight is delayed by 4 hours, can I get a refund?'
    Required behavior:
    - Selects: Policy RAG ONLY
    - Does NOT call: Flight Status, Weather, or Delay Prediction
    - Grounded citations provided from authoritative documents
    """
    query = "If my flight is delayed by 4 hours, can I get a refund under DGCA rules?"
    response: AgentResponse = await aeroai_agent.query(query)

    assert response.selected_tools == ["policy_rag"]
    assert "policy_information" in response.sections
    policy_sec = response.sections["policy_information"]
    assert len(policy_sec["citations"]) > 0
    assert "Relevant policy:" in response.answer
    assert "Delay probability:" not in response.answer


# ---------------------------------------------------------------------------
# 3. Combined Question
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_combined_question():
    """
    Prompt: 'My flight tomorrow has a high delay risk. What should I do?'
    Required behavior:
    - Selects: Flight Status + Weather + Delay Prediction + Policy RAG
    - Output clearly separates all sections:
      Flight information, Weather, ML prediction, Model explanation, Policy information, Recommendation
    """
    query = "My flight AI202 tomorrow has a high delay risk. What should I do and what are my rights?"
    response: AgentResponse = await aeroai_agent.query(query)

    for tool_name in ["flight_status", "weather", "delay_prediction", "policy_rag"]:
        assert tool_name in response.selected_tools

    # Verify all separated text sections exist in the formatted answer
    assert "Delay probability:" in response.answer
    assert "Model factors:" in response.answer
    assert "Current flight status:" in response.answer
    assert "Weather:" in response.answer
    assert "Relevant policy:" in response.answer
    assert "Recommendation:" in response.answer

    # Verify all structured sections exist
    assert "ml_prediction" in response.sections
    assert "flight_status" in response.sections
    assert "weather" in response.sections
    assert "policy_information" in response.sections
    assert "recommendation" in response.sections


# ---------------------------------------------------------------------------
# 4. Tool Failure Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_tool_failure_handling():
    """
    If a tool fails (e.g. simulated network timeout), the agent must:
    - Gracefully isolate the failure
    - Explain in the response what information is unavailable
    - Continue delivering the remaining tool outputs without crashing
    """
    # Mock flight_status tool to throw an exception
    with patch("app.modules.ai_agents.tools.flight_service.get_flight_status", side_effect=RuntimeError("Aviation radar connection timed out")):
        response: AgentResponse = await aeroai_agent.query("Will flight AI202 be delayed?")

        assert "flight_status" in response.tool_errors
        assert "temporarily unavailable" in response.answer
        # Remaining tools must succeed
        assert "delay_prediction" in response.tool_results
        assert response.sections["ml_prediction"]["data_source"] == "PREDICTED"
        assert response.audit_trace["failure_count"] >= 1


# ---------------------------------------------------------------------------
# 5. Missing Flight Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_flight_handling():
    """
    Querying a non-existent flight:
    - Must NOT invent flight status or coordinates
    - Explains that the flight was not found in operational schedules or radar
    """
    response: AgentResponse = await aeroai_agent.query("What is the status of flight ZZ999?")

    assert "flight_status" in response.selected_tools
    status_sec = response.sections["flight_status"]
    assert status_sec["status"] == "not_found"
    assert "was not found" in response.answer
    # Does not fabricate coordinates
    assert "live_coordinates" not in status_sec


# ---------------------------------------------------------------------------
# 6. Missing Weather Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_weather_handling():
    """
    When weather observation is missing or airport is unknown:
    - Does NOT invent weather observations
    - Explains that weather observation is unavailable
    - Delay prediction gracefully proceeds with robust imputation
    """
    with patch("app.modules.ai_agents.tools.weather_service.get_weather", return_value=None):
        response: AgentResponse = await aeroai_agent.query("Will flight AI202 be delayed?", context={"airport": "UNKNOWN"})

        assert "weather" in response.sections
        assert response.sections["weather"]["status"] == "unavailable"
        assert "Weather observation" in response.answer
        assert "currently unavailable" in response.answer


# ---------------------------------------------------------------------------
# 7. Insufficient RAG Evidence Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_insufficient_rag_evidence():
    """
    Out-of-scope query:
    - Policy RAG refuses without hallucinating
    - Agent clearly communicates insufficient evidence
    """
    query = "What is the policy for transporting radioactive plutonium and enriched uranium in cabin baggage?"
    response: AgentResponse = await aeroai_agent.query(query)

    assert "policy_rag" in response.selected_tools
    policy_sec = response.sections.get("policy_information", {})
    assert policy_sec.get("sufficient_evidence") is False
    assert "sufficient evidence" in response.answer.lower()


# ---------------------------------------------------------------------------
# 8. Flight Search Tool Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_flight_search_tool():
    """
    Querying alternative flights:
    - Selects flight_search tool
    - Returns available options with seat inventory and provenance
    """
    query = "Find alternative flights from DEL to BOM"
    response: AgentResponse = await aeroai_agent.query(query)

    assert "flight_search" in response.selected_tools
    assert "flight_search" in response.sections
    search_data = response.sections["flight_search"]
    assert search_data["count"] > 0
    assert "flights" in search_data
    assert search_data["flights"][0]["data_source"] in ["LIVE", "MOCK"]


# ---------------------------------------------------------------------------
# 9. Audit Logging & Secret Scrubbing
# ---------------------------------------------------------------------------
def test_audit_logging_scrubs_secrets():
    """
    Verifies that secrets (API keys, tokens, passwords) are scrubbed from logs.
    """
    sensitive_text = "Check flight AI202 with api_key=AIzaSyB1234567890abcdef and token=secret_jwt_token_xyz"
    scrubbed = scrub_sensitive_text(sensitive_text)
    assert "AIzaSyB1234567890abcdef" not in scrubbed
    assert "secret_jwt_token_xyz" not in scrubbed
    assert "[REDACTED]" in scrubbed

    # Test dict scrubbing
    sensitive_dict = {
        "user": "traveler",
        "password": "supersecretpassword",
        "api_key": "my-secret-key-123",
        "query": "Is flight AI202 on time?"
    }
    scrubbed_dict = scrub_sensitive_text(sensitive_dict)
    assert scrubbed_dict["password"] == "[REDACTED]"
    assert scrubbed_dict["api_key"] == "[REDACTED]"
    assert scrubbed_dict["user"] == "traveler"


# ---------------------------------------------------------------------------
# 10. REST API Endpoints
# ---------------------------------------------------------------------------
def test_api_agent_query_endpoint():
    """Tests POST /api/v1/agent/query endpoint."""
    resp = client.post("/api/v1/agent/query", json={
        "message": "Will flight AI202 be delayed?",
        "flight_number": "AI202",
        "origin": "DEL",
        "destination": "BOM"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "answer" in data
    assert "sections" in data
    assert "selected_tools" in data
    assert "ml_prediction" in data["sections"]
    assert data["execution_duration_ms"] > 0


def test_api_agent_chat_endpoint():
    """Tests POST /api/v1/agent/chat conversational endpoint."""
    resp = client.post("/api/v1/agent/chat", json={
        "message": "If my flight is cancelled, can I get a full refund?",
        "session_id": "test_session_123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "test_session_123"
    assert "answer" in data
    assert "selected_tools" in data
    assert "policy_rag" in data["selected_tools"]


def test_api_agent_tools_catalog_endpoint():
    """Tests GET /api/v1/agent/tools endpoint."""
    resp = client.get("/api/v1/agent/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 5
    tool_names = [t["name"] for t in data["tools"]]
    assert "flight_search" in tool_names
    assert "flight_status" in tool_names
    assert "weather" in tool_names
    assert "delay_prediction" in tool_names
    assert "policy_rag" in tool_names


def test_api_agent_audit_logs_endpoint():
    """Tests GET /api/v1/agent/audit-logs endpoint."""
    resp = client.get("/api/v1/agent/audit-logs?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "traces" in data
    assert isinstance(data["traces"], list)
