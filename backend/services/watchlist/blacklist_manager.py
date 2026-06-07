"""
Blacklist Manager — CRUD operations for confirmed fraud accounts.
Supports soft-delete to preserve audit trail.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from models.sql.blacklist import Blacklist

logger = logging.getLogger(__name__)


async def add_to_blacklist(
    db: AsyncSession,
    account_id: str,
    reason: str,
    added_by: uuid.UUID,
    case_id: Optional[uuid.UUID] = None,
    evidence_transaction_ids: Optional[str] = None,
    court_order_ref: Optional[str] = None,
) -> Blacklist:
    """Add an account to the blacklist. Reactivates if previously deactivated."""
    # Check existing
    result = await db.execute(
        select(Blacklist).where(Blacklist.account_id == account_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.is_active:
            return existing  # Already blacklisted
        # Reactivate
        existing.is_active = True
        existing.reason = reason
        existing.added_by = added_by
        existing.added_at = datetime.utcnow()
        existing.deactivated_at = None
        existing.deactivated_by = None
        existing.deactivation_reason = None
        existing.propagation_complete = False
        if case_id:
            existing.case_reference = case_id
        if evidence_transaction_ids:
            existing.evidence_transaction_ids = evidence_transaction_ids
        if court_order_ref:
            existing.court_order_ref = court_order_ref
        await db.commit()
        logger.info(f"Reactivated blacklist entry for {account_id}")
        return existing

    entry = Blacklist(
        account_id=account_id,
        reason=reason,
        added_by=added_by,
        case_reference=case_id,
        evidence_transaction_ids=evidence_transaction_ids,
        court_order_ref=court_order_ref,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    logger.info(f"Blacklisted account {account_id}: {reason}")
    return entry


async def remove_from_blacklist(
    db: AsyncSession,
    account_id: str,
    deactivated_by: uuid.UUID,
    reason: str = "Manual removal"
) -> bool:
    """Soft-delete a blacklist entry (preserves audit trail)."""
    result = await db.execute(
        select(Blacklist).where(
            Blacklist.account_id == account_id,
            Blacklist.is_active == True
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        return False

    entry.is_active = False
    entry.deactivated_at = datetime.utcnow()
    entry.deactivated_by = deactivated_by
    entry.deactivation_reason = reason
    await db.commit()
    logger.info(f"Deactivated blacklist entry for {account_id}")
    return True


async def get_blacklist(
    db: AsyncSession,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0
) -> tuple:
    """Get paginated blacklist entries."""
    query = select(Blacklist).order_by(Blacklist.added_at.desc())
    if active_only:
        query = query.where(Blacklist.is_active == True)

    from sqlalchemy import func
    count_query = select(func.count(Blacklist.id))
    if active_only:
        count_query = count_query.where(Blacklist.is_active == True)
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.limit(limit).offset(offset))
    entries = result.scalars().all()
    return entries, total


async def is_blacklisted(db: AsyncSession, account_id: str) -> Optional[Blacklist]:
    """Check if an account is actively blacklisted."""
    result = await db.execute(
        select(Blacklist).where(
            Blacklist.account_id == account_id,
            Blacklist.is_active == True
        )
    )
    return result.scalar_one_or_none()


async def mark_bank_notified(db: AsyncSession, account_id: str) -> bool:
    """Mark that the bank has been notified about this blacklisted account."""
    await db.execute(
        update(Blacklist).where(
            Blacklist.account_id == account_id
        ).values(
            bank_notified=True,
            bank_notification_date=datetime.utcnow()
        )
    )
    await db.commit()
    return True
