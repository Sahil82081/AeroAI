import re
from typing import Tuple

class LocationMatcher:
    """
    Matches location and terminal proximity across multi-modal bookings
    (Airports, Railway Stations, City Centers, Hotels).
    """

    AIRPORT_CODES = {
        "bom": ("mumbai", "airport"),
        "del": ("delhi", "airport"),
        "blr": ("bangalore", "airport"),
        "sfo": ("san francisco", "airport"),
        "hnd": ("tokyo", "airport"),
        "nrt": ("tokyo", "airport"),
        "lhr": ("london", "airport"),
        "jfk": ("new york", "airport"),
    }

    @classmethod
    def normalize_city(cls, location_str: str) -> str:
        if not location_str:
            return "unknown"
        text = location_str.lower().strip()

        # Check IATA codes in brackets or standalone
        code_match = re.search(r"\b([a-z]{3})\b", text)
        if code_match and code_match.group(1) in cls.AIRPORT_CODES:
            return cls.AIRPORT_CODES[code_match.group(1)][0]

        for city in ["mumbai", "delhi", "bangalore", "jaipur", "chandigarh", "tokyo", "kyoto", "san francisco", "london", "singapore"]:
            if city in text:
                return city

        # Clean punctuation
        cleaned = re.sub(r"[,\-\(\)]", " ", text).split()
        return cleaned[0] if cleaned else "unknown"

    @classmethod
    def evaluate_transfer_proximity(cls, arrival_loc: str, departure_loc: str, arr_type: str, dep_type: str) -> Tuple[str, int]:
        """
        Returns:
            (transfer_type, min_required_buffer_minutes)
            transfer_type: 'same_airport', 'same_station', 'intra_city_transfer', 'inter_city_transfer'
        """
        arr_city = cls.normalize_city(arrival_loc)
        dep_city = cls.normalize_city(departure_loc)

        arr_lower = (arrival_loc or "").lower()
        dep_lower = (departure_loc or "").lower()

        if arr_city != dep_city and arr_city != "unknown" and dep_city != "unknown":
            # Inter-city mismatch! Impossible connection unless another transit leg exists
            return "inter_city_transfer", 240

        # Same city or local transfer
        if arr_type == "FLIGHT" and dep_type == "FLIGHT":
            # Air to Air transfer
            if ("terminal 2" in arr_lower and "terminal 2" in dep_lower) or ("t2" in arr_lower and "t2" in dep_lower):
                return "same_terminal", 60
            return "airport_terminal_transfer", 90

        if arr_type == "FLIGHT" and dep_type == "TRAIN":
            # Airport to Railway Station (e.g. DEL Airport to NDLS / Old Delhi)
            return "airport_to_station_transfer", 120

        if arr_type == "FLIGHT" and dep_type == "HOTEL":
            # Airport to Hotel
            return "airport_to_hotel_transfer", 75

        if arr_type == "TRAIN" and dep_type == "HOTEL":
            # Station to Hotel
            return "station_to_hotel_transfer", 45

        if arr_type == "HOTEL" and dep_type in ["ACTIVITY", "TOUR"]:
            return "hotel_to_activity_transfer", 30

        return "intra_city_transfer", 60
