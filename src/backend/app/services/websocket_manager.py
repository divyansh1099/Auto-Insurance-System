"""
WebSocket Manager for Real-Time Updates

Manages WebSocket connections for real-time driving behavior updates,
safety alerts, and dynamic pricing changes.
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import structlog
from datetime import datetime

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # driver_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> driver_id mapping
        self.connection_drivers: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, driver_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if driver_id not in self.active_connections:
            self.active_connections[driver_id] = set()
        
        self.active_connections[driver_id].add(websocket)
        self.connection_drivers[websocket] = driver_id
        
        logger.info("websocket_connected", driver_id=driver_id, total_connections=len(self.active_connections[driver_id]))

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        driver_id = self.connection_drivers.get(websocket)
        if driver_id:
            if driver_id in self.active_connections:
                self.active_connections[driver_id].discard(websocket)
                if not self.active_connections[driver_id]:
                    del self.active_connections[driver_id]
            del self.connection_drivers[websocket]
            
            logger.info("websocket_disconnected", driver_id=driver_id)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("websocket_send_error", error=str(e))
            self.disconnect(websocket)

    async def broadcast_to_driver(self, driver_id: str, message: dict):
        """Broadcast a message to all connections for a driver."""
        if driver_id not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[driver_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error("websocket_broadcast_error", driver_id=driver_id, error=str(e))
                disconnected.add(websocket)

        # Remove disconnected connections
        for ws in disconnected:
            self.disconnect(ws)

    async def send_driving_update(self, driver_id: str, update: dict):
        """Send real-time driving behavior update."""
        message = {
            'type': 'driving_update',
            'timestamp': datetime.utcnow().isoformat(),
            'data': update
        }
        await self.broadcast_to_driver(driver_id, message)

    async def send_safety_alert(self, driver_id: str, alert: dict):
        """Send safety alert to driver."""
        message = {
            'type': 'safety_alert',
            'timestamp': datetime.utcnow().isoformat(),
            'data': alert
        }
        await self.broadcast_to_driver(driver_id, message)

    async def send_pricing_update(self, driver_id: str, pricing: dict):
        """Send dynamic pricing update."""
        message = {
            'type': 'pricing_update',
            'timestamp': datetime.utcnow().isoformat(),
            'data': pricing
        }
        await self.broadcast_to_driver(driver_id, message)

    async def send_risk_score_update(self, driver_id: str, risk_data: dict):
        """Send risk score update."""
        message = {
            'type': 'risk_score_update',
            'timestamp': datetime.utcnow().isoformat(),
            'data': risk_data
        }
        await self.broadcast_to_driver(driver_id, message)

    def get_connected_drivers(self) -> Set[str]:
        """Get set of driver IDs with active connections."""
        return set(self.active_connections.keys())


# Global connection manager
_manager_instance: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create connection manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConnectionManager()
    return _manager_instance

