"""
Realistic Mock Datasets for Flights, Trains, Buses, and Hotels.
Covers Indian domestic corridors (Mumbai -> Delhi -> Jaipur / Chandigarh)
and International corridors (SFO -> Tokyo -> Kyoto).
Explicitly labeled as SIMULATED MOCK SUPPLIER DATA.
"""
import copy
from typing import Dict, List, Any

INITIAL_FLIGHTS_DATASET: List[Dict[str, Any]] = [
    {
        "transport_id": "FLT101",
        "supplier_type": "flight",
        "provider": "IndiGo Airlines",
        "flight_number": "6E-2142",
        "origin": "Mumbai",
        "origin_code": "BOM",
        "destination": "Delhi",
        "destination_code": "DEL",
        "departure": "2026-10-20T12:15:00",
        "arrival": "2026-10-20T14:25:00",
        "duration_minutes": 130,
        "price": 6200.0,
        "currency": "INR",
        "available_seats": 12,
        "cabin_class": "ECONOMY_FLEX",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 4,
            "penalty_pct": 10.0,
            "cancellation_fee": 500.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "FLT102",
        "supplier_type": "flight",
        "provider": "Vistara / Air India",
        "flight_number": "AI-866",
        "origin": "Mumbai",
        "origin_code": "BOM",
        "destination": "Delhi",
        "destination_code": "DEL",
        "departure": "2026-10-20T14:00:00",
        "arrival": "2026-10-20T16:10:00",
        "duration_minutes": 130,
        "price": 7450.0,
        "currency": "INR",
        "available_seats": 8,
        "cabin_class": "PREMIUM_ECONOMY",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 12,
            "penalty_pct": 15.0,
            "cancellation_fee": 1000.0,
            "rebooking_fee": 750.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "FLT103",
        "supplier_type": "flight",
        "provider": "IndiGo Airlines",
        "flight_number": "6E-5091",
        "origin": "Delhi",
        "origin_code": "DEL",
        "destination": "Jaipur",
        "destination_code": "JAI",
        "departure": "2026-10-20T17:45:00",
        "arrival": "2026-10-20T18:45:00",
        "duration_minutes": 60,
        "price": 3850.0,
        "currency": "INR",
        "available_seats": 6,
        "cabin_class": "ECONOMY",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 6,
            "penalty_pct": 15.0,
            "cancellation_fee": 600.0,
            "rebooking_fee": 400.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "FLT104",
        "supplier_type": "flight",
        "provider": "Alliance Air",
        "flight_number": "9I-831",
        "origin": "Delhi",
        "origin_code": "DEL",
        "destination": "Jaipur",
        "destination_code": "JAI",
        "departure": "2026-10-20T19:30:00",
        "arrival": "2026-10-20T20:35:00",
        "duration_minutes": 65,
        "price": 3400.0,
        "currency": "INR",
        "available_seats": 14,
        "cabin_class": "ECONOMY_SAVER",
        "cancellation_rules": {
            "fare_tier": "SAVER",
            "refundable": False,
            "free_cancellation_hours_before": 24,
            "penalty_pct": 88.0,
            "cancellation_fee": 2500.0,
            "rebooking_fee": 1200.0
        },
        "refund_eligibility": False,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "FLT201",
        "supplier_type": "flight",
        "provider": "All Nippon Airways",
        "flight_number": "NH-107",
        "origin": "SFO",
        "origin_code": "SFO",
        "destination": "HND",
        "destination_code": "HND",
        "departure": "2026-10-20T13:30:00",
        "arrival": "2026-10-21T16:45:00",
        "duration_minutes": 675,
        "price": 1280.0,
        "currency": "USD",
        "available_seats": 5,
        "cabin_class": "ECONOMY_FLEX",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 2,
            "penalty_pct": 5.0,
            "cancellation_fee": 50.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "FLT202",
        "supplier_type": "flight",
        "provider": "Japan Airlines",
        "flight_number": "JL-001",
        "origin": "SFO",
        "origin_code": "SFO",
        "destination": "HND",
        "destination_code": "HND",
        "departure": "2026-10-20T15:00:00",
        "arrival": "2026-10-21T18:15:00",
        "duration_minutes": 675,
        "price": 1190.0,
        "currency": "USD",
        "available_seats": 9,
        "cabin_class": "ECONOMY",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 6,
            "penalty_pct": 10.0,
            "cancellation_fee": 100.0,
            "rebooking_fee": 50.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    }
]


