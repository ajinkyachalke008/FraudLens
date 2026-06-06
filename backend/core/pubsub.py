import json
import logging
from typing import AsyncGenerator
from core.cache import get_redis_client

logger = logging.getLogger(__name__)

async def publish_alert(channel: str, message: dict):
    """
    Publishes a JSON dictionary to the specified Redis channel.
    """
    try:
        client = await get_redis_client()
        await client.publish(channel, json.dumps(message))
    except Exception as e:
        logger.error(f"Failed to publish to Redis channel {channel}: {e}")

async def subscribe_alerts(channel: str) -> AsyncGenerator[dict, None]:
    """
    Subscribes to a Redis channel and yields JSON-decoded messages.
    """
    try:
        client = await get_redis_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield data
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from Redis channel {channel}")
    except Exception as e:
        logger.error(f"Redis subscription error on channel {channel}: {e}")
