import os
import json
import asyncio
from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

class EventProducer:
    _producer: AIOKafkaProducer = None

    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        if cls._producer is None:
            cls._producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            # Try to start, but don't crash if Kafka isn't up during local dev without docker
            try:
                await cls._producer.start()
            except Exception as e:
                print(f"Failed to connect to Kafka: {e}")
                cls._producer = None
        return cls._producer

    @classmethod
    async def send_event(cls, topic: str, message: dict):
        producer = await cls.get_producer()
        if producer:
            try:
                await producer.send_and_wait(topic, message)
            except Exception as e:
                print(f"Error sending Kafka message: {e}")
        else:
            print(f"[MOCK KAFKA] Topic: {topic} | Message: {message}")

    @classmethod
    async def stop(cls):
        if cls._producer:
            await cls._producer.stop()
            cls._producer = None
