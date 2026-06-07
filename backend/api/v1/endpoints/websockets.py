from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
import logging
from streaming.consumer import STREAM_METRICS
from jose import jwt, JWTError
from core.security import SECRET_KEY, ALGORITHM
from core.pubsub import subscribe_alerts
from core.database import AsyncSessionLocal
from services.alerts.alert_engine import acknowledge_alert

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket Client connected. Active tabs: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket Client disconnected. Active tabs: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Failed to send to a websocket: {e}")

manager = ConnectionManager()

redis_task = None

async def redis_listener():
    logger.info("Starting Redis Pub/Sub listener for WebSockets...")
    async for message in subscribe_alerts("fraud_alerts"):
        await manager.broadcast_json(message)

@router.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    Persistent WebSocket connection for the Next.js Frontend.
    Pushes Live ML Scored Transactions immediately as they are processed.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise ValueError("Invalid token")
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await manager.connect(websocket)
    
    global redis_task
    if redis_task is None:
        redis_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ALERT_ACK":
                        alert_id = msg.get("alert_id")
                        if alert_id:
                            async with AsyncSessionLocal() as db:
                                await acknowledge_alert(alert_id, user_id, db)
                                await db.commit()
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/metrics")
async def get_stream_metrics():
    """Returns real-time streaming infrastructure health and throughput."""
    return {
        "active_websocket_clients": len(manager.active_connections),
        "messages_processed": STREAM_METRICS["messages_processed"],
        "high_risk_flags": STREAM_METRICS["high_risk_flags"],
        "last_processed_time": STREAM_METRICS["last_processed_time"]
    }
