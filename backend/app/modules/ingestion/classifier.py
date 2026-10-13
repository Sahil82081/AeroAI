import re
from typing import Optional, Tuple, List
from app.models.models import BookingType

class BookingClassifier:
    """Classifies travel emails into flight, train, bus, hotel, or activity."""
    
    PATTERNS = {
        "flight": [
            r"\b(flight|airline|airways|airport|boarding pass|pnr|terminal|seat \d+[a-z]?|takeoff|gate \d+)\b",
            r"\b(indigo|air india|emirates|delta|united|lufthansa|singapore airlines|qantas|british airways|spicejet|vistara|ryanair)\b",
            r"\b([A-Z0-9]{2}\s*-\s*\d{3,4}|flight number)\b"
        ],
        "train": [
            r"\b(train|railway|railways|irctc|shinkansen|eurostar|amtrak|berth|coach|station|platform|pnr number|e-ticket)\b",
            r"\b(rajdhani|shatabdi|tejas|duronto|garib rath|sncf|deutsche bahn)\b"
        ],
        "bus": [
            r"\b(bus|redbus|coach|zingbus|volvo|isbt|boarding point|drop-off point|sleeper|seater)\b"
        ],
        "hotel": [
            r"\b(hotel|resort|check-in|check-out|room|nights?|guests?|marriott|hyatt|hilton|taj|radisson|airbnb|hostel)\b"
        ],
        "activity": [
            r"\b(tour|activity|walking tour|museum|sightseeing|voucher|guide|meeting point|getyourguide|viator|klook)\b"
        ]
    }

    @classmethod
    def classify(cls, subject: str, body: str) -> Tuple[Optional[str], float]:
        text = f"{subject}\n{body}".lower()
        scores = {"flight": 0.0, "train": 0.0, "bus": 0.0, "hotel": 0.0, "activity": 0.0}

        for category, patterns in cls.PATTERNS.items():
            for pat in patterns:
                matches = re.findall(pat, text, re.IGNORECASE)
                scores[category] += len(matches) * 1.5

        # Subject keywords have higher weight
        subject_lower = subject.lower()
        if "flight" in subject_lower or "airline" in subject_lower:
            scores["flight"] += 4.0
        if "train" in subject_lower or "irctc" in subject_lower or "rail" in subject_lower:
            scores["train"] += 4.0
        if "bus" in subject_lower or "redbus" in subject_lower:
            scores["bus"] += 4.0
        if "hotel" in subject_lower or "reservation confirmed" in subject_lower or "stay" in subject_lower:
            scores["hotel"] += 4.0
        if "tour" in subject_lower or "activity" in subject_lower or "experience" in subject_lower:
            scores["activity"] += 4.0

        best_category = max(scores, key=scores.get)
        total_score = sum(scores.values())

        if total_score == 0 or scores[best_category] == 0:
            return None, 0.0

        confidence = min(1.0, round(scores[best_category] / max(1.0, total_score * 0.8), 2))
        return best_category, confidence