INITIAL_TRAINS_DATASET: List[Dict[str, Any]] = [
    {
        "transport_id": "TRN123",
        "supplier_type": "train",
        "provider": "Indian Railways (IRCTC)",
        "train_number": "12015 / Ajmer Shatabdi Special",
        "origin": "Delhi",
        "origin_code": "NDLS",
        "destination": "Jaipur",
        "destination_code": "JP",
        "departure": "2026-10-20T17:30:00",
        "arrival": "2026-10-20T22:00:00",
        "duration_minutes": 270,
        "price": 800.0,
        "currency": "INR",
        "available_seats": 15,
        "coach_class": "AC_CHAIR_CAR (CC)",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 4,
            "penalty_pct": 10.0,
            "cancellation_fee": 65.0,
            "rebooking_fee": 50.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "TRN124",
        "supplier_type": "train",
        "provider": "Indian Railways (IRCTC)",
        "train_number": "20978 / Vande Bharat Express",
        "origin": "Delhi",
        "origin_code": "DEC",
        "destination": "Jaipur",
        "destination_code": "JP",
        "departure": "2026-10-20T18:40:00",
        "arrival": "2026-10-20T22:30:00",
        "duration_minutes": 230,
        "price": 1150.0,
        "currency": "INR",
        "available_seats": 22,
        "coach_class": "EXECUTIVE_CHAIR (EC)",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 4,
            "penalty_pct": 10.0,
            "cancellation_fee": 120.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "TRN125",
        "supplier_type": "train",
        "provider": "Indian Railways (IRCTC)",
        "train_number": "12986 / Jaipur Double Decker AC",
        "origin": "Delhi",
        "origin_code": "DEE",
        "destination": "Jaipur",
        "destination_code": "JP",
        "departure": "2026-10-20T19:35:00",
        "arrival": "2026-10-21T00:05:00",
        "duration_minutes": 270,
        "price": 680.0,
        "currency": "INR",
        "available_seats": 34,
        "coach_class": "AC_CHAIR_CAR (CC)",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 6,
            "penalty_pct": 15.0,
            "cancellation_fee": 60.0,
            "rebooking_fee": 40.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "TRN201",
        "supplier_type": "train",
        "provider": "Indian Railways (IRCTC)",
        "train_number": "12951 / Mumbai New Delhi Tejas Rajdhani",
        "origin": "Mumbai",
        "origin_code": "MMCT",
        "destination": "Delhi",
        "destination_code": "NDLS",
        "departure": "2026-10-20T17:00:00",
        "arrival": "2026-10-21T08:32:00",
        "duration_minutes": 932,
        "price": 3420.0,
        "currency": "INR",
        "available_seats": 9,
        "coach_class": "AC_2_TIER (2A)",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 12,
            "penalty_pct": 15.0,
            "cancellation_fee": 200.0,
            "rebooking_fee": 150.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "TRN301",
        "supplier_type": "train",
        "provider": "JR Central Shinkansen",
        "train_number": "Nozomi 418",
        "origin": "Tokyo",
        "origin_code": "TYO",
        "destination": "Kyoto",
        "destination_code": "KYO",
        "departure": "2026-10-21T18:00:00",
        "arrival": "2026-10-21T20:15:00",
        "duration_minutes": 135,
        "price": 135.0,
        "currency": "USD",
        "available_seats": 18,
        "coach_class": "ORDINARY_RESERVED",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 1,
            "penalty_pct": 5.0,
            "cancellation_fee": 5.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "TRN302",
        "supplier_type": "train",
        "provider": "JR Central Shinkansen",
        "train_number": "Hikari 522",
        "origin": "Tokyo",
        "origin_code": "TYO",
        "destination": "Kyoto",
        "destination_code": "KYO",
        "departure": "2026-10-21T20:03:00",
        "arrival": "2026-10-21T22:45:00",
        "duration_minutes": 162,
        "price": 120.0,
        "currency": "USD",
        "available_seats": 25,
        "coach_class": "ORDINARY_RESERVED",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 1,
            "penalty_pct": 5.0,
            "cancellation_fee": 5.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    }
]


