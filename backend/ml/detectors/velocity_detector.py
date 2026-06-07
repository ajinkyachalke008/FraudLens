"""
Velocity Detector — Detects high-speed transaction bursts.
Flags: >10 txns in 60 min, or total volume >5x 30-day avg in 24hrs.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class VelocityDetector:
    THRESHOLD_TXN_PER_HOUR = 10
    THRESHOLD_VOLUME_MULTIPLIER = 5

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        """Returns 0.0-1.0 velocity risk score."""
        from models.sql.transaction import Transaction

        now = datetime.utcnow()

        try:
            # Count & sum in last 1 hour
            hour_ago = now - timedelta(hours=1)
            result_1h = await db.execute(
                select(
                    func.count(Transaction.id),
                    func.coalesce(func.sum(Transaction.amount), 0)
                ).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= hour_ago
                )
            )
            count_1h, volume_1h = result_1h.one()
            count_1h = int(count_1h or 0)
            volume_1h = float(volume_1h or 0)

            # 30-day average daily volume
            month_ago = now - timedelta(days=30)
            result_30d = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= month_ago
                )
            )
            volume_30d = float(result_30d.scalar() or 0)
            avg_daily = volume_30d / 30 if volume_30d > 0 else 1.0

            # Score calculation
            velocity_score = min(count_1h / self.THRESHOLD_TXN_PER_HOUR, 1.0)
            volume_ratio = (volume_1h / avg_daily) / self.THRESHOLD_VOLUME_MULTIPLIER if avg_daily > 0 else 0
            volume_score = min(volume_ratio, 1.0)

            final = max(velocity_score, volume_score)

            self._evidence = {
                "txn_count_1h": count_1h,
                "volume_1h": volume_1h,
                "avg_daily_30d": round(avg_daily, 2),
                "volume_multiplier": round(volume_1h / avg_daily, 1) if avg_daily > 0 else 0,
                "triggered": final > 0.6
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"VelocityDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
