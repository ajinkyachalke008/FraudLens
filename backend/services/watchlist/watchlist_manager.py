"""
Watchlist Manager — CRUD operations for accounts under surveillance.
Supports watch levels (PASSIVE/ACTIVE/URGENT) and review scheduling.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from models.sql.blacklist import Watchlist

logger = logging.getLogger(__name__)


async def add_to_watchlist(
    db: AsyncSession,
    account_id: str,
    reason: str,
    watch_level: str = "PASSIVE",
    added_by: Optional[uuid.UUID] = None,
    assigned_investigator: Optional[uuid.UUID] = None,
    review_date=None,
    notes: Optional[str] = None,
    source: str = "manual",
    source_account_id: Optional[str] = None,
) -> Watchlist:
    """Add an account to the watchlist. Updates if already exists."""
    # Check existing
    result = await db.execute(
        select(Watchlist).where(Watchlist.account_id == account_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update to higher watch level if needed
        level_order = {"PASSIVE": 0, "ACTIVE": 1, "URGENT": 2}
        if level_order.get(watch_level, 0) > level_order.get(existing.watch_level, 0):
            existing.watch_level = watch_level
        existing.reason = f"{existing.reason}; {reason}"
        existing.updated_at = datetime.utcnow()
        if assigned_investigator:
            existing.assigned_investigator = assigned_investigator
        if notes:
            existing.notes = f"{existing.notes or ''}\n{notes}".strip()
        await db.commit()
        return existing

    entry = Watchlist(
        account_id=account_id,
        reason=reason,
        watch_level=watch_level,
        assigned_investigator=assigned_investigator,
        review_date=review_date,
        notes=notes,
        added_by=added_by,
        source=source,
        source_account_id=source_account_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    logger.info(f"Added {account_id} to watchlist (level={watch_level}, source={source})")
    return entry


async def update_watchlist_entry(
    db: AsyncSession,
    account_id: str,
    watch_level: Optional[str] = None,
    assigned_investigator: Optional[uuid.UUID] = None,
    review_date=None,
    notes: Optional[str] = None,
) -> Optional[Watchlist]:
    """Update an existing watchlist entry."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.account_id == account_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None

    if watch_level:
        entry.watch_level = watch_level
    if assigned_investigator:
        entry.assigned_investigator = assigned_investigator
    if review_date:
        entry.review_date = review_date
    if notes is not None:
        entry.notes = notes

    entry.updated_at = datetime.utcnow()
    await db.commit()
    return entry


async def remove_from_watchlist(db: AsyncSession, account_id: str) -> bool:
    """Remove an account from the watchlist."""
    result = await db.execute(
        delete(Watchlist).where(Watchlist.account_id == account_id)
    )
    await db.commit()
    return result.rowcount > 0


async def get_watchlist(
    db: AsyncSession,
    watch_level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> tuple:
    """Get paginated watchlist entries."""
    query = select(Watchlist).order_by(Watchlist.added_at.desc())
    if watch_level:
        query = query.where(Watchlist.watch_level == watch_level)

    count_query = select(func.count(Watchlist.id))
    if watch_level:
        count_query = count_query.where(Watchlist.watch_level == watch_level)
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.limit(limit).offset(offset))
    entries = result.scalars().all()
    return entries, total


async def is_watched(db: AsyncSession, account_id: str) -> Optional[Watchlist]:
    """Check if an account is on the watchlist."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.account_id == account_id)
    )
    return result.scalar_one_or_none()
