from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any

from core.database import get_db
from models.sql.case import Case
from models.sql.transaction import Transaction
from models.sql.user import User
from api.deps import get_current_user
from fastapi_cache.decorator import cache

router = APIRouter()

@router.get("/telemetry", response_model=Dict[str, Any])
@cache(expire=10)
async def get_dashboard_telemetry(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns global system telemetry for the Mission Control dashboard.
    """
    # 1. Total Value at Risk (Sum of all critical transaction amounts)
    val_query = await db.execute(
        select(func.sum(Transaction.amount)).where(Transaction.risk_flag == 'critical')
    )
    total_protected = val_query.scalar() or 0.0

    # 2. Total Cases Active
    case_query = await db.execute(
        select(func.count(Case.id)).where(Case.status == 'open')
    )
    active_cases = case_query.scalar() or 0

    # 3. Recent Alerts (Top 10 most recent critical cases)
    alerts_query = await db.execute(
        select(Case).order_by(Case.created_at.desc()).limit(10)
    )
    recent_alerts = alerts_query.scalars().all()
    
    formatted_alerts = [
        {
            "id": str(c.id),
            "case_number": c.case_number,
            "title": c.title,
            "status": c.status,
            "priority": c.priority,
            "amount": float(c.total_amount) if c.total_amount else 0.0,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in recent_alerts
    ]

    # Global Threat Level Calculation
    # Simple heuristic based on active cases
    if active_cases > 50:
        threat_level = "CRITICAL"
    elif active_cases > 10:
        threat_level = "ELEVATED"
    else:
        threat_level = "NOMINAL"

    return {
        "telemetry": {
            "threat_level": threat_level,
            "total_protected_value": float(total_protected),
            "active_cases": active_cases,
        },
        "recent_alerts": formatted_alerts
    }
