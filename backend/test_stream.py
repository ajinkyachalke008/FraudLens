import asyncio
import aiohttp
import json
import random
import time

async def send_transaction(session, i):
    payload = {
        "id": f"txn_stream_{int(time.time())}_{i}",
        "amount": round(random.uniform(10.0, 50000.0), 2),
        "source": f"ACC-{random.randint(100, 200)}",
        "target": f"ACC-{random.randint(500, 600)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "transaction_type": "TRANSFER"
    }
    
    # We must match TransactionCreate schema which also needs velocity
    payload["hour_of_day"] = random.randint(0, 23)
    payload["velocity_1h"] = random.randint(1, 20)
    payload["velocity_24h"] = random.randint(1, 100)
    
    async with session.post('http://127.0.0.1:8000/api/v1/ingest/transaction', json=payload) as response:
        return await response.text()

async def main():
    print("Initiating Burst Stream of 10 Transactions...")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(10):
            tasks.append(asyncio.create_task(send_transaction(session, i)))
            await asyncio.sleep(0.5) # Slight delay to let websocket visualize clearly
            
        results = await asyncio.gather(*tasks)
        print("Burst Complete.")

if __name__ == "__main__":
    asyncio.run(main())
