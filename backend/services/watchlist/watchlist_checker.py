"""
Watchlist Checker — Check any account against both blacklist and watchlist.
Used by the streaming pipeline and alert engine for real-time checks.
"""
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.sql.blacklist import Blacklist, Watchlist
from models.schemas.watchlist_schemas import AccountCheckResult

logger = logging.getLogger(__name__)


async def check_account(db: AsyncSession, account_id: str) -> AccountCheckResult:
    """Check if a single account is blacklisted or watched."""
    # Check blacklist
    bl_result = await db.execute(
        select(Blacklist).where(
            Blacklist.account_id == account_id,
            Blacklist.is_active == True
        )
    )
    bl_entry = bl_result.scalar_one_or_none()

    # Check watchlist
    wl_result = await db.execute(
        select(Watchlist).where(Watchlist.account_id == account_id)
    )
    wl_entry = wl_result.scalar_one_or_none()

    return AccountCheckResult(
        account_id=account_id,
        is_blacklisted=bl_entry is not None,
        blacklist_reason=bl_entry.reason if bl_entry else None,
        blacklist_date=bl_entry.added_at if bl_entry else None,
        is_watched=wl_entry is not None,
        watch_level=wl_entry.watch_level if wl_entry else None,
        watch_reason=wl_entry.reason if wl_entry else None,
    )


async def bulk_check(
    db: AsyncSession,
    account_ids: List[str]
) -> List[AccountCheckResult]:
    """Check multiple accounts against blacklist and watchlist."""
    results = []
    for acc_id in account_ids:
        result = await check_account(db, acc_id)
        results.append(result)
    return results
