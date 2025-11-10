"""
Redis Pub/Sub Subscriber Service

Listens to Redis channels for real-time telematics updates and forwards them
to WebSocket connections. Replaces polling mechanism with push-based updates.
"""

import asyncio
import json
import structlog
from typing import Set, Optional, Dict
from datetime import datetime

from app.services.redis_client import get_redis_client
from app.services.websocket_manager import get_connection_manager

logger = structlog.get_logger()


class RedisSubscriber:
    """Subscribes to Redis channels and forwards messages to WebSocket connections."""

    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        self.running = False
        self.manager = get_connection_manager()
        self.subscribed_channels: Set[str] = set()
        self._task: Optional[asyncio.Task] = None
        self._last_subscription_update = 0

    async def start(self):
        """Start the Redis subscriber."""
        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("redis_subscriber_start_failed", reason="Redis not available")
            return

        # Create a separate Redis connection for pub/sub (required by redis-py)
        import redis
        from app.config import get_settings
        settings = get_settings()
        
        try:
            # Create dedicated connection for pub/sub
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=None  # No timeout for pub/sub
            )
            self.redis_client.ping()
            
            self.pubsub = self.redis_client.pubsub()
            self.running = True
            
            # Start listening task
            self._task = asyncio.create_task(self._listen_loop())
            
            logger.info("redis_subscriber_started")
        except Exception as e:
            logger.error("redis_subscriber_init_failed", error=str(e))
            self.running = False

    async def subscribe_to_driver(self, driver_id: str):
        """Subscribe to channels for a specific driver."""
        if not self.pubsub:
            return

        channels = [
            f"realtime:analysis:{driver_id}",
            f"realtime:pricing:{driver_id}",
            f"realtime:events:{driver_id}"
        ]

        for channel in channels:
            if channel not in self.subscribed_channels:
                self.pubsub.subscribe(channel)
                self.subscribed_channels.add(channel)
                logger.debug("subscribed_to_channel", channel=channel)

    async def unsubscribe_from_driver(self, driver_id: str):
        """Unsubscribe from channels for a specific driver."""
        if not self.pubsub:
            return

        channels = [
            f"realtime:analysis:{driver_id}",
            f"realtime:pricing:{driver_id}",
            f"realtime:events:{driver_id}"
        ]

        for channel in channels:
            if channel in self.subscribed_channels:
                self.pubsub.unsubscribe(channel)
                self.subscribed_channels.discard(channel)
                logger.debug("unsubscribed_from_channel", channel=channel)

    async def _listen_loop(self):
        """Main loop that listens for Redis messages."""
        if not self.pubsub:
            return

        logger.info("redis_listen_loop_started")

        try:
            while self.running:
                try:
                    # Get message from Redis (non-blocking with timeout)
                    # Run in executor since Redis operations are blocking
                    loop = asyncio.get_event_loop()
                    message = await loop.run_in_executor(
                        None,
                        lambda: self.pubsub.get_message(timeout=1.0, ignore_subscribe_messages=True)
                    )
                    
                    if message:
                        await self._handle_message(message)
                    
                    # Update subscriptions based on connected drivers (every 5 seconds)
                    import time
                    current_time = time.time()
                    if current_time - self._last_subscription_update > 5.0:
                        await self._update_subscriptions()
                        self._last_subscription_update = current_time
                    
                    # Small sleep to prevent tight loop
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error("redis_listen_error", error=str(e))
                    await asyncio.sleep(1)  # Wait before retrying

        except asyncio.CancelledError:
            logger.info("redis_listen_loop_cancelled")
        except Exception as e:
            logger.error("redis_listen_loop_failed", error=str(e))
        finally:
            if self.pubsub:
                self.pubsub.close()
            if self.redis_client:
                self.redis_client.close()
            logger.info("redis_subscriber_stopped")

    async def _handle_message(self, message: Dict):
        """Handle incoming Redis message and forward to WebSocket."""
        try:
            channel = message.get('channel')
            data = message.get('data')
            
            if not channel or not data:
                return

            # Parse message data
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                logger.warning("invalid_message_format", channel=channel)
                return

            # Extract driver_id from channel name
            # Channel format: "realtime:{type}:{driver_id}"
            parts = channel.split(':')
            if len(parts) < 3:
                return
            
            driver_id = parts[2]
            message_type = message_data.get('type')
            payload = message_data.get('data', {})

            # Forward to WebSocket based on message type
            if message_type == 'analysis':
                await self.manager.send_driving_update(driver_id, {
                    'risk_score': payload.get('risk_score'),
                    'safety_score': payload.get('safety_score'),
                    'behavior_metrics': payload.get('behavior_metrics', {})
                })
                
                # Send risk score update
                await self.manager.send_risk_score_update(driver_id, {
                    'risk_score': payload.get('risk_score'),
                    'safety_score': payload.get('safety_score')
                })
                
                # Send safety alerts if any
                if payload.get('safety_alerts'):
                    for alert in payload['safety_alerts']:
                        await self.manager.send_safety_alert(driver_id, alert)

            elif message_type == 'pricing':
                await self.manager.send_pricing_update(driver_id, payload)

            elif message_type == 'event':
                # Send raw event update (for immediate display)
                event_data = payload.get('data', {})
                analysis = payload.get('analysis', {})
                
                await self.manager.send_driving_update(driver_id, {
                    'risk_score': analysis.get('risk_score'),
                    'safety_score': analysis.get('safety_score'),
                    'behavior_metrics': {
                        **analysis.get('behavior_metrics', {}),
                        'current_speed': event_data.get('speed', 0),
                        'current_acceleration': event_data.get('acceleration', 0)
                    }
                })

            logger.debug(
                "message_forwarded",
                channel=channel,
                driver_id=driver_id,
                message_type=message_type
            )

        except Exception as e:
            logger.error("message_handling_failed", error=str(e), channel=channel)

    async def _update_subscriptions(self):
        """Update subscriptions based on currently connected drivers."""
        if not self.pubsub:
            return

        connected_drivers = self.manager.get_connected_drivers()
        
        # Subscribe to new drivers
        for driver_id in connected_drivers:
            await self.subscribe_to_driver(driver_id)
        
        # Unsubscribe from disconnected drivers (optional - keep subscriptions for reconnection)
        # This is optional since Redis pub/sub is lightweight

    async def stop(self):
        """Stop the subscriber."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("redis_subscriber_stopped")


# Global subscriber instance
_subscriber_instance: Optional[RedisSubscriber] = None


def get_subscriber() -> RedisSubscriber:
    """Get or create subscriber instance."""
    global _subscriber_instance
    if _subscriber_instance is None:
        _subscriber_instance = RedisSubscriber()
    return _subscriber_instance


async def start_redis_subscriber():
    """Start the Redis subscriber as a background task."""
    subscriber = get_subscriber()
    if not subscriber.running:
        await subscriber.start()

