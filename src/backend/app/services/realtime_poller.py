"""
Real-Time Poller Service (DEPRECATED - Use Redis Pub/Sub Instead)

This service polls Redis for updates. It's been replaced by redis_subscriber.py
which uses Redis pub/sub for push-based updates (lower latency, better performance).

Kept as fallback for backward compatibility.
"""

import asyncio
import json
import structlog
from typing import Dict, Optional

from app.services.redis_client import get_redis_client
from app.services.websocket_manager import get_connection_manager

logger = structlog.get_logger()


class RealTimePoller:
    """Polls Redis for updates and sends via WebSocket."""

    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize poller.
        
        Args:
            poll_interval: Seconds between polls
        """
        self.poll_interval = poll_interval
        self.running = False
        self.redis_client = get_redis_client()
        self.manager = get_connection_manager()

    async def start(self):
        """Start polling loop."""
        self.running = True
        logger.info("realtime_poller_started", interval=self.poll_interval)

        while self.running:
            try:
                await self._poll_and_broadcast()
            except Exception as e:
                logger.error("realtime_poller_error", error=str(e))

            await asyncio.sleep(self.poll_interval)

    async def _poll_and_broadcast(self):
        """Poll Redis and broadcast updates."""
        if not self.redis_client:
            return

        # Get all connected drivers
        connected_drivers = self.manager.get_connected_drivers()

        for driver_id in connected_drivers:
            try:
                # Get analysis update
                analysis_data = self.redis_client.get(f"realtime:analysis:{driver_id}")
                if analysis_data:
                    analysis = json.loads(analysis_data)
                    
                    # Send driving update
                    await self.manager.send_driving_update(driver_id, {
                        'risk_score': analysis.get('risk_score'),
                        'safety_score': analysis.get('safety_score'),
                        'behavior_metrics': analysis.get('behavior_metrics', {})
                    })

                    # Send safety alerts
                    if analysis.get('safety_alerts'):
                        for alert in analysis['safety_alerts']:
                            await self.manager.send_safety_alert(driver_id, alert)

                    # Send risk score update
                    await self.manager.send_risk_score_update(driver_id, {
                        'risk_score': analysis.get('risk_score'),
                        'safety_score': analysis.get('safety_score')
                    })

                # Get pricing update
                pricing_data = self.redis_client.get(f"realtime:pricing:{driver_id}")
                if pricing_data:
                    pricing = json.loads(pricing_data)
                    await self.manager.send_pricing_update(driver_id, pricing)

            except Exception as e:
                logger.warning("realtime_poll_error", driver_id=driver_id, error=str(e))

    def stop(self):
        """Stop polling."""
        self.running = False
        logger.info("realtime_poller_stopped")


# Global poller instance
_poller_instance: Optional[RealTimePoller] = None


def get_poller() -> RealTimePoller:
    """Get or create poller instance."""
    global _poller_instance
    if _poller_instance is None:
        _poller_instance = RealTimePoller()
    return _poller_instance


async def start_realtime_poller():
    """Start the real-time poller as a background task."""
    poller = get_poller()
    if not poller.running:
        asyncio.create_task(poller.start())

