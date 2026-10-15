"""
Mock Flight Provider for AeroAI.

Provides deterministic, offline simulated flight status and inventory records.
Used for local testing, offline golden-triangle demonstrations, and as an automatic
fallback when real external aviation APIs (OpenSky, Aviationstack) are unreachable,
rate-limited, or lack coverage for a specific callsign.

ALL outputs from this provider are explicitly tagged with:
    data_source = "MOCK"
    provider_name = "Mock Flight Provider"
"""

import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from app.core.logger import logger
from app.modules.flights.interfaces import (
    FlightProvider,
    FlightStatusRecord,
    FlightPosition,
    FlightInventoryItem
)

# Known catalog of benchmark flight templates
MOCK_FLIGHT_CATALOG: Dict[str, Dict[str, Any]] = {
    "AI202": {
        "carrier_code": "AI",
        "carrier_name": "Air India",
        "origin": "BOM",
        "origin_city": "Mumbai",
        "destination": "DEL",
        "destination_city": "Delhi",
        "status": "DELAYED",
        "delay_minutes": 240,
        "position": {
            "latitude": 19.0896,
            "longitude": 72.8656,
            "altitude_ft": 0.0,
            "velocity_kts": 0.0,
            "heading_deg": 45.0,
            "vertical_rate_fpm": 0.0,
            "on_ground": True
        },
        "notes": "Flight delayed +240m due to incoming aircraft rotation and severe fog ground hold."
    },
    "UK981": {
        "carrier_code": "UK",
        "carrier_name": "Vistara (Air India)",
        "origin": "DEL",
        "origin_city": "Delhi",
        "destination": "BOM",
        "destination_city": "Mumbai",
        "status": "AIRBORNE",
        "delay_minutes": 15,
        "position": {
            "latitude": 24.5854,
            "longitude": 73.7125,
            "altitude_ft": 34000.0,
            "velocity_kts": 450.0,
            "heading_deg": 195.0,
            "vertical_rate_fpm": 0.0,
            "on_ground": False
        },
        "notes": "En-route cruising at FL340 over Rajasthan corridor."
    },
    "6E205": {
        "carrier_code": "6E",
        "carrier_name": "IndiGo",
        "origin": "DEL",
        "origin_city": "Delhi",
        "destination": "JAI",
        "destination_city": "Jaipur",
        "status": "SCHEDULED",
        "delay_minutes": 0,
        "position": None,
        "notes": "On-time, boarding at gate 14A."
    },
    "BA142": {
        "carrier_code": "BA",
        "carrier_name": "British Airways",
        "origin": "DEL",
        "origin_city": "Delhi",
        "destination": "LHR",
        "destination_city": "London",
        "status": "AIRBORNE",
        "delay_minutes": 0,
        "position": {
            "latitude": 38.9072,
            "longitude": 45.1234,
            "altitude_ft": 38000.0,
            "velocity_kts": 490.0,
            "heading_deg": 305.0,
            "vertical_rate_fpm": 0.0,
            "on_ground": False
        },
        "notes": "Cruising transatlantic corridor towards London Heathrow."
    },
    "DL450": {
        "carrier_code": "DL",
        "carrier_name": "Delta Air Lines",
        "origin": "JFK",
        "origin_city": "New York",
        "destination": "SFO",
        "destination_city": "San Francisco",
        "status": "AIRBORNE",
        "delay_minutes": 35,
        "position": {
            "latitude": 41.8781,
            "longitude": -87.6298,
            "altitude_ft": 32000.0,
            "velocity_kts": 430.0,
            "heading_deg": 260.0,
            "vertical_rate_fpm": -200.0,
            "on_ground": False
        },
        "notes": "Transcontinental flight delayed 35m due to headwind."
    }
}


