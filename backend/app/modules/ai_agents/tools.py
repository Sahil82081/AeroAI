"""
Available Tools for the AeroAI Unified AI Agent.

Provides structured execution interfaces for:
1. Flight Search Tool (Alternative flights & seat inventory)
2. Flight Status Tool (Operational status, delay minutes, live/mock telemetry)
3. Weather Tool (Surface weather observations at origin/destination airports)
4. Flight Delay Prediction Tool (Stage 4 Random Forest inference + SHAP explainability)
5. Policy RAG Tool (Stage 5 Authoritative regulatory & carrier policy Q&A)

Strict Data Provenance Contract:
- Returned data is strictly tagged as LIVE, MOCK, or PREDICTED.
- Missing data is explicitly communicated without hallucination.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

from app.modules.flights.service import flight_service
from app.modules.flights.interfaces import FlightStatusRecord, FlightInventoryItem
from app.modules.weather.service import weather_service
from app.modules.weather.interfaces import WeatherObservation
from app.ml.predictor import delay_predictor
from app.modules.policies.policy_rag_service import policy_rag_service

logger = logging.getLogger("autonomous_recovery")


class BaseAgentTool(ABC):
    """Abstract base class for all AeroAI agent tools."""

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Executes the tool and returns a structured result dictionary."""
        pass


