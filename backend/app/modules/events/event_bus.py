"""
Event Bus Module (Staged Architecture).
Will handle Apache Kafka consumer/producer for flight telemetry and disruption events.
"""
from typing import Dict, Any, Callable

class EventBusStub:
    """Mock/Stub event dispatcher prior to Kafka deployment."""
    def __init__(self):
        self._subscribers = {}
        self.published_events = []

    def publish(self, topic: str, message: Dict[str, Any]):
        event_record = {"topic": topic, "data": message}
        self.published_events.append(event_record)
        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception:
                pass

    def subscribe(self, topic: str, handler: Callable):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

event_bus = EventBusStub()
