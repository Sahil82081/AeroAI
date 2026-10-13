import os
import json
import httpx
from typing import Optional
from app.core.config import settings
from app.core.logger import logger
from app.schemas.ingestion_schemas import NormalizedBooking, ParserExtractionResult
from app.models.models import EmailParsingStatus
from app.modules.ingestion.validator import BookingValidator

GEMINI_PROMPT_TEMPLATE = """
You are an expert travel confirmation email parser for the Autonomous Disruption Recovery Agent.
Analyze the following travel booking confirmation email and extract the structured booking details in valid JSON format.

Supported types: "flight", "train", "bus", "hotel", "activity".

CRITICAL INSTRUCTIONS:
1. Do NOT invent or hallucinate missing information.
2. If dates or times are imperfect, approximate or missing, set the field to null.
3. If information is ambiguous, assign an appropriate confidence score (0.0 to 1.0).
4. Dates and times MUST be in ISO format (YYYY-MM-DDTHH:MM:SS) if identifiable, otherwise null.

JSON OUTPUT SCHEMA:
{
  "type": "flight" | "train" | "bus" | "hotel" | "activity",
  "provider": string,
  "booking_reference": string,
  "title": string,
  "passenger": string or null,
  "origin": string or null,
  "destination": string or null,
  "departure": string (ISO) or null,
  "arrival": string (ISO) or null,
  "flight_number": string or null,
  "train_number": string or null,
  "bus_number": string or null,
  "hotel_name": string or null,
  "room_type": string or null,
  "seat": string or null,
  "price": number,
  "currency": string,
  "confidence": number between 0.0 and 1.0
}

Subject: {subject}
Body:
{body}

Respond ONLY with the JSON block.
"""

class GeminiEmailParser:
    """Uses Google Gemini API for intelligent zero-shot travel extraction."""

    @classmethod
    async def parse(cls, subject: str, body: str) -> ParserExtractionResult:
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.info("GEMINI_API_KEY not configured. Falling back to Heuristic parser.")
            from app.modules.ingestion.heuristic_parser import HeuristicEmailParser
            return HeuristicEmailParser.parse(subject, body)

        prompt = GEMINI_PROMPT_TEMPLATE.format(subject=subject, body=body)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    logger.warning(f"Gemini API returned status {res.status_code}. Using heuristic fallback.")
                    from app.modules.ingestion.heuristic_parser import HeuristicEmailParser
                    return HeuristicEmailParser.parse(subject, body)
                
                resp_json = res.json()
                text_content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                parsed_json = json.loads(text_content)

                model_confidence = float(parsed_json.pop("confidence", 0.85))
                normalized = NormalizedBooking(**parsed_json)
                is_valid, missing, val_conf, clarification = BookingValidator.validate(normalized)

                final_conf = round(min(model_confidence, val_conf), 2)
                status = EmailParsingStatus.PARSED if is_valid and final_conf >= 0.7 else EmailParsingStatus.UNCERTAIN

                return ParserExtractionResult(
                    success=True,
                    status=status,
                    confidence=final_conf,
                    booking_type=normalized.type,
                    normalized_booking=normalized,
                    missing_fields=missing,
                    clarification_prompt=clarification,
                    parser_used="gemini"
                )
        except Exception as e:
            logger.error(f"Gemini parser call failed: {e}. Falling back to Heuristic parser.")
            from app.modules.ingestion.heuristic_parser import HeuristicEmailParser
            result = HeuristicEmailParser.parse(subject, body)
            result.parser_used = "heuristic-fallback"
            return result
