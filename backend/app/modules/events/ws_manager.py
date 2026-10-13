"""
Stage 9: Real-Time WebSocket Connection Manager for Kafka Event Streaming.
Broadcasts live recovery milestones and Kafka topic events to connected frontend clients:
- "Flight delay detected"
- "Train connection affected"
- "Searching alternatives"
- "Optimization completed"
- "Train rebooked"
- "Hotel updated"
- "Traveler notified"
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import WebSocket
from app.core.logger import logger


class WebSocketConnectionManager:
    """
    Manages active WebSocket clients and broadcasts Kafka event updates in real time.
    Thread-safe and async-compatible (works seamlessly from both sync and async contexts).
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.live_milestones: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")
        # Send welcome handshake + recent milestones
        await websocket.send_json({
            "type": "WS_CONNECTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to Kafka Event-Driven Recovery Stream",
            "recent_milestones": self.live_milestones[-25:],
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast_async(self, payload: Dict[str, Any]):
        """Broadcasts a JSON frame to all connected WebSocket clients."""
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(payload)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    def broadcast_event(self, event_dict: Dict[str, Any]):
        """
        Records a real-time milestone and dispatches it to all connected WebSocket clients.
        Can be called safely from synchronous or asynchronous code.
        """
        ui_message = event_dict.get("ui_message") or ""
        milestone_frame = {
            "type": "KAFKA_EVENT",
            "event_id": event_dict.get("event_id"),
            "correlation_id": event_dict.get("correlation_id"),
            "causation_id": event_dict.get("causation_id"),
            "topic": event_dict.get("topic"),
            "event_type": event_dict.get("event_type"),
            "producer": event_dict.get("producer"),
            "timestamp": event_dict.get("timestamp"),
            "partition": event_dict.get("partition", 0),
            "offset": event_dict.get("offset", 0),
            "retry_count": event_dict.get("retry_count", 0),
            "ui_message": ui_message,
            "payload": event_dict.get("payload", {}),
        }
        self.live_milestones.append(milestone_frame)
        # Keep bounded history
        if len(self.live_milestones) > 200:
            self.live_milestones = self.live_milestones[-200:]

        if not self.active_connections:
            return

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast_async(milestone_frame))
        except RuntimeError:
            # Running in a worker thread (e.g., sync FastAPI endpoint or background thread)
            try:
                asyncio.run(self.broadcast_async(milestone_frame))
            except Exception:
                pass

    def clear_milestones(self):
        self.live_milestones.clear()


ws_manager = WebSocketConnectionManager()
