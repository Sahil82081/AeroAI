"""
Supplier Integration Module.
Provides realistic mock interfaces simulating Airline GDS, Hotel CRS, and Rail APIs.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta

class MockAirlineSupplier:
    """Simulates real external airline flight availability and rebooking API."""
    @staticmethod
    def search_alternative_flights(origin: str, destination: str, earliest_time: datetime) -> List[Dict[str, Any]]:
        return [
            {
                "flight_number": "NH-11",
                "airline": "All Nippon Airways",
                "departure": earliest_time + timedelta(hours=2),
                "arrival": earliest_time + timedelta(hours=13),
                "price": 320.0,
                "currency": "USD",
                "seats_available": 4,
                "simulated": True
            },
            {
                "flight_number": "JL-2",
                "airline": "Japan Airlines",
                "departure": earliest_time + timedelta(hours=4),
                "arrival": earliest_time + timedelta(hours=15),
                "price": 280.0,
                "currency": "USD",
                "seats_available": 9,
                "simulated": True
            }
        ]

class MockHotelSupplier:
    """Simulates real hotel reservation updates and check-in notices."""
    @staticmethod
    def update_checkin_window(reservation_ref: str, new_estimated_checkin: datetime) -> Dict[str, Any]:
        return {
            "reservation_ref": reservation_ref,
            "status": "CHECKIN_TIME_UPDATED",
            "confirmed_checkin": new_estimated_checkin.isoformat(),
            "no_show_penalty_waived": True,
            "simulated": True
        }
