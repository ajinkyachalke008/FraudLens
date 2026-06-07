"""
Dormancy Detector — Detects inactive accounts that suddenly become active.
Flags: >90 days of inactivity followed by burst of transactions.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DormancyDetector:
    DORMANCY_THRESHOLD_DAYS = 90
    BURST_THRESHOLD_TXNS = 5  # 5+ txns after dormancy = suspicious

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)

            # Recent activity (last 7 days)
            recent_result = await db.execute(
                select(func.count(Transaction.id)).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= week_ago
                )
            )
            recent_count = int(recent_result.scalar() or 0)

            if recent_count == 0:
                self._evidence = {"recent_txns": 0, "triggered": False}
                return 0.0

            # Find the transaction before the recent burst
            pre_burst_result = await db.execute(
                select(func.max(Transaction.timestamp)).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp < week_ago
                )
            )
            last_pre_burst = pre_burst_result.scalar()

            if not last_pre_burst:
                # No history before this week — could be new account
                self._evidence = {
                    "recent_txns": recent_count,
                    "dormancy_days": None,
                    "is_new_account": True,
                    "triggered": False
                }
                return 0.1  # Slight risk for brand new accounts with activity

            # Calculate dormancy gap
            dormancy_days = (week_ago - last_pre_burst).days

            if dormancy_days < self.DORMANCY_THRESHOLD_DAYS:
                self._evidence = {
                    "recent_txns": recent_count,
                    "dormancy_days": dormancy_days,
                    "triggered": False
                }
                return 0.0

            # Score: longer dormancy + more recent activity = higher risk
            dormancy_factor = min(dormancy_days / (self.DORMANCY_THRESHOLD_DAYS * 3), 1.0)
            burst_factor = min(recent_count / (self.BURST_THRESHOLD_TXNS * 2), 1.0)
            final = (dormancy_factor * 0.6 + burst_factor * 0.4)

            self._evidence = {
                "recent_txns_7d": recent_count,
                "dormancy_days": dormancy_days,
                "last_activity_before_burst": last_pre_burst.isoformat(),
                "triggered": final > 0.4
            }
            return round(min(final, 1.0), 3)

        except Exception as e:
            logger.warning(f"DormancyDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
