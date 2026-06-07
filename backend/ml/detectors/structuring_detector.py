"""
Structuring Detector — Detects sub-threshold 'smurfing' transactions.
Flags: 3+ transactions between ₹45,000-₹49,999 in the same day.
Classic below-₹50k reporting threshold evasion.
"""
import logging
from sqlalchemy import select, func, cast, Date, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StructuringDetector:
    THRESHOLD_MIN = 45000
    THRESHOLD_MAX = 49999
    MIN_COUNT = 3

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            result = await db.execute(
                select(
                    cast(Transaction.timestamp, Date).label("day"),
                    func.count(Transaction.id).label("cnt"),
                    func.sum(Transaction.amount).label("total")
                ).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.amount >= self.THRESHOLD_MIN,
                    Transaction.amount <= self.THRESHOLD_MAX
                ).group_by(cast(Transaction.timestamp, Date))
                .having(func.count(Transaction.id) >= self.MIN_COUNT)
            )
            suspicious_days = result.all()

            if not suspicious_days:
                self._evidence = {"suspicious_days": 0, "max_per_day": 0, "triggered": False}
                return 0.0

            max_count = max(row.cnt for row in suspicious_days)
            total_suspicious = sum(row.cnt for row in suspicious_days)
            score = min(max_count / (self.MIN_COUNT * 2), 1.0)

            self._evidence = {
                "suspicious_days": len(suspicious_days),
                "max_sub_threshold_txns_per_day": max_count,
                "total_suspicious_txns": total_suspicious,
                "range": f"₹{self.THRESHOLD_MIN:,}-₹{self.THRESHOLD_MAX:,}",
                "triggered": score > 0.4
            }
            return round(score, 3)

        except Exception as e:
            logger.warning(f"StructuringDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
