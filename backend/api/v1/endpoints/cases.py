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

    # Get the old case status for the audit log
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        return {"error": "Case not found"}, 404
        
    old_status = case.status

    await db.execute(
        update(Case).where(Case.id == case_id).values(status=status)
    )
    
    # Create Audit Log
    from models.sql.audit import AuditLog
    audit_log = AuditLog(
        entity_type="case",
        entity_id=str(case_id),
        actor_id=current_user.id,
        action="STATUS_CHANGED",
        metadata_blob={"old_status": old_status, "new_status": status}
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": f"Case {case_id} status updated to '{status}'"}

from pydantic import BaseModel
class CaseNoteCreate(BaseModel):
    content: str
    note_type: str = "general"

@router.post("/{case_id}/notes")
async def add_case_note(
    case_id: UUID,
    note_in: CaseNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models.sql.case_note import CaseNote
    from models.sql.audit import AuditLog
    
    new_note = CaseNote(
        case_id=case_id,
        author_id=current_user.id,
        content=note_in.content,
        note_type=note_in.note_type
    )
    db.add(new_note)
    
    # Audit trail for notes
    audit_log = AuditLog(
        entity_type="case",
        entity_id=str(case_id),
        actor_id=current_user.id,
        action="NOTE_ADDED",
        metadata_blob={"note_type": note_in.note_type}
    )
    db.add(audit_log)
    
    await db.commit()
    return {"message": "Case note added successfully"}

@router.get("/{case_id}/timeline")
async def get_case_timeline(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a unified, chronologically sorted timeline of CaseNotes and AuditLogs.
    """
    from models.sql.case_note import CaseNote
    from models.sql.audit import AuditLog
    
    # Fetch Notes
    notes_result = await db.execute(
        select(CaseNote, User.full_name)
        .outerjoin(User, CaseNote.author_id == User.id)
        .where(CaseNote.case_id == case_id)
    )
    notes = notes_result.all()
    
    # Fetch Audit Logs
    audit_result = await db.execute(
        select(AuditLog, User.full_name)
        .outerjoin(User, AuditLog.actor_id == User.id)
        .where(AuditLog.entity_id == str(case_id))
    )
    audits = audit_result.all()
    
    timeline = []
    
    for note, author_name in notes:
        timeline.append({
            "type": "note",
            "id": str(note.id),
            "content": note.content,
            "note_type": note.note_type,
            "author": author_name or "System",
            "timestamp": note.created_at.isoformat()
        })
        
    for audit, author_name in audits:
        timeline.append({
            "type": "audit",
            "id": str(audit.id),
            "action": audit.action,
            "metadata": audit.metadata_blob,
            "author": author_name or "System",
            "timestamp": audit.created_at.isoformat()
        })
        
    # Sort by timestamp ascending
    timeline.sort(key=lambda x: x["timestamp"])
    
@router.get("/{case_id}/spatial")
async def get_case_spatial_data(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns spatial coordinate representations for all entities linked to this case.
    Uses mock geocoding based on Pune/Mumbai for demonstration of live mapping.
    """
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    if not case_result.scalar_one_or_none():
        return {"error": "Case not found"}, 404

    txn_result = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
    transactions = txn_result.scalars().all()
    
    locations = []
    connections = []
    
    import random
    # Base coordinates for Pune (Victims) and Mumbai (Suspects)
    PUNE_BASE = [73.8567, 18.5204]
    MUMBAI_BASE = [72.8777, 19.0760]
    
    seen_accounts = set()
    
    for t in transactions:
        amount = float(t.amount)
        # Generate stable randomness based on account name
        src_seed = hash(t.from_account) % 1000 / 10000.0
        dst_seed = hash(t.to_account) % 1000 / 10000.0
        
        src_coord = [PUNE_BASE[0] + src_seed, PUNE_BASE[1] + src_seed]
        dst_coord = [MUMBAI_BASE[0] + dst_seed, MUMBAI_BASE[1] + dst_seed]
        
        if t.from_account not in seen_accounts:
            locations.append({"id": t.from_account, "name": t.from_account, "coordinates": src_coord, "type": "victim", "size": 50, "amount": amount})
            seen_accounts.add(t.from_account)
            
        if t.to_account not in seen_accounts:
            locations.append({"id": t.to_account, "name": t.to_account, "coordinates": dst_coord, "type": "suspect", "size": 100, "amount": amount})
            seen_accounts.add(t.to_account)
            
        connections.append({"source": src_coord, "target": dst_coord, "amount": amount})
        
    return {"locations": locations, "connections": connections}

@router.get("/{case_id}/graph")
async def get_case_graph_data(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns nodes and edges exclusively isolated to this case for the D3 Network Graph.
    """
    txn_result = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
    transactions = txn_result.scalars().all()
    
    nodes = []
    edges = []
    seen = set()
    
    for t in transactions:
        if t.from_account not in seen:
            nodes.append({"id": t.from_account, "label": t.from_account, "type": "victim", "riskScore": 0.1})
            seen.add(t.from_account)
        if t.to_account not in seen:
            nodes.append({"id": t.to_account, "label": t.to_account, "type": "suspect", "riskScore": 0.95})
            seen.add(t.to_account)
            
        edges.append({"source": t.from_account, "target": t.to_account, "amount": float(t.amount)})
        
    return {"nodes": nodes, "links": edges}
