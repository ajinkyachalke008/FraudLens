class MockRedisClient:
    async def publish(self, channel: str, message: str):
        pass
        
    async def pubsub(self):
        class MockPubSub:
            async def subscribe(self, channel: str):
                pass
            async def listen(self):
                # infinite async generator that yields nothing
                import asyncio
                while True:
                    await asyncio.sleep(1)
                    yield None
        return MockPubSub()
        
    async def close(self):
        pass

async def get_redis_client():
    return MockRedisClient()
