"""
Propagation Engine — When an account is blacklisted, automatically
adds linked accounts to the watchlist based on graph proximity.
1st-degree neighbors → URGENT watchlist
2nd-degree neighbors → PASSIVE watchlist
"""
import logging
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from models.sql.transaction import Transaction
from models.schemas.watchlist_schemas import PropagationResult
from services.watchlist.watchlist_manager import add_to_watchlist

logger = logging.getLogger(__name__)


async def propagate_blacklist(
    db: AsyncSession,
    account_id: str,
    added_by: Optional[uuid.UUID] = None,
    neo4j_driver=None
) -> PropagationResult:
    """
    Propagates blacklist status to linked accounts.
    Uses Neo4j for graph traversal when available, falls back to SQL.
    """
    first_degree = set()
    second_degree = set()

    if neo4j_driver:
        try:
            first_degree, second_degree = await _propagate_via_neo4j(
                account_id, neo4j_driver
            )
        except Exception as e:
            logger.warning(f"Neo4j propagation failed, falling back to SQL: {e}")
            first_degree, second_degree = await _propagate_via_sql(account_id, db)
    else:
        first_degree, second_degree = await _propagate_via_sql(account_id, db)

    # Remove the blacklisted account itself from results
    first_degree.discard(account_id)
    second_degree.discard(account_id)
    second_degree -= first_degree  # Don't double-add

    # Add 1st degree → URGENT
    first_count = 0
    for neighbor_id in first_degree:
        await add_to_watchlist(
            db=db,
            account_id=neighbor_id,
            reason=f"1st-degree link to blacklisted account {account_id}",
            watch_level="URGENT",
            added_by=added_by,
            source="propagation",
            source_account_id=account_id,
        )
        first_count += 1

    # Add 2nd degree → PASSIVE
    second_count = 0
    for neighbor_id in second_degree:
        await add_to_watchlist(
            db=db,
            account_id=neighbor_id,
            reason=f"2nd-degree link to blacklisted account {account_id}",
            watch_level="PASSIVE",
            added_by=added_by,
            source="propagation",
            source_account_id=account_id,
        )
        second_count += 1

    result = PropagationResult(
        source_account_id=account_id,
        first_degree_added=first_count,
        second_degree_added=second_count,
        total_watchlist_entries_created=first_count + second_count,
        investigators_notified=0  # TODO: integrate with alert system
    )

    logger.info(
        f"Propagation for {account_id}: "
        f"{first_count} URGENT + {second_count} PASSIVE watchlist entries"
    )
    return result


async def _propagate_via_neo4j(account_id: str, neo4j_driver) -> tuple:
    """Use Neo4j to find 1st and 2nd degree neighbors."""
    first_degree = set()
    second_degree = set()

    async with neo4j_driver.session() as session:
        # 1st degree
        result = await session.run("""
            MATCH (a:Account {accountNumber: $id})-[:SENT|RECEIVED]-(neighbor)
            RETURN neighbor.accountNumber AS acc
        """, id=account_id)
        records = await result.data()
        first_degree = {r["acc"] for r in records if r["acc"]}

        # 2nd degree
        result2 = await session.run("""
            MATCH (a:Account {accountNumber: $id})-[:SENT|RECEIVED*2]-(neighbor)
            WHERE neighbor.accountNumber <> $id
            RETURN DISTINCT neighbor.accountNumber AS acc
        """, id=account_id)
        records2 = await result2.data()
        second_degree = {r["acc"] for r in records2 if r["acc"]}

    return first_degree, second_degree


async def _propagate_via_sql(account_id: str, db: AsyncSession) -> tuple:
    """SQL fallback — find neighbors from transaction table."""
    first_degree = set()
    second_degree = set()

    # 1st degree: accounts directly transacting with blacklisted account
    result = await db.execute(
        select(Transaction.from_account, Transaction.to_account).where(
            or_(
                Transaction.from_account == account_id,
                Transaction.to_account == account_id
            )
        )
    )
    for row in result.all():
        if row[0] != account_id:
            first_degree.add(row[0])
        if row[1] != account_id:
            first_degree.add(row[1])

    # 2nd degree: accounts transacting with 1st degree neighbors
    if first_degree:
        result2 = await db.execute(
            select(Transaction.from_account, Transaction.to_account).where(
                or_(
                    Transaction.from_account.in_(first_degree),
                    Transaction.to_account.in_(first_degree)
                )
            ).limit(500)  # Limit to prevent explosion
        )
        for row in result2.all():
            second_degree.add(row[0])
            second_degree.add(row[1])

    return first_degree, second_degree
