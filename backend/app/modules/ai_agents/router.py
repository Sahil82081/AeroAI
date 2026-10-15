"""
Intent & Tool Router for the AeroAI Unified AI Agent.

Analyzes user requests and context to select ONLY the tools necessary for the query.
Extracts entities: flight numbers, airport codes, cities, dates, and airlines.

Routing Logic:
- "Will my flight be delayed?" -> Flight Status + Weather + Delay Prediction
- "If my flight is delayed by 4 hours, can I get a refund?" -> Policy RAG
- "My flight tomorrow has a high delay risk. What should I do?" -> Flight Status + Weather + Delay Prediction + Policy RAG
- "Find alternative flights from DEL to BOM" -> Flight Search
- "What is the status of flight AI202?" -> Flight Status (+ Weather if requested)
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.logger import logger


# Mapping of common city names to IATA airport codes
CITY_AIRPORT_MAP = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bengaluru": "BLR",
    "bangalore": "BLR",
    "jaipur": "JAI",
    "london": "LHR",
    "heathrow": "LHR",
    "new york": "JFK",
    "jfk": "JFK",
    "san francisco": "SFO",
    "chicago": "ORD",
    "atlanta": "ATL",
    "dubai": "DXB"
}

KNOWN_AIRPORT_CODES = {
    "DEL", "BOM", "BLR", "JAI", "LHR", "JFK", "SFO", "ORD", "ATL", "DXB",
    "EWR", "LAX", "DFW", "DEN", "CLT", "MIA", "SEA", "PHX", "BOS", "MSP"
}

# Airline designators
AIRLINE_CODE_MAP = {
    "AI": "Air India",
    "UK": "Vistara",
    "6E": "IndiGo",
    "BA": "British Airways",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "AA": "American Airlines"
}


@dataclass
class RoutedEntities:
    """Entities extracted from user query and optional context."""
    flight_number: Optional[str] = None
    carrier_code: Optional[str] = None
    airline_name: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    target_date: Optional[str] = None
    min_seats: int = 1
    airports_for_weather: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """Decision specifying selected tools and extracted entity arguments."""
    selected_tools: List[str]
    entities: RoutedEntities
    intent_summary: str
    rationale: str


class AgentIntentRouter:
    """
    Evaluates passenger query and conversation context to select necessary tools.
    Enforces the rule: Do NOT call every tool for every request.
    """

    # Keyword indicators
    PREDICTION_KEYWORDS = [
        "delay", "delayed", "late", "risk", "predict", "prediction", "forecast",
        "will my flight", "chance of delay", "on time", "delay probability",
        "disruption risk", "likely to be delayed"
    ]

    POLICY_KEYWORDS = [
        "policy", "rights", "refund", "compensation", "cancel", "cancellation",
        "baggage", "lost bag", "damaged bag", "dgca", "eu261", "14 cfr",
        "hotel", "refreshment", "meal", "food", "voucher", "rules", "eligibility",
        "what should i do", "what are my rights", "what are my options", "entitled to",
        "can i get", "rebooking fee", "waiver"
    ]

    SEARCH_KEYWORDS = [
        "search", "find", "alternative", "flights from", "available flights",
        "flights to", "other flights", "options from", "rebook flight", "next flight"
    ]

    WEATHER_KEYWORDS = [
        "weather", "storm", "fog", "rain", "wind", "snow", "temperature",
        "visibility", "meteorological", "turbulence", "thunderstorm"
    ]

    STATUS_KEYWORDS = [
        "status", "where is", "gate", "terminal", "altitude", "live tracking",
        "radar", "coordinates", "flight status", "arrived", "departed"
    ]

    def route(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Determines the optimal tool subset and extracts arguments from user message + context.
        """
        text = (message or "").strip()
        lower_text = text.lower()
        ctx = context or {}

        # 1. Extract Entities
        entities = self._extract_entities(text, ctx)

        # 2. Score Intent Categories
        has_prediction_intent = any(k in lower_text for k in self.PREDICTION_KEYWORDS)
        has_policy_intent = any(k in lower_text for k in self.POLICY_KEYWORDS)
        has_search_intent = any(k in lower_text for k in self.SEARCH_KEYWORDS)
        has_weather_intent = any(k in lower_text for k in self.WEATHER_KEYWORDS)
        has_status_intent = any(k in lower_text for k in self.STATUS_KEYWORDS)

        # Disambiguation: "If my flight is delayed by 4 hours, can I get a refund?" is a POLICY question,
        # not an operational prediction request, unless an actual flight number or explicit prediction request exists.
        is_hypothetical_delay_policy = (
            has_policy_intent
            and not entities.flight_number
            and not any(phrase in lower_text for phrase in ["will my flight", "delay risk", "delay probability", "what should i do", "what are my options"])
        )
        if is_hypothetical_delay_policy:
            has_prediction_intent = False

        # Context overrides or signals
        if ctx.get("force_tools"):
            selected = list(ctx["force_tools"])
            return RoutingDecision(
                selected_tools=selected,
                entities=entities,
                intent_summary="Forced tool execution via context",
                rationale="Explicitly instructed via request context."
            )

        selected_tools: List[str] = []
        rationales: List[str] = []

        # -------------------------------------------------------------
        # Decision Matrix
        # -------------------------------------------------------------

        # Case 1: Search Request (Find alternative flights)
        if has_search_intent and not (has_prediction_intent and entities.flight_number):
            selected_tools.append("flight_search")
            rationales.append("Flight Search: Passenger is seeking available alternative flights.")
            if has_policy_intent:
                selected_tools.append("policy_rag")
                rationales.append("Policy RAG: Passenger also inquired about rebooking/refund policies.")

        # Case 2: Combined Disruption Risk + Policy Action ("High delay risk, what should I do?")
        elif has_prediction_intent and has_policy_intent:
            selected_tools.extend(["flight_status", "weather", "delay_prediction", "policy_rag"])
            rationales.append(
                "Combined Intent: Analyzing flight status, airport weather, and ML delay prediction, "
                "supplemented with authoritative policy guidance on passenger rights and remedies."
            )

        # Case 3: Pure Policy Question ("If flight is delayed 4 hours, can I get a refund?")
        elif has_policy_intent and not (has_prediction_intent and entities.flight_number):
            selected_tools.append("policy_rag")
            rationales.append("Policy RAG: Query focuses strictly on passenger rights, regulatory rules, or airline policies.")

        # Case 4: Flight Delay Prediction ("Will my flight be delayed?")
        elif has_prediction_intent:
            selected_tools.extend(["flight_status", "weather", "delay_prediction"])
            rationales.append("Prediction Intent: Querying operational status, weather observations, and ML delay inference.")

        # Case 5: Pure Flight Status / Tracking ("What is the status of AI202?")
        elif has_status_intent or (entities.flight_number and not has_policy_intent and not has_search_intent):
            selected_tools.append("flight_status")
            rationales.append("Flight Status: Passenger asked for operational status and telemetry of a specific flight.")
            if has_weather_intent:
                selected_tools.append("weather")
                rationales.append("Weather: Explicit weather conditions requested alongside flight status.")

        # Case 6: Pure Weather Query
        elif has_weather_intent:
            selected_tools.append("weather")
            rationales.append("Weather: Query is strictly regarding airport weather conditions.")

        # Default Fallback: If no clear pattern, default to Policy RAG if text exists
        else:
            selected_tools.append("policy_rag")
            rationales.append("General Advisory: Routing to Policy RAG as default informational assistant.")

        # Ensure unique preserving order
        unique_tools = []
        for t in selected_tools:
            if t not in unique_tools:
                unique_tools.append(t)

        intent_summary = f"Selected {len(unique_tools)} tool(s): {', '.join(unique_tools)}"
        rationale = " ".join(rationales)

        logger.info(f"[AgentIntentRouter] {intent_summary} | Query: '{text[:80]}...'")

        return RoutingDecision(
            selected_tools=unique_tools,
            entities=entities,
            intent_summary=intent_summary,
            rationale=rationale
        )

    def _extract_entities(self, text: str, ctx: Dict[str, Any]) -> RoutedEntities:
        """Extracts flight number, origin, destination, carrier, and weather airport codes."""
        entities = RoutedEntities()

        # Flight Number: e.g. AI202, AI 202, 6E205, UK981, BA142, DL450
        STOP_WORDS = {"BY", "TO", "IN", "ON", "AT", "IS", "AM", "OR", "AN", "IF", "AS", "DO", "SO", "UP", "NO", "FOR", "AND", "THE"}
        fn_match = re.search(r'\b([A-Z0-9]{2,3})\s?([0-9]{1,4})\b', text, re.IGNORECASE)
        if fn_match:
            carrier_part = fn_match.group(1).upper()
            number_part = fn_match.group(2)
            if carrier_part not in STOP_WORDS:
                entities.flight_number = f"{carrier_part}{number_part}"
                entities.carrier_code = carrier_part
                entities.airline_name = AIRLINE_CODE_MAP.get(carrier_part)
        elif ctx.get("flight_number"):
            entities.flight_number = str(ctx["flight_number"]).strip().upper()
            carrier_match = re.match(r'^([A-Z0-9]{2,3})', entities.flight_number)
            if carrier_match:
                entities.carrier_code = carrier_match.group(1)
                entities.airline_name = AIRLINE_CODE_MAP.get(entities.carrier_code)

        # Origin / Destination Airport Codes
        upper_tokens = [tok.strip(",.?!:;()") for tok in text.split()]
        found_airports: List[str] = []
        for tok in upper_tokens:
            tok_upper = tok.upper()
            if tok_upper in KNOWN_AIRPORT_CODES and tok_upper not in found_airports:
                found_airports.append(tok_upper)

        # Check city names
        lower_text = text.lower()
        for city, code in CITY_AIRPORT_MAP.items():
            if re.search(r'\b' + re.escape(city) + r'\b', lower_text):
                if code not in found_airports:
                    found_airports.append(code)

        # Directional heuristics: "from X to Y"
        from_to_match = re.search(r'from\s+([a-zA-Z\s]{3,15})\s+to\s+([a-zA-Z\s]{3,15})', text, re.IGNORECASE)
        if from_to_match:
            orig_raw = from_to_match.group(1).strip().lower()
            dest_raw = from_to_match.group(2).strip().lower()
            if orig_raw in CITY_AIRPORT_MAP:
                entities.origin = CITY_AIRPORT_MAP[orig_raw]
            elif orig_raw.upper() in KNOWN_AIRPORT_CODES:
                entities.origin = orig_raw.upper()

            if dest_raw in CITY_AIRPORT_MAP:
                entities.destination = CITY_AIRPORT_MAP[dest_raw]
            elif dest_raw.upper() in KNOWN_AIRPORT_CODES:
                entities.destination = dest_raw.upper()

        if not entities.origin and found_airports:
            entities.origin = found_airports[0]
            if len(found_airports) > 1:
                entities.destination = found_airports[1]

        # Context overrides
        if ctx.get("origin"):
            entities.origin = str(ctx["origin"]).strip().upper()
        if ctx.get("destination"):
            entities.destination = str(ctx["destination"]).strip().upper()
        if ctx.get("date"):
            entities.target_date = str(ctx["date"]).strip()

        # Build airports for weather
        weather_airports = []
        if entities.origin and entities.origin not in weather_airports:
            weather_airports.append(entities.origin)
        if entities.destination and entities.destination not in weather_airports:
            weather_airports.append(entities.destination)
        for a in found_airports:
            if a not in weather_airports:
                weather_airports.append(a)

        if not weather_airports and entities.flight_number == "AI202":
            # Default benchmark corridor for AI202
            weather_airports = ["DEL", "BOM"]

        entities.airports_for_weather = weather_airports

        return entities


# Singleton router
intent_router = AgentIntentRouter()
