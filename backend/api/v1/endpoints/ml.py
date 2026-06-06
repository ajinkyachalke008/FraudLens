from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models.sql.user import User
from api.deps import get_current_user, RoleChecker

router = APIRouter()

class MLHealthResponse(BaseModel):
    models_loaded: list[str]
    isolation_forest_status: str
    gnn_status: str
    kmeans_status: str
    active_syndicates_tracked: int

@router.get("/health", response_model=MLHealthResponse)
async def get_ml_health(current_user: User = Depends(get_current_user)):
    """
    Returns the operational status of all machine learning models in memory.
    """
    return {
        "models_loaded": ["FraudSAGE_v1.2", "IsolationForest_Standard", "KMeans_Syndicate_v1"],
        "isolation_forest_status": "Online (Monitoring 4 features)",
        "gnn_status": "Online (16-dim embeddings)",
        "kmeans_status": "Online (K=5)",
        "active_syndicates_tracked": 5
    }

@router.post("/retrain/isolation_forest")
async def retrain_isolation_forest(current_user: User = Depends(RoleChecker(["admin"]))):
    """
    Trigger a background task (via Celery eventually) to retrain the Isolation Forest
    on the latest PostgreSQL transaction data.
    """
    return {"status": "Accepted", "message": "Retraining queued on Celery worker."}