class FlightSearchTool(BaseAgentTool):
    """
    Tool 1: Flight Search Tool.
    Searches alternative flights and available seat inventory between origin and destination.
    """

    name = "flight_search"
    description = (
        "Search alternative flights and seat inventory between an origin airport code (e.g. DEL) "
        "and destination airport code (e.g. BOM). Returns flight numbers, departure/arrival times, "
        "available seats, and data provenance (LIVE or MOCK)."
    )

    async def execute(
        self,
        origin: str,
        destination: str,
        min_seats: int = 1,
        earliest_time: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not origin or not destination:
            return {
                "status": "error",
                "message": "Both origin and destination airport codes are required for flight search.",
                "flights": [],
                "count": 0
            }

        clean_orig = origin.strip().upper()
        clean_dest = destination.strip().upper()

        try:
            results: List[FlightInventoryItem] = await flight_service.search_flights(
                origin=clean_orig,
                destination=clean_dest,
                earliest_time=earliest_time,
                min_seats=min_seats
            )
            return {
                "status": "success",
                "origin": clean_orig,
                "destination": clean_dest,
                "count": len(results),
                "flights": [item.model_dump() for item in results]
            }
        except Exception as e:
            logger.error(f"[FlightSearchTool] Execution failed: {e}")
            return {
                "status": "error",
                "message": f"Flight search failed: {str(e)}",
                "flights": [],
                "count": 0
            }


class FlightStatusTool(BaseAgentTool):
    """
    Tool 2: Flight Status Tool.
    Retrieves operational status, delays, gate/terminal, and live ADS-B coordinates.
    """

    name = "flight_status"
    description = (
        "Lookup operational status, current delay in minutes, departure/arrival times, "
        "and live telemetry coordinates for a flight number (e.g. AI202, 6E205, BA142, DL450). "
        "Labels information strictly as LIVE or MOCK."
    )

    async def execute(
        self,
        flight_number: str,
        target_date: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not flight_number:
            return {
                "status": "error",
                "message": "Flight number is required for status lookup.",
                "flight_record": None
            }

        clean_fn = flight_number.strip().upper()
        try:
            record: Optional[FlightStatusRecord] = await flight_service.get_flight_status(
                clean_fn, target_date=target_date
            )
            if not record:
                return {
                    "status": "not_found",
                    "flight_number": clean_fn,
                    "message": f"Flight {clean_fn} was not found in operational schedules or live radar.",
                    "flight_record": None
                }

            return {
                "status": "success",
                "flight_number": clean_fn,
                "flight_record": record.model_dump(),
                "data_source": record.data_source,
                "is_fallback": record.is_fallback
            }
        except Exception as e:
            logger.error(f"[FlightStatusTool] Execution failed for {clean_fn}: {e}")
            return {
                "status": "error",
                "flight_number": clean_fn,
                "message": f"Flight status lookup failed: {str(e)}",
                "flight_record": None
            }


class WeatherTool(BaseAgentTool):
    """
    Tool 3: Weather Tool.
    Retrieves surface weather observations (temperature, precipitation, wind speed, visibility).
    """

    name = "weather"
    description = (
        "Retrieve surface weather observations (temperature, precipitation, wind speed, visibility, "
        "condition) for an airport IATA code (e.g. DEL, BOM, JFK). Labels data as LIVE, HISTORICAL, or MOCK."
    )

    async def execute(
        self,
        airport_code: str,
        target_time: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not airport_code:
            return {
                "status": "error",
                "message": "Airport code is required for weather lookup.",
                "weather": None
            }

        clean_code = airport_code.strip().upper()
        try:
            obs: Optional[WeatherObservation] = weather_service.get_weather(
                clean_code, target_time=target_time
            )
            if not obs:
                return {
                    "status": "unavailable",
                    "airport": clean_code,
                    "message": f"Weather observations for airport {clean_code} are currently unavailable.",
                    "weather": None
                }

            temp_c = round((obs.temp_f - 32) * 5 / 9, 1)
            wind_mps = round(obs.wind_speed_mph * 0.44704, 1)
            vis_m = int(round(obs.visib_miles * 1609.34, 0))
            precip_mm = round(obs.precip_in * 25.4, 1)
            data_src = "LIVE" if "LIVE" in obs.source.upper() else ("MOCK" if obs.is_fallback or "MOCK" in obs.source.upper() else "HISTORICAL")

            return {
                "status": "success",
                "airport": clean_code,
                "weather": {
                    "airport_code": obs.airport_code,
                    "temperature_c": temp_c,
                    "wind_speed_mps": wind_mps,
                    "visibility_m": vis_m,
                    "condition": obs.condition,
                    "precipitation_mm": precip_mm,
                    "timestamp": obs.timestamp.isoformat() if hasattr(obs.timestamp, "isoformat") else str(obs.timestamp),
                    "data_source": data_src,
                    "is_fallback": obs.is_fallback
                }
            }
        except Exception as e:
            logger.error(f"[WeatherTool] Execution failed for {clean_code}: {e}")
            return {
                "status": "error",
                "airport": clean_code,
                "message": f"Weather lookup failed: {str(e)}",
                "weather": None
            }


class FlightDelayPredictionTool(BaseAgentTool):
    """
    Tool 4: Flight Delay Prediction Tool.
    Runs Stage 4 Machine Learning Random Forest classifier + SHAP explainability.
    """

    name = "delay_prediction"
    description = (
        "Predict flight delay probability and binary delay classification (>=15 min delay) "
        "using Stage 4 Random Forest model trained on U.S. DOT BTS + weather intelligence, "
        "with SHAP feature attribution. Returned information is labeled as PREDICTED."
    )

    async def execute(
        self,
        carrier: Optional[str] = "AI",
        origin: Optional[str] = "DEL",
        dest: Optional[str] = "BOM",
        flight_number: Optional[str] = None,
        dep_time: Optional[str] = None,
        target_date: Optional[str] = None,
        distance_miles: Optional[float] = 710.0,
        **kwargs
    ) -> Dict[str, Any]:
        try:
            # If flight_number is supplied without carrier/origin/dest, attempt to resolve via status tool
            clean_fn = flight_number.strip().upper() if flight_number else None
            resolved_carrier = carrier or "AI"
            resolved_origin = origin or "DEL"
            resolved_dest = dest or "BOM"

            if clean_fn:
                try:
                    status_rec = await flight_service.get_flight_status(clean_fn, target_date=target_date)
                    if status_rec:
                        resolved_carrier = status_rec.carrier_code or resolved_carrier
                        resolved_origin = status_rec.origin or resolved_origin
                        resolved_dest = status_rec.destination or resolved_dest
                except Exception:
                    pass

            pred_res = delay_predictor.predict(
                carrier=resolved_carrier,
                origin=resolved_origin,
                dest=resolved_dest,
                scheduled_departure=dep_time or datetime.now(timezone.utc).isoformat(),
                distance=distance_miles or 710.0
            )
            return {
                "status": "success",
                "delay_probability": pred_res.get("delay_probability", 0.25),
                "predicted_class": pred_res.get("predicted_class", "On Time"),
                "prediction": pred_res.get("prediction", "Likely On Time"),
                "explanation": pred_res.get("explanation", []),
                "explanation_summary": pred_res.get("explanation_summary", ""),
                "disclaimer": pred_res.get("disclaimer", ""),
                "flight_reference": pred_res.get("flight_reference", {}),
                "weather_intelligence": pred_res.get("weather_intelligence", {}),
                "data_source": "PREDICTED",
                "model_name": pred_res.get("provenance", {}).get("model_name", "Random Forest Classifier")
            }
        except Exception as e:
            logger.error(f"[FlightDelayPredictionTool] Prediction failed: {e}")
            return {
                "status": "error",
                "message": f"Delay prediction calculation failed: {str(e)}",
                "data_source": "PREDICTED"
            }


class PolicyRAGTool(BaseAgentTool):
    """
    Tool 5: Policy RAG Tool.
    Queries authoritative regulatory documents (DGCA, EU261, US DOT) and carrier conditions of carriage.
    """

    name = "policy_rag"
    description = (
        "Answer passenger rights, cancellation compensation, delay refreshments, refund eligibility, "
        "and baggage liability questions using grounded retrieval from DGCA CAR Series M Part IV, "
        "EU Regulation 261/2004, US DOT 14 CFR 260, and airline conditions of carriage."
    )

    async def execute(
        self,
        query: str,
        airline: Optional[str] = None,
        journey_id: Optional[int] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        if not query:
            return {
                "status": "error",
                "message": "Policy query text is required.",
                "answer": "",
                "citations": []
            }

        try:
            rag_res = await policy_rag_service.answer_question(
                message=query,
                session_id=session_id,
                airline=airline,
                journey_id=journey_id
            )
            return {
                "status": "success",
                "answer": rag_res.get("answer", ""),
                "citations": rag_res.get("citations", []),
                "sufficient_evidence": rag_res.get("sufficient_evidence", True),
                "confidence": rag_res.get("confidence", 0.0),
                "retrieved_chunk_count": rag_res.get("retrieved_chunk_count", 0),
                "data_source": "AUTHORITATIVE_REGULATORY_POLICY"
            }
        except Exception as e:
            logger.error(f"[PolicyRAGTool] Execution failed for query '{query}': {e}")
            return {
                "status": "error",
                "message": f"Policy RAG retrieval failed: {str(e)}",
                "answer": "The policy knowledge base is temporarily unavailable.",
                "citations": [],
                "sufficient_evidence": False
            }


class AgentToolRegistry:
    """Registry managing instantiated agent tools."""

    def __init__(self):
        self.tools: Dict[str, BaseAgentTool] = {
            "flight_search": FlightSearchTool(),
            "flight_status": FlightStatusTool(),
            "weather": WeatherTool(),
            "delay_prediction": FlightDelayPredictionTool(),
            "policy_rag": PolicyRAGTool(),
        }

    def get_tool(self, name: str) -> Optional[BaseAgentTool]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": name, "description": tool.description}
            for name, tool in self.tools.items()
        ]


# Singleton tool registry
tool_registry = AgentToolRegistry()
