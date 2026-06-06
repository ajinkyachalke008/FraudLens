import json
import asyncio
import logging
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

class StreamProducer:
    """
    Produces transactions to Kafka.
    If Kafka is unreachable (e.g. Docker down on Windows), it gracefully falls back
    to an in-memory asyncio.Queue so the UI can still be developed locally.
    """
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer = None
        self.fallback_queue: asyncio.Queue = None
        self.use_fallback = False

    async def start(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info("✅ Connected to Kafka Producer.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Kafka ({e}). Enabling memory queue fallback!")
            self.use_fallback = True
            self.fallback_queue = asyncio.Queue()

    async def stop(self):
        if self.producer and not self.use_fallback:
            await self.producer.stop()

    async def send_transaction(self, topic: str, data: dict):
        if self.use_fallback:
            # Fallback to internal queue
            await self.fallback_queue.put({"topic": topic, "data": data})
        else:
            try:
                await self.producer.send_and_wait(topic, data)
            except Exception as e:
                logger.error(f"Failed to send to Kafka: {e}")

# Global instance
producer_client = StreamProducer()
