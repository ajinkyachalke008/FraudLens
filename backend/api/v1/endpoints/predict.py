from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd

from ml.models.gnn import run_mock_gnn_inference
from ml.models.isolation_forest import TransactionAnomalyDetector
from ml.models.clustering import FraudSyndicateClustering
from ml.explainability.shap_explainer import FraudExplainer
from models.sql.user import User
from api.deps import get_current_user
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

router = APIRouter()
isolation_forest = TransactionAnomalyDetector()
syndicate_clustering = FraudSyndicateClustering()

class TransactionPayload(BaseModel):
    id: str
    amount: float
    hour_of_day: int
    velocity_1h: int
    velocity_24h: int

class PredictionResponse(BaseModel):
    target_id: str
    risk_score: float
    is_fraud: bool
    confidence: float
    explanation: dict
    syndicate_id: Optional[str] = None

@router.post("/transaction", response_model=PredictionResponse)
async def predict_transaction(payload: TransactionPayload, current_user: User = Depends(get_current_user)):
    """
    Runs Tabular Anomaly Detection (Isolation Forest) on a single transaction.
    """
    df = pd.DataFrame([payload.dict()])
    
    try:
        # Get Isolation Forest prediction
        results = isolation_forest.predict(df)
        result = results[0]
        
        # Get SHAP Explanation
        explainer = FraudExplainer(model=isolation_forest, feature_names=df.columns.tolist())
        explanation = explainer.generate_explanation(payload.dict())
        
        return {
            "target_id": payload.id,
            "risk_score": result["anomaly_risk_score"],
            "is_fraud": result["is_anomaly"],
            "confidence": 0.85 if result["is_anomaly"] else 0.95,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/account/{account_id}", response_model=PredictionResponse)
async def predict_account(account_id: str, current_user: User = Depends(get_current_user)):
    """
    Runs Graph Neural Network (FraudSAGE) inference on a specific account.
    (Currently uses mock tensors since Neo4j is offline).
    """
    try:
        # Run Mock PyTorch Inference
        gnn_scores, embeddings = run_mock_gnn_inference(num_nodes=1)
        risk_score = float(gnn_scores[0]) if isinstance(gnn_scores, list) else float(gnn_scores)
        
        # Predict Fraud Syndicate using Latent Embeddings
        # Extract the single node embedding from the batch [num_nodes, hidden_dims]
        node_embedding = embeddings[0] if isinstance(embeddings[0], list) else embeddings
        syndicate_id = syndicate_clustering.predict_syndicate(node_embedding)
        
        # Mock features for SHAP
        mock_features = {
            "degree_centrality": 15 if risk_score > 0.5 else 2,
            "velocity_1h": 8 if risk_score > 0.5 else 1,
            "amount": 250000 if risk_score > 0.5 else 10000
        }
        
        explainer = FraudExplainer(model=None, feature_names=list(mock_features.keys()))
        explanation = explainer.generate_explanation(mock_features)
        
        return {
            "target_id": account_id,
            "risk_score": explanation["total_risk_score"],
            "is_fraud": explanation["total_risk_score"] > 0.6,
            "confidence": 0.89,
            "explanation": explanation,
            "syndicate_id": f"SYN-{syndicate_id + 100}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
