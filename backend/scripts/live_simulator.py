import asyncio
import aiohttp
import random
import time
import uuid

# Pune coordinates
PUNE_LAT = 18.5204
PUNE_LNG = 73.8567

async def simulate_investment_scam(session, target_account="UPI-SCAM-999"):
    """
    Simulates a classic Investment Scam:
    1. Small "test" transaction.
    2. Medium transaction.
    3. Large "draining" transaction.
    """
    victim_account = f"ACC-VICTIM-{random.randint(1000, 9999)}"
    victim_lat = PUNE_LAT + random.uniform(-0.1, 0.1)
    victim_lng = PUNE_LNG + random.uniform(-0.1, 0.1)
    
    suspect_lat = 19.0760 + random.uniform(-0.05, 0.05) # Suspect in Mumbai
    suspect_lng = 72.8777 + random.uniform(-0.05, 0.05)
    
    amounts = [5000.0, 50000.0, 250000.0]
    
    print(f"[*] Starting Investment Scam simulation for victim {victim_account} -> {target_account}")
    
    for idx, amount in enumerate(amounts):
        payload = {
            "transaction_ref": f"SIM-{uuid.uuid4().hex[:8]}",
            "from_account": victim_account,
            "to_account": target_account,
            "amount": amount,
            "currency": "INR",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "transaction_type": "UPI",
            "status": "COMPLETED",
            "src_lat": victim_lat,
            "src_lng": victim_lng,
            "dst_lat": suspect_lat,
            "dst_lng": suspect_lng,
            "hour_of_day": int(time.strftime("%H", time.gmtime())),
            "velocity_1h": idx + 1,
            "velocity_24h": idx + 2
        }
        
        try:
            async with session.post('http://127.0.0.1:8001/api/v1/ingest/transaction', json=payload) as response:
                if response.status == 200:
                    print(f"  [+] Sent ₹{amount} from {victim_account} -> {target_account}")
                else:
                    print(f"  [-] Failed: {await response.text()}")
        except Exception as e:
            print(f"  [!] Connection error: {e}")
            
        await asyncio.sleep(random.uniform(2.0, 5.0)) # Wait 2-5 seconds between steps

async def main():
    print("========================================")
    print("FRAUDLENS AUTONOMOUS SIMULATOR ONLINE")
    print("========================================")
    
    async with aiohttp.ClientSession() as session:
        while True:
            # Spawn a new victim falling for an investment scam
            target_suspect = f"UPI-SCAM-{random.choice(['ALPHA', 'BETA', 'GAMMA'])}"
            asyncio.create_task(simulate_investment_scam(session, target_suspect))
            
            # Wait 10-20 seconds before another victim falls for it
            await asyncio.sleep(random.uniform(10.0, 20.0))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
