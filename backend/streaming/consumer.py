import json
import logging
import time
import uuid
from datetime import datetime
from aiokafka import AIOKafkaConsumer

from core.database import AsyncSessionLocal
from sqlalchemy import select
from models.sql.transaction import Transaction
from models.sql.account import Account
from models.sql.case import Case
from streaming.producer import producer_client
from api.v1.endpoints.predict import (
    isolation_forest, syndicate_clustering, run_mock_gnn_inference, FraudExplainer
)
from core.pubsub import publish_alert
import pandas as pd

logger = logging.getLogger(__name__)

# Global streaming metrics for analytics dashboard
STREAM_METRICS = {
    "messages_processed": 0,
    "high_risk_flags": 0,
    "last_processed_time": None
}

# Deprecated in favor of Redis Pub/Sub, but keeping for backwards compatibility
broadcast_callback = None

async def archive_to_postgres(data: dict, is_fraud: bool, syndicate_id: str):
    """Sinks the scored transaction into the PostgreSQL cold-storage ledger."""
    async with AsyncSessionLocal() as session:
        try:
            # Upsert Accounts (query by account_number, NOT by UUID PK)
            source_result = await session.execute(
                select(Account).where(Account.account_number == data['source'])
            )
            if not source_result.scalar_one_or_none():
                session.add(Account(account_number=data['source'], bank_name="Unknown"))
                
            target_result = await session.execute(
                select(Account).where(Account.account_number == data['target'])
            )
            if not target_result.scalar_one_or_none():
                session.add(Account(account_number=data['target'], bank_name="Unknown"))
                
            # Auto-Generate Case for Critical Risk
            case_id = None
            if is_fraud:
                logger.warning(f"🚨 CRITICAL ALERT: Auto-generating Case for Syndicate {syndicate_id}")
                new_case = Case(
                    id=uuid.uuid4(),
                    title=f"Automated Alert: High-Risk Transfer detected in {syndicate_id}",
                    case_number=f"ALERT-{str(uuid.uuid4())[:8].upper()}",
                    status='open',
                    priority='critical',
                    description=f"AI Engine flagged transaction with critical risk. Suspect origin: {data['source']}.",
                    total_amount=data['amount'],
                    suspect_count=2
                )
                session.add(new_case)
                case_id = new_case.id

            # Insert Transaction
            txn = Transaction(
                id=uuid.uuid4(),
                transaction_ref=data.get('id', str(uuid.uuid4())),
                from_account=data['source'],
                to_account=data['target'],
                amount=data['amount'],
                timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) if 'timestamp' in data else datetime.utcnow(),
                transaction_type=data.get('transaction_type', 'TRANSFER'),
                risk_flag='critical' if is_fraud else 'low',
                case_id=case_id
            )
            session.add(txn)
            await session.commit()
            logger.info(f"💾 Archived {txn.transaction_ref} to DB (Risk: {txn.risk_flag})")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to archive to Postgres: {e}")

def set_broadcast_callback(func):
    global broadcast_callback
    broadcast_callback = func

async def process_transaction(data: dict):
    """Passes a raw transaction through the entire ML pipeline."""
    logger.info(f"Processing transaction: {data.get('id')}")
    global STREAM_METRICS
    try:
        # 1. Isolation Forest (Tabular Anomaly)
        df = pd.DataFrame([data])
        iso_results = isolation_forest.predict(df)[0]
        
        # 2. FraudSAGE GNN
        gnn_scores, embeddings = run_mock_gnn_inference(num_nodes=1)
        risk_score = float(gnn_scores[0]) if isinstance(gnn_scores, list) else float(gnn_scores)
        
        # 3. K-Means Syndicate
        node_embedding = embeddings[0] if isinstance(embeddings[0], list) else embeddings
        syndicate_id = syndicate_clustering.predict_syndicate(node_embedding)
        
        # 4. SHAP Explanation
        mock_features = {"degree_centrality": 15 if risk_score > 0.5 else 2, "amount": data.get("amount", 0)}
        explainer = FraudExplainer(model=None, feature_names=list(mock_features.keys()))
        explanation = explainer.generate_explanation(mock_features)
        
        # Update Metrics
        STREAM_METRICS["messages_processed"] += 1
        STREAM_METRICS["last_processed_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if explanation["total_risk_score"] > 0.6:
            STREAM_METRICS["high_risk_flags"] += 1
        
        # Formulate Intelligence Package
        scored_payload = {
            "type": "NEW_TRANSACTION",
            "data": {
                **data,
                "ai_analysis": {
                    "risk_score": explanation["total_risk_score"],
                    "is_fraud": explanation["total_risk_score"] > 0.6,
                    "confidence": 0.89,
                    "syndicate_id": f"SYN-{syndicate_id + 100}",
                    "explanation": explanation
                }
            }
        }
        
        # Archive to Cold Storage (Postgres)
        await archive_to_postgres(
            data=data, 
            is_fraud=explanation["total_risk_score"] > 0.6, 
            syndicate_id=f"SYN-{syndicate_id + 100}"
        )
        
        # Broadcast to WebSockets via Redis Pub/Sub
        await publish_alert("fraud_alerts", scored_payload)
        
        # Legacy callback for direct hooks if any
        if broadcast_callback:
            await broadcast_callback(scored_payload)
            
    except Exception as e:
        logger.error(f"Error processing transaction pipeline: {e}")

async def start_consumer(bootstrap_servers: str = "localhost:9092"):
    """Background worker that continuously polls for new transactions."""
    if producer_client.use_fallback:
        logger.info("Starting Queue Consumer (Fallback Mode)...")
        while True:
            msg = await producer_client.fallback_queue.get()
            if msg["topic"] == "fraudlens.transactions.raw":
                await process_transaction(msg["data"])
            producer_client.fallback_queue.task_done()
    else:
        try:
            consumer = AIOKafkaConsumer(
                "fraudlens.transactions.raw",
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id="fraudlens_ml_workers"
            )
            await consumer.start()
            logger.info("✅ Connected to Kafka Consumer.")
            try:
                async for msg in consumer:
                    await process_transaction(msg.value)
            finally:
                await consumer.stop()
        except Exception as e:
            logger.error(f"Kafka Consumer died: {e}")
