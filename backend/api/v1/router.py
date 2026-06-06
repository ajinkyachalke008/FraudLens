from fastapi import APIRouter
from .endpoints import ingest, graph, predict, ml, websockets, dashboard, cases, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(predict.router, prefix="/predict", tags=["ml"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning Dashboard"])
api_router.include_router(websockets.router, tags=["WebSockets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Mission Control Dashboard"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case Management"])
