"""
Stage 7: AeroAI Unified AI Agent.

Integrates the 5 core capabilities:
1. Flight Search Tool
2. Flight Status Tool
3. Weather Tool
4. Flight Delay Prediction Tool
5. Policy RAG Tool

Intelligent Routing:
- Evaluates incoming questions and context.
- Selects ONLY the tools necessary for the query.
- Never calls every tool blindly for every request.

Anti-Hallucination & Provenance:
- Never invents flight status, weather observations, or travel policies.
- Explicitly labels data as LIVE, MOCK, or PREDICTED.
- Formulates statistical uncertainty (predictions are never presented as deterministic certainty).
- Gracefully communicates missing or failed tool data.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.logger import logger
from app.modules.ai_agents.tools import tool_registry
from app.modules.ai_agents.router import intent_router, RoutingDecision
from app.modules.ai_agents.formatter import response_formatter
from app.modules.ai_agents.logger import agent_audit_logger


@dataclass
class AgentResponse:
    """Unified response object returned by AeroAI agent."""
    query: str
    answer: str
    sections: Dict[str, Any]
    selected_tools: List[str]
    tool_results: Dict[str, Any]
    tool_errors: Dict[str, str]
    audit_trace: Dict[str, Any]
    execution_duration_ms: float
    session_id: str


class AeroAIUnifiedAgent:
    """
    Unified AI Agent for AeroAI.
    Coordinates tool selection, resilient execution, response formatting, and audit logging.
    """

    def __init__(self):
        self.router = intent_router
        self.tool_registry = tool_registry
        self.formatter = response_formatter
        self.audit_logger = agent_audit_logger

    async def query(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Processes a user query by dynamically selecting and executing necessary tools.
        """
        start_time = time.perf_counter()
        clean_query = (message or "").strip()
        ctx = context or {}
        sid = session_id or ctx.get("session_id") or "default_session"

        logger.info(f"[AeroAIAgent] Query received: '{clean_query}' (session={sid})")

        # Step 1: Route and determine necessary tools
        routing: RoutingDecision = self.router.route(clean_query, ctx)
        selected_tools = routing.selected_tools
        entities = routing.entities

        tool_results: Dict[str, Any] = {}
        tool_errors: Dict[str, str] = {}
        tool_executions: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        # Step 2: Execute selected tools with individual failure isolation

        # --- A. Flight Status Tool ---
        if "flight_status" in selected_tools:
            t_start = time.perf_counter()
            tool = self.tool_registry.get_tool("flight_status")
            fn = entities.flight_number or ctx.get("flight_number")
            status_input = {"flight_number": fn, "target_date": entities.target_date}

            if not fn:
                # If no flight number was provided for a status check, note it gracefully
                tool_results["flight_status"] = {
                    "status": "no_flight_identified",
                    "message": "No flight number was identified in the query or context."
                }
                tool_executions.append({
                    "tool": "flight_status",
                    "inputs": status_input,
                    "duration_ms": 0.1,
                    "status": "skipped",
                    "reason": "No flight number provided"
                })
            else:
                try:
                    res = await tool.execute(**status_input)
                    tool_results["flight_status"] = res
                    if res.get("status") == "error":
                        err_msg = res.get("message", "Flight status error")
                        tool_errors["flight_status"] = err_msg
                        failures.append({"tool": "flight_status", "error": err_msg})
                    elif res.get("status") == "success" and res.get("flight_record"):
                        rec = res["flight_record"]
                        entities.origin = entities.origin or rec.get("origin")
                        entities.destination = entities.destination or rec.get("destination")
                        entities.carrier_code = entities.carrier_code or rec.get("carrier_code")

                    tool_executions.append({
                        "tool": "flight_status",
                        "inputs": status_input,
                        "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                        "status": res.get("status", "success")
                    })
                except Exception as e:
                    err_msg = str(e)
                    logger.error(f"[AeroAIAgent] Flight status tool failure: {err_msg}")
                    tool_errors["flight_status"] = err_msg
                    failures.append({"tool": "flight_status", "error": err_msg})
                    tool_executions.append({
                        "tool": "flight_status",
                        "inputs": status_input,
                        "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                        "status": "failed",
                        "error": err_msg
                    })

        # --- B. Weather Tool ---
        if "weather" in selected_tools:
            t_start = time.perf_counter()
            tool = self.tool_registry.get_tool("weather")
            # Select target airport for weather
            airports = entities.airports_for_weather or ([entities.origin] if entities.origin else [])
            target_airport = airports[0] if airports else (ctx.get("airport") or "DEL")

            weather_input = {"airport_code": target_airport}
            try:
                res = await tool.execute(**weather_input)
                tool_results["weather"] = res
                if res.get("status") == "error":
                    err_msg = res.get("message", "Weather lookup error")
                    tool_errors["weather"] = err_msg
                    failures.append({"tool": "weather", "error": err_msg})
                tool_executions.append({
                    "tool": "weather",
                    "inputs": weather_input,
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": res.get("status", "success")
                })
            except Exception as e:
                err_msg = str(e)
                logger.error(f"[AeroAIAgent] Weather tool failure: {err_msg}")
                tool_errors["weather"] = err_msg
                failures.append({"tool": "weather", "error": err_msg})
                tool_executions.append({
                    "tool": "weather",
                    "inputs": weather_input,
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": "failed",
                    "error": err_msg
                })

        # --- C. Delay Prediction Tool ---
        if "delay_prediction" in selected_tools:
            t_start = time.perf_counter()
            tool = self.tool_registry.get_tool("delay_prediction")
            pred_input = {
                "carrier": entities.carrier_code or ctx.get("carrier") or "AI",
                "origin": entities.origin or ctx.get("origin") or "DEL",
                "dest": entities.destination or ctx.get("destination") or "BOM",
                "flight_number": entities.flight_number,
                "target_date": entities.target_date,
                "distance_miles": ctx.get("distance_miles", 710.0)
            }
            try:
                res = await tool.execute(**pred_input)
                tool_results["delay_prediction"] = res
                if res.get("status") == "error":
                    err_msg = res.get("message", "Delay prediction error")
                    tool_errors["delay_prediction"] = err_msg
                    failures.append({"tool": "delay_prediction", "error": err_msg})
                tool_executions.append({
                    "tool": "delay_prediction",
                    "inputs": pred_input,
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": res.get("status", "success")
                })
            except Exception as e:
                err_msg = str(e)
                logger.error(f"[AeroAIAgent] Delay prediction tool failure: {err_msg}")
                tool_errors["delay_prediction"] = err_msg
                failures.append({"tool": "delay_prediction", "error": err_msg})
                tool_executions.append({
                    "tool": "delay_prediction",
                    "inputs": pred_input,
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": "failed",
                    "error": err_msg
                })

        # --- D. Policy RAG Tool ---
        if "policy_rag" in selected_tools:
            t_start = time.perf_counter()
            tool = self.tool_registry.get_tool("policy_rag")
            rag_input = {
                "query": clean_query,
                "airline": entities.airline_name or ctx.get("airline"),
                "journey_id": ctx.get("journey_id"),
                "session_id": sid
            }
            try:
                res = await tool.execute(**rag_input)
                tool_results["policy_rag"] = res
                if res.get("status") == "error":
                    err_msg = res.get("message", "Policy RAG error")
                    tool_errors["policy_rag"] = err_msg
                    failures.append({"tool": "policy_rag", "error": err_msg})
                tool_executions.append({
                    "tool": "policy_rag",
                    "inputs": {"query": clean_query, "airline": rag_input.get("airline")},
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": res.get("status", "success")
                })
            except Exception as e:
                err_msg = str(e)
                logger.error(f"[AeroAIAgent] Policy RAG tool failure: {err_msg}")
                tool_errors["policy_rag"] = err_msg
                failures.append({"tool": "policy_rag", "error": err_msg})
                tool_executions.append({
                    "tool": "policy_rag",
                    "inputs": {"query": clean_query},
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": "failed",
                    "error": err_msg
                })

        # --- E. Flight Search Tool ---
        if "flight_search" in selected_tools:
            t_start = time.perf_counter()
            tool = self.tool_registry.get_tool("flight_search")
            orig = entities.origin or ctx.get("origin") or "DEL"
            dest = entities.destination or ctx.get("destination") or "BOM"
            search_input = {
                "origin": orig,
                "destination": dest,
                "min_seats": entities.min_seats or ctx.get("min_seats", 1)
            }
            try:
                res = await tool.execute(**search_input)
                tool_results["flight_search"] = res
                if res.get("status") == "error":
                    err_msg = res.get("message", "Flight search error")
                    tool_errors["flight_search"] = err_msg
                    failures.append({"tool": "flight_search", "error": err_msg})
                tool_executions.append({
                    "tool": "flight_search",
                    "inputs": search_input,
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": res.get("status", "success")
                })
            except Exception as e:
                err_msg = str(e)
                logger.error(f"[AeroAIAgent] Flight search tool failure: {err_msg}")
                tool_errors["flight_search"] = err_msg
                failures.append({"tool": "flight_search", "error": err_msg})
                tool_executions.append({
                    "tool": "flight_search",
                    "inputs": search_input,
                    "duration_ms": round((time.perf_counter() - t_start) * 1000, 2),
                    "status": "failed",
                    "error": err_msg
                })

        # Step 3: Format structured response
        formatted = self.formatter.format_response(
            query=clean_query,
            selected_tools=selected_tools,
            tool_results=tool_results,
            tool_errors=tool_errors,
            entities=entities
        )
        answer_text = formatted["response_text"]
        sections = formatted["sections"]

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Step 4: Audit logging
        audit_trace = self.audit_logger.log_interaction(
            user_request=clean_query,
            selected_tools=selected_tools,
            tool_executions=tool_executions,
            failures=failures,
            response_summary=answer_text[:200],
            execution_duration_ms=duration_ms,
            session_id=sid
        )

        return AgentResponse(
            query=clean_query,
            answer=answer_text,
            sections=sections,
            selected_tools=selected_tools,
            tool_results=tool_results,
            tool_errors=tool_errors,
            audit_trace=audit_trace,
            execution_duration_ms=round(duration_ms, 2),
            session_id=sid
        )


# Global singleton agent
aeroai_agent = AeroAIUnifiedAgent()
