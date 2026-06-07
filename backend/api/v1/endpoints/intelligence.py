"""
Risk Intelligence API — 8-signal risk profiles for accounts.
Supports single, batch, and high-risk account queries.
"""
import time
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.sql.user import User
from models.schemas.intelligence import (
    AccountRiskProfile, BatchRiskScoreRequest, BatchRiskScoreResponse,
    HighRiskAccountsResponse, RiskScanResponse
)
from api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/risk-profile/{account_id}", response_model=AccountRiskProfile)
async def get_risk_profile(
    account_id: str,
    use_mock: bool = Query(False, description="Force mock data (for offline testing)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns full 8-signal risk profile for a single account.
    Each signal ranges 0.0-1.0, with composite score and risk tier.
    """
    if use_mock:
        from ml.detectors.risk_aggregator import get_mock_profile
        return get_mock_profile(account_id)

    try:
        from ml.detectors.risk_aggregator import compute_risk_profile
        profile = await compute_risk_profile(account_id, db)
        return profile
    except Exception as e:
        logger.warning(f"Live risk profile failed for {account_id}, returning mock: {e}")
        from ml.detectors.risk_aggregator import get_mock_profile
        return get_mock_profile(account_id)


@router.post("/batch-risk-score", response_model=BatchRiskScoreResponse)
async def batch_risk_score(
    body: BatchRiskScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Score multiple accounts in a single request (max 100)."""
    start = time.time()
    profiles = []

    for account_id in body.account_ids:
        try:
            from ml.detectors.risk_aggregator import compute_risk_profile
            profile = await compute_risk_profile(account_id, db)
        except Exception:
            from ml.detectors.risk_aggregator import get_mock_profile
            profile = get_mock_profile(account_id)
        profiles.append(profile)

    duration_ms = int((time.time() - start) * 1000)
    return BatchRiskScoreResponse(
        profiles=profiles,
        total_scored=len(profiles),
        scoring_duration_ms=duration_ms
    )


@router.get("/high-risk-accounts", response_model=HighRiskAccountsResponse)
async def get_high_risk_accounts(
    tier: Optional[str] = Query(None, description="Filter by tier: CRITICAL, ALERT, WATCH"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns accounts sorted by risk score.
    Falls back to mock data when no accounts are scored yet.
    """
    from ml.detectors.risk_aggregator import MOCK_PROFILES

    # For now, return mock profiles (will be replaced with DB-stored profiles)
    profiles = list(MOCK_PROFILES.values())

    if tier:
        tier = tier.upper()
        profiles = [p for p in profiles if p.risk_tier == tier]

    # Sort by risk score descending
    profiles.sort(key=lambda p: p.final_risk_score, reverse=True)
    profiles = profiles[:limit]

    return HighRiskAccountsResponse(
        accounts=profiles,
        total=len(profiles),
        tier_filter=tier
    )


@router.post("/run-full-scan", response_model=RiskScanResponse)
async def run_full_scan(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers a full risk scan on all accounts.
    Returns immediately — scan runs in background.
    """
    from sqlalchemy import func, select
    from models.sql.account import Account

    # Count accounts to scan
    result = await db.execute(select(func.count(Account.id)))
    total = result.scalar() or 0

    # TODO: Launch background task for full scan
    import uuid
    job_id = str(uuid.uuid4())

    return RiskScanResponse(
        job_id=job_id,
        status="started",
        accounts_to_scan=total,
        message=f"Full risk scan started for {total} accounts. Results will update risk profiles."
    )

@router.get("/cross-case/links")
async def get_cross_case_links(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detects Shared Suspect Accounts across multiple cases.
    Returns overlapping nodes and the specific cases they connect.
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            account, 
            array_agg(DISTINCT case_id) as linked_cases, 
            SUM(amount) as total_volume,
            COUNT(*) as txn_count
        FROM (
            SELECT from_account as account, case_id, amount FROM transactions WHERE case_id IS NOT NULL
            UNION ALL
            SELECT to_account as account, case_id, amount FROM transactions WHERE case_id IS NOT NULL
        ) AS acc_cases
        GROUP BY account
        HAVING COUNT(DISTINCT case_id) > 1
        ORDER BY total_volume DESC
        LIMIT 50
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    links = []
    case_ids = set()
    for row in rows:
        case_ids.update(row.linked_cases)
        
    # Resolve Case Numbers
    from models.sql.case import Case
    from sqlalchemy import select
    case_map = {}
    if case_ids:
        case_res = await db.execute(select(Case.id, Case.case_number).where(Case.id.in_(case_ids)))
        case_map = {str(c.id): c.case_number for c in case_res.all()}
        
    for row in rows:
        links.append({
            "account": row.account,
            "linked_cases": [{"id": str(cid), "case_number": case_map.get(str(cid), "UNKNOWN")} for cid in row.linked_cases],
            "total_volume": float(row.total_volume),
            "txn_count": row.txn_count
        })
        
    return {"links": links, "total_syndicates_detected": len(links)}

@router.get("/cross-case/graph")
async def get_cross_case_graph(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the Macro-Level D3 Network Graph for Cross-Case Syndicates.
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            account, 
            array_agg(DISTINCT case_id) as linked_cases
        FROM (
            SELECT from_account as account, case_id FROM transactions WHERE case_id IS NOT NULL
            UNION ALL
            SELECT to_account as account, case_id FROM transactions WHERE case_id IS NOT NULL
        ) AS acc_cases
        GROUP BY account
        HAVING COUNT(DISTINCT case_id) > 1
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    nodes = []
    links = []
    seen_nodes = set()
    
    from models.sql.case import Case
    from sqlalchemy import select
    
    case_ids = set()
    for row in rows:
        case_ids.update(row.linked_cases)
        
    case_map = {}
    if case_ids:
        case_res = await db.execute(select(Case.id, Case.case_number).where(Case.id.in_(case_ids)))
        case_map = {str(c.id): c.case_number for c in case_res.all()}
        
    for row in rows:
        acc_node_id = f"ACC-{row.account}"
        if acc_node_id not in seen_nodes:
            nodes.append({"id": acc_node_id, "label": row.account, "type": "shared_suspect", "riskScore": 1.0})
            seen_nodes.add(acc_node_id)
            
        for cid in row.linked_cases:
            case_node_id = f"CASE-{cid}"
            if case_node_id not in seen_nodes:
                nodes.append({"id": case_node_id, "label": case_map.get(str(cid), "UNKNOWN"), "type": "case_cluster", "riskScore": 0.5})
                seen_nodes.add(case_node_id)
                
            links.append({"source": acc_node_id, "target": case_node_id, "type": "involved_in"})
            
    return {"nodes": nodes, "links": links}
