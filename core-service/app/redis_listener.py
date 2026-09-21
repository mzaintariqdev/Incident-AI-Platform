import asyncio
import json

import redis.asyncio as aioredis

from app.config import settings
from app.ws import manager


async def listen_for_ticket_events():
    """Background task: listens on the 'ticket_events' Redis channel and
    forwards anything the ai-worker announces there to all connected
    WebSocket dashboard clients."""
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("ticket_events")

    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                await manager.broadcast(data)
            except Exception:
                pass