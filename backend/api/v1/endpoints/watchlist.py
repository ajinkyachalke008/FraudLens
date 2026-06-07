"""
Blacklist & Watchlist API — Manage confirmed fraud accounts and
accounts under surveillance. Includes propagation and bulk checking.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.sql.user import User
from models.schemas.watchlist_schemas import (
    BlacklistEntry, BlacklistAddRequest, BlacklistResponse,
    WatchlistEntry, WatchlistAddRequest, WatchlistUpdateRequest, WatchlistResponse,
    AccountCheckResult, BulkCheckRequest, BulkCheckResponse, PropagationResult
)
from api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ──── Blacklist Endpoints ──────────────────────────────────────

@router.get("/blacklist", response_model=BlacklistResponse)
async def list_blacklist(
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all blacklisted accounts."""
    from services.watchlist.blacklist_manager import get_blacklist
    entries, total = await get_blacklist(db, active_only, limit, offset)

    return BlacklistResponse(
        entries=[_bl_to_schema(e) for e in entries],
        total=total
    )


@router.post("/blacklist", response_model=BlacklistEntry, status_code=201)
async def add_to_blacklist(
    body: BlacklistAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an account to the blacklist. Optionally propagates to linked accounts."""
    from services.watchlist.blacklist_manager import add_to_blacklist as bl_add

    entry = await bl_add(
        db=db,
        account_id=body.account_id,
        reason=body.reason,
        added_by=current_user.id,
        case_id=body.case_id,
        evidence_transaction_ids=body.evidence_transaction_ids,
    )

    # Propagate if requested
    if body.propagate:
        try:
            from services.watchlist.propagation_engine import propagate_blacklist
            await propagate_blacklist(db, body.account_id, added_by=current_user.id)
        except Exception as e:
            logger.warning(f"Propagation failed for {body.account_id}: {e}")

    return _bl_to_schema(entry)


@router.delete("/blacklist/{account_id}")
async def remove_from_blacklist(
    account_id: str,
    reason: str = Query("Manual removal"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft-delete a blacklist entry (preserves audit trail)."""
    from services.watchlist.blacklist_manager import remove_from_blacklist as bl_remove
    success = await bl_remove(db, account_id, current_user.id, reason)
    if not success:
        raise HTTPException(404, f"Account {account_id} not found in active blacklist")
    return {"message": f"Account {account_id} removed from blacklist", "account_id": account_id}


# ──── Watchlist Endpoints ──────────────────────────────────────

@router.get("/watch", response_model=WatchlistResponse)
async def list_watchlist(
    watch_level: Optional[str] = Query(None, description="PASSIVE | ACTIVE | URGENT"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all watched accounts."""
    from services.watchlist.watchlist_manager import get_watchlist
    entries, total = await get_watchlist(db, watch_level, limit, offset)

    return WatchlistResponse(
        entries=[_wl_to_schema(e) for e in entries],
        total=total
    )


@router.post("/watch", response_model=WatchlistEntry, status_code=201)
async def add_to_watchlist(
    body: WatchlistAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an account to the watchlist."""
    from services.watchlist.watchlist_manager import add_to_watchlist as wl_add

    entry = await wl_add(
        db=db,
        account_id=body.account_id,
        reason=body.reason,
        watch_level=body.watch_level,
        added_by=current_user.id,
        assigned_investigator=body.assigned_investigator,
        review_date=body.review_date,
        notes=body.notes,
    )
    return _wl_to_schema(entry)


@router.patch("/watch/{account_id}", response_model=WatchlistEntry)
async def update_watchlist(
    account_id: str,
    body: WatchlistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a watchlist entry."""
    from services.watchlist.watchlist_manager import update_watchlist_entry

    entry = await update_watchlist_entry(
        db, account_id,
        watch_level=body.watch_level,
        assigned_investigator=body.assigned_investigator,
        review_date=body.review_date,
        notes=body.notes,
    )
    if not entry:
        raise HTTPException(404, f"Account {account_id} not found in watchlist")
    return _wl_to_schema(entry)


@router.delete("/watch/{account_id}")
async def remove_from_watchlist(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an account from the watchlist."""
    from services.watchlist.watchlist_manager import remove_from_watchlist as wl_remove
    success = await wl_remove(db, account_id)
    if not success:
        raise HTTPException(404, f"Account {account_id} not found in watchlist")
    return {"message": f"Account {account_id} removed from watchlist"}


# ──── Account Check Endpoints ──────────────────────────────────

@router.get("/check/{account_id}", response_model=AccountCheckResult)
async def check_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if an account is blacklisted or watched."""
    from services.watchlist.watchlist_checker import check_account as wl_check
    return await wl_check(db, account_id)


@router.post("/bulk-check", response_model=BulkCheckResponse)
async def bulk_check_accounts(
    body: BulkCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check multiple accounts against blacklist and watchlist."""
    from services.watchlist.watchlist_checker import bulk_check
    results = await bulk_check(db, body.account_ids)
    return BulkCheckResponse(
        results=results,
        blacklisted_count=sum(1 for r in results if r.is_blacklisted),
        watched_count=sum(1 for r in results if r.is_watched),
    )


# ──── Helpers ──────────────────────────────────────────────────

def _bl_to_schema(entry) -> BlacklistEntry:
    return BlacklistEntry(
        id=entry.id,
        account_id=entry.account_id,
        reason=entry.reason,
        evidence_transaction_ids=entry.evidence_transaction_ids,
        added_by=entry.added_by,
        case_reference=entry.case_reference,
        is_active=entry.is_active,
        bank_notified=entry.bank_notified,
        bank_notification_date=entry.bank_notification_date,
        court_order_ref=entry.court_order_ref,
        propagation_complete=entry.propagation_complete,
        added_at=entry.added_at,
    )


def _wl_to_schema(entry) -> WatchlistEntry:
    return WatchlistEntry(
        id=entry.id,
        account_id=entry.account_id,
        reason=entry.reason,
        watch_level=entry.watch_level,
        assigned_investigator=entry.assigned_investigator,
        review_date=entry.review_date,
        notes=entry.notes,
        last_activity=entry.last_activity,
        source=entry.source,
        source_account_id=entry.source_account_id,
        added_by=entry.added_by,
        added_at=entry.added_at,
        updated_at=entry.updated_at,
    )