class MockFlightProvider(FlightProvider):
    """Concrete mock implementation of the FlightProvider interface."""

    def __init__(self, simulate_latency_ms: float = 0.0):
        self.simulate_latency_ms = simulate_latency_ms

    async def get_flight_status(
        self,
        flight_number: str,
        target_date: Optional[str] = None
    ) -> Optional[FlightStatusRecord]:
        """Returns deterministic simulated flight status for a given flight number."""
        clean_fn = re.sub(r"[\s\-]", "", flight_number.upper())
        now = datetime.now(timezone.utc)

        # Check catalog first
        if clean_fn in MOCK_FLIGHT_CATALOG:
            cat = MOCK_FLIGHT_CATALOG[clean_fn]
            pos = FlightPosition(**cat["position"]) if cat.get("position") else None
            sched_dep = now - timedelta(hours=2) if cat["status"] in ["AIRBORNE", "DELAYED"] else now + timedelta(hours=1)
            sched_arr = sched_dep + timedelta(hours=2)
            act_dep = sched_dep + timedelta(minutes=cat["delay_minutes"])
            est_arr = sched_arr + timedelta(minutes=cat["delay_minutes"])

            return FlightStatusRecord(
                flight_number=clean_fn,
                callsign=f"{cat['carrier_code']}{clean_fn[2:]}",
                carrier_code=cat["carrier_code"],
                carrier_name=cat["carrier_name"],
                origin=cat["origin"],
                origin_city=cat.get("origin_city"),
                destination=cat["destination"],
                destination_city=cat.get("destination_city"),
                status=cat["status"],
                scheduled_departure=sched_dep,
                actual_departure=act_dep if cat["status"] != "SCHEDULED" else None,
                scheduled_arrival=sched_arr,
                estimated_arrival=est_arr,
                delay_minutes=cat["delay_minutes"],
                position=pos,
                data_source="MOCK",
                provider_name="Mock Flight Provider",
                is_fallback=False,
                notes=cat.get("notes"),
                last_updated=now
            )

        # Synthesize fallback for unknown flight numbers (deterministic carrier mapping)
        carrier_prefix = clean_fn[:2] if len(clean_fn) >= 2 else "AI"
        carrier_map = {
            "AI": ("Air India", "BOM", "DEL"),
            "6E": ("IndiGo", "DEL", "BOM"),
            "UK": ("Vistara", "DEL", "BLR"),
            "SG": ("SpiceJet", "DEL", "JAI"),
            "BA": ("British Airways", "LHR", "DEL"),
            "DL": ("Delta Air Lines", "JFK", "LAX"),
            "AA": ("American Airlines", "ORD", "DFW"),
            "UA": ("United Airlines", "SFO", "ORD"),
            "LH": ("Lufthansa", "FRA", "DEL"),
            "EK": ("Emirates", "DXB", "BOM"),
        }
        if carrier_prefix not in carrier_map:
            return None

        carrier_name, default_orig, default_dest = carrier_map[carrier_prefix]

        sched_dep = now + timedelta(hours=2)
        sched_arr = sched_dep + timedelta(hours=2, minutes=15)

        return FlightStatusRecord(
            flight_number=clean_fn,
            callsign=f"{carrier_prefix}{clean_fn[2:]}",
            carrier_code=carrier_prefix,
            carrier_name=carrier_name,
            origin=default_orig,
            destination=default_dest,
            status="SCHEDULED",
            scheduled_departure=sched_dep,
            actual_departure=None,
            scheduled_arrival=sched_arr,
            estimated_arrival=sched_arr,
            delay_minutes=0,
            position=None,
            data_source="MOCK",
            provider_name="Mock Flight Provider",
            is_fallback=False,
            notes="Synthesized on-demand deterministic mock flight status.",
            last_updated=now
        )

    async def search_flights(
        self,
        origin: str,
        destination: str,
        earliest_time: Optional[datetime] = None,
        min_seats: int = 1
    ) -> List[FlightInventoryItem]:
        """Provides simulated alternative flights across scheduled corridors."""
        base_time = earliest_time or datetime.now(timezone.utc)
        results = []

        # Standard carrier templates
        templates = [
            ("AI-801", "Air India", 1, 130, 4850.0, 12, "ECONOMY"),
            ("6E-502", "IndiGo", 2.5, 125, 4200.0, 8, "ECONOMY"),
            ("UK-915", "Vistara", 4.0, 135, 5900.0, 5, "PREMIUM_ECONOMY"),
            ("AI-214", "Air India", 6.0, 130, 11500.0, 3, "BUSINESS"),
            ("6E-711", "IndiGo", 8.0, 120, 3800.0, 14, "ECONOMY"),
        ]

        for fn, carrier, hr_offset, dur, price, seats, cabin in templates:
            if seats < min_seats:
                continue
            dep = base_time + timedelta(hours=hr_offset)
            arr = dep + timedelta(minutes=dur)
            results.append(FlightInventoryItem(
                flight_number=fn,
                carrier=carrier,
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time=dep,
                arrival_time=arr,
                duration_minutes=dur,
                price=price,
                currency="INR",
                available_seats=seats,
                cabin_class=cabin,
                data_source="MOCK",
                provider_name="Mock Flight Provider",
                is_fallback=False
            ))

        return results
