from fastapi import APIRouter
from .endpoints import ingest, graph, predict, ml, websockets, dashboard, cases, auth
from .endpoints import ingest_multi, intelligence, watchlist, patterns, shared_entities, alerts, reports, enrichment

api_router = APIRouter()

# ──── Existing Routers ─────────────────────────────────────────
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(predict.router, prefix="/predict", tags=["ml"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning Dashboard"])
api_router.include_router(websockets.router, tags=["WebSockets"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Mission Control Dashboard"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case Management"])

# ──── Phase 1: New Routers ─────────────────────────────────────
api_router.include_router(ingest_multi.router, prefix="/ingest", tags=["Multi-Format Ingestion"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Risk Intelligence"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Blacklist & Watchlist"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(enrichment.router, prefix="/enrichment", tags=["Enrichment"])

# ──── Phase 2: Intelligence Layer ─────────────────────────────
api_router.include_router(patterns.router, prefix="/patterns", tags=["Pattern Analysis"])
api_router.include_router(shared_entities.router, prefix="/entities", tags=["Shared Entities"])

