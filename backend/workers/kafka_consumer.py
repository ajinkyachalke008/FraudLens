import os
import json
import asyncio
from aiokafka import AIOKafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC = "live_transactions"

async def consume_events():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="fraudlens_workers",
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset="earliest"
    )
    
    print(f"Connecting to Kafka on {KAFKA_BOOTSTRAP_SERVERS}...")
    try:
        await consumer.start()
        print("Successfully connected to Kafka. Listening for events...")
    except Exception as e:
        print(f"Failed to start Kafka Consumer: {e}")
        return

    try:
        async for msg in consumer:
            payload = msg.value
            print(f"[Kafka Consumer] Processed transaction {payload.get('transaction_id')} for account {payload.get('from_account')}")
            # Here we would insert into PostgreSQL and Neo4j
            # Since the FastAPI app does this in live_streamer.py right now, this worker can handle heavy asynchronous processing
            # such as risk scoring or triggering OSINT APIs based on transaction patterns.
            
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_events())