INITIAL_BUSES_DATASET: List[Dict[str, Any]] = [
    {
        "transport_id": "BUS101",
        "supplier_type": "bus",
        "provider": "RSRTC Gold Line Volvo AC",
        "bus_number": "RJ-14-PA-8821",
        "origin": "Delhi",
        "origin_code": "DEL-ISBT",
        "destination": "Jaipur",
        "destination_code": "JAI-SINDHI",
        "departure": "2026-10-20T17:00:00",
        "arrival": "2026-10-20T22:15:00",
        "duration_minutes": 315,
        "price": 750.0,
        "currency": "INR",
        "available_seats": 19,
        "bus_type": "VOLVO_MULTI_AXLE_SEMI_SLEEPER",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 2,
            "penalty_pct": 10.0,
            "cancellation_fee": 50.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "BUS102",
        "supplier_type": "bus",
        "provider": "Zingbus Electric AC Sleeper",
        "bus_number": "ZB-DL-JP-409",
        "origin": "Delhi",
        "origin_code": "DEL-DHAULA",
        "destination": "Jaipur",
        "destination_code": "JAI-NARAYAN",
        "departure": "2026-10-20T18:30:00",
        "arrival": "2026-10-20T23:30:00",
        "duration_minutes": 300,
        "price": 650.0,
        "currency": "INR",
        "available_seats": 11,
        "bus_type": "ELECTRIC_AC_SLEEPER_2_1",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 4,
            "penalty_pct": 15.0,
            "cancellation_fee": 75.0,
            "rebooking_fee": 25.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "BUS103",
        "supplier_type": "bus",
        "provider": "NueGo Electric Premier Coach",
        "bus_number": "NG-EV-118",
        "origin": "Delhi",
        "origin_code": "DEL-ISBT",
        "destination": "Jaipur",
        "destination_code": "JAI-SINDHI",
        "departure": "2026-10-20T20:00:00",
        "arrival": "2026-10-21T00:45:00",
        "duration_minutes": 285,
        "price": 590.0,
        "currency": "INR",
        "available_seats": 24,
        "bus_type": "ELECTRIC_SEATER_AC",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 1,
            "penalty_pct": 5.0,
            "cancellation_fee": 30.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "BUS201",
        "supplier_type": "bus",
        "provider": "Zingbus Electric AC Sleeper",
        "bus_number": "ZB-DL-CHD-202",
        "origin": "Delhi",
        "origin_code": "DEL-ISBT",
        "destination": "Chandigarh",
        "destination_code": "CHD-43",
        "departure": "2026-10-24T08:00:00",
        "arrival": "2026-10-24T13:15:00",
        "duration_minutes": 315,
        "price": 850.0,
        "currency": "INR",
        "available_seats": 16,
        "bus_type": "ELECTRIC_AC_SLEEPER",
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 4,
            "penalty_pct": 10.0,
            "cancellation_fee": 80.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "transport_id": "BUS301",
        "supplier_type": "bus",
        "provider": "Airport Limousine Bus Tokyo",
        "bus_number": "TYO-LIMO-18",
        "origin": "HND",
        "origin_code": "HND",
        "destination": "Tokyo",
        "destination_code": "TYO-SHINJUKU",
        "departure": "2026-10-21T20:15:00",
        "arrival": "2026-10-21T21:05:00",
        "duration_minutes": 50,
        "price": 25.0,
        "currency": "USD",
        "available_seats": 28,
        "bus_type": "AIRPORT_EXPRESS_COACH",
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 1,
            "penalty_pct": 0.0,
            "cancellation_fee": 0.0,
            "rebooking_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    }
]


INITIAL_HOTELS_DATASET: List[Dict[str, Any]] = [
    {
        "hotel_id": "HTL101",
        "supplier_type": "hotel",
        "provider": "The Heritage Palace Jaipur",
        "hotel_name": "The Heritage Palace Jaipur",
        "location": "Jaipur",
        "city": "Jaipur",
        "address": "MI Road, Civil Lines, Jaipur, Rajasthan 302001",
        "check_in_window": "14:00 - 23:59 (24h Front Desk)",
        "standard_check_in": "18:00",
        "standard_check_out": "11:00",
        "price_per_night": 5400.0,
        "price": 5400.0,
        "currency": "INR",
        "available_rooms": 7,
        "room_type": "Royal Heritage Deluxe Room",
        "late_checkin_supported": True,
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 24,
            "penalty_pct": 20.0,
            "cancellation_fee": 1000.0,
            "late_checkin_modification_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "hotel_id": "HTL102",
        "supplier_type": "hotel",
        "provider": "ITC Rajputana Jaipur",
        "hotel_name": "ITC Rajputana, A Luxury Collection Hotel",
        "location": "Jaipur",
        "city": "Jaipur",
        "address": "Palace Road, Jaipur, Rajasthan 302006 (Near Jaipur Railway Station)",
        "check_in_window": "15:00 - 23:59 (24h Front Desk)",
        "standard_check_in": "15:00",
        "standard_check_out": "12:00",
        "price_per_night": 8500.0,
        "price": 8500.0,
        "currency": "INR",
        "available_rooms": 5,
        "room_type": "Executive Club Room",
        "late_checkin_supported": True,
        "cancellation_rules": {
            "fare_tier": "STANDARD",
            "refundable": True,
            "free_cancellation_hours_before": 24,
            "penalty_pct": 25.0,
            "cancellation_fee": 1500.0,
            "late_checkin_modification_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "hotel_id": "HTL201",
        "supplier_type": "hotel",
        "provider": "Pullman New Delhi Aerocity",
        "hotel_name": "Pullman New Delhi Aerocity",
        "location": "Delhi",
        "city": "Delhi",
        "address": "Asset No 02, GMR Hospitality District, IGI Airport, New Delhi",
        "check_in_window": "14:00 - 23:59 (24h Airport Transit Desk)",
        "standard_check_in": "14:00",
        "standard_check_out": "12:00",
        "price_per_night": 9200.0,
        "price": 9200.0,
        "currency": "INR",
        "available_rooms": 10,
        "room_type": "Superior Transit King Room",
        "late_checkin_supported": True,
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 6,
            "penalty_pct": 10.0,
            "cancellation_fee": 800.0,
            "late_checkin_modification_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "hotel_id": "HTL301",
        "supplier_type": "hotel",
        "provider": "JW Marriott Mumbai Sahar",
        "hotel_name": "JW Marriott Mumbai Sahar",
        "location": "Mumbai",
        "city": "Mumbai",
        "address": "IA Project Road, Chhatrapati Shivaji Intl Airport, Mumbai",
        "check_in_window": "15:00 - 23:59",
        "standard_check_in": "15:00",
        "standard_check_out": "12:00",
        "price_per_night": 14500.0,
        "price": 14500.0,
        "currency": "INR",
        "available_rooms": 4,
        "room_type": "Deluxe Guest Room, 1 King",
        "late_checkin_supported": True,
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 24,
            "penalty_pct": 15.0,
            "cancellation_fee": 2000.0,
            "late_checkin_modification_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    },
    {
        "hotel_id": "HTL401",
        "supplier_type": "hotel",
        "provider": "Park Hyatt Tokyo",
        "hotel_name": "Park Hyatt Tokyo",
        "location": "Tokyo",
        "city": "Tokyo",
        "address": "3-7-1-2 Nishi-Shinjuku, Shinjuku-Ku, Tokyo, Japan",
        "check_in_window": "15:00 - 23:59 (24h Concierge)",
        "standard_check_in": "15:00",
        "standard_check_out": "12:00",
        "price_per_night": 350.0,
        "price": 350.0,
        "currency": "USD",
        "available_rooms": 6,
        "room_type": "Park Deluxe King",
        "late_checkin_supported": True,
        "cancellation_rules": {
            "fare_tier": "FLEXIBLE",
            "refundable": True,
            "free_cancellation_hours_before": 24,
            "penalty_pct": 10.0,
            "cancellation_fee": 50.0,
            "late_checkin_modification_fee": 0.0
        },
        "refund_eligibility": True,
        "is_mock_api": True,
        "simulated": True
    }
]


class MockSupplierDataStore:
    """In-memory stateful store for mock supplier inventory and active booking records."""
    flights: List[Dict[str, Any]] = copy.deepcopy(INITIAL_FLIGHTS_DATASET)
    trains: List[Dict[str, Any]] = copy.deepcopy(INITIAL_TRAINS_DATASET)
    buses: List[Dict[str, Any]] = copy.deepcopy(INITIAL_BUSES_DATASET)
    hotels: List[Dict[str, Any]] = copy.deepcopy(INITIAL_HOTELS_DATASET)
    booking_ledger: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def reset(cls) -> None:
        cls.flights = copy.deepcopy(INITIAL_FLIGHTS_DATASET)
        cls.trains = copy.deepcopy(INITIAL_TRAINS_DATASET)
        cls.buses = copy.deepcopy(INITIAL_BUSES_DATASET)
        cls.hotels = copy.deepcopy(INITIAL_HOTELS_DATASET)
        cls.booking_ledger.clear()

    @classmethod
    def find_transport(cls, transport_id: str) -> Any:
        for collection in (cls.flights, cls.trains, cls.buses):
            for item in collection:
                if item["transport_id"].upper() == transport_id.upper():
                    return item
        return None

    @classmethod
    def find_hotel(cls, hotel_id: str) -> Any:
        for item in cls.hotels:
            if item["hotel_id"].upper() == hotel_id.upper():
                return item
        return None


def matches_location(item_loc: str, item_code: str, query_loc: str) -> bool:
    """Case-insensitive matching across city names, airport/station codes, and substrings."""
    if not query_loc:
        return True
    q = query_loc.strip().lower()
    loc = (item_loc or "").lower()
    code = (item_code or "").lower()
    if q in loc or loc in q or q == code:
        return True
    # Common aliases
    aliases = {
        "mumbai": ["bom", "mmct", "chhatrapati", "sahar", "mumbai"],
        "delhi": ["del", "ndls", "dee", "dec", "isbt", "new delhi", "delhi", "indira gandhi"],
        "jaipur": ["jai", "jp", "jaipur", "sindhi"],
        "tokyo": ["hnd", "nrt", "tyo", "haneda", "narita", "shinjuku", "tokyo"],
        "kyoto": ["kyo", "kyoto"],
        "sfo": ["sfo", "san francisco"],
        "chandigarh": ["chd", "chandigarh"]
    }
    for canonical, terms in aliases.items():
        if any(t in q for t in terms) and (any(t in loc for t in terms) or code in terms):
            return True
    return False
