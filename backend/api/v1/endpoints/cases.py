from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional
from uuid import UUID

from core.database import get_db
from models.sql.case import Case
from models.sql.transaction import Transaction
from models.sql.user import User
from api.deps import get_current_user, RoleChecker

router = APIRouter()

@router.get("/")
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by case status: open, closed, archived"),
    priority: Optional[str] = Query(None, description="Filter by priority: critical, high, medium, low"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a paginated list of cases, with optional status/priority filters.
    Used by the Mission Control Case Ledger.
    """
    query = select(Case).order_by(Case.created_at.desc())

    if status:
        query = query.where(Case.status == status)
    if priority:
        query = query.where(Case.priority == priority)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    cases = result.scalars().all()

    # Get total count for pagination
    count_query = select(func.count(Case.id))
    if status:
        count_query = count_query.where(Case.status == status)
    if priority:
        count_query = count_query.where(Case.priority == priority)
    total = (await db.execute(count_query)).scalar() or 0

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "cases": [
            {
                "id": str(c.id),
                "case_number": c.case_number,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "description": c.description,
                "total_amount": float(c.total_amount) if c.total_amount else 0.0,
                "victim_count": c.victim_count,
                "suspect_count": c.suspect_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in cases
        ]
    }

@router.get("/{case_id}")
async def get_case_detail(case_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns the full detail of a single case, including all linked transactions.
    """
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    
    if not case:
        return {"error": "Case not found"}, 404

    # Fetch linked transactions
    txn_result = await db.execute(
        select(Transaction).where(Transaction.case_id == case_id).order_by(Transaction.timestamp.desc())
    )
    transactions = txn_result.scalars().all()

    return {
        "case": {
            "id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "status": case.status,
            "priority": case.priority,
            "description": case.description,
            "total_amount": float(case.total_amount) if case.total_amount else 0.0,
            "victim_count": case.victim_count,
            "suspect_count": case.suspect_count,
            "created_at": case.created_at.isoformat() if case.created_at else None,
        },
        "linked_transactions": [
            {
                "id": str(t.id),
                "transaction_ref": t.transaction_ref,
                "from_account": t.from_account,
                "to_account": t.to_account,
                "amount": float(t.amount),
                "risk_flag": t.risk_flag,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            }
            for t in transactions
        ]
    }

@router.patch("/{case_id}/status")
async def update_case_status(
    case_id: UUID, 
    status: str = Query(...), 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "investigator"]))
):
    """
    Updates the status of a case (open → investigating → closed → archived).
    Used by investigators to manage alert lifecycle.
    """
    valid_statuses = ['open', 'investigating', 'closed', 'archived']
    if status not in valid_statuses:
        return {"error": f"Invalid status. Must be one of: {valid_statuses}"}, 400

    await db.execute(
        update(Case).where(Case.id == case_id).values(status=status)
    )
    await db.commit()
    return {"message": f"Case {case_id} status updated to '{status}'"}
