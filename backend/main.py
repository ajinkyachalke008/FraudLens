import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from core.database import init_db
from core.neo4j import init_neo4j
from api.v1.router import api_router
from streaming.producer import producer_client
from streaming.consumer import start_consumer
from fastapi_limiter import FastAPILimiter
from fastapi_cache import FastAPICache

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_neo4j()
    
    # Initialize In-Memory Cache (No Redis needed!)
    logger.info("Initializing In-Memory Cache...")
    from fastapi_cache.backends.inmemory import InMemoryBackend
    FastAPICache.init(InMemoryBackend(), prefix="fraudlens-cache")
    # Rate limiting disabled for Native Demo Mode
    
    # Initialize Kafka / Streaming Pipeline
    logger.info("Initializing Streaming Pipeline...")
    await producer_client.start()
    
    # Launch the consumer as a background asyncio task so it doesn't block FastAPI
    asyncio.create_task(start_consumer())
    
    print("FraudLens API starting up...")
    yield
    
    # Shutdown
    logger.info("Shutting down FraudLens API...")
    await producer_client.stop()
    print("FraudLens API shutting down...")

app = FastAPI(
    title="FraudLens API",
    description="Graph Neural Network-powered fraud investigation platform for Pune Police Cybercrime Cell",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "https://frontend-lemon-theta-90.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "online", "app": "FraudLens", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
