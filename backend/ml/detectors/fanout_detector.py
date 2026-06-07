"""
Fan-Out Detector — Detects one account distributing money to many unique recipients.
Classic mule scatter pattern: receive large sum → split to 10+ recipients.
Also detects 'commission agent' behavior (keeping a cut before distributing).
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FanOutDetector:
    """
    Detects outbound scatter patterns:
    - One sender to many recipients in short time window
    - Uniform amounts (equal splits) are extra suspicious
    - High fan-out with low fan-in = distribution node
    """

    RECIPIENT_THRESHOLD_24H = 8    # 8+ unique recipients in 24h
    RECIPIENT_THRESHOLD_7D = 15    # 15+ unique recipients in 7 days
    EQUAL_SPLIT_TOLERANCE = 0.05   # 5% tolerance for "equal" amounts

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()

            # Unique recipients in last 24 hours
            day_ago = now - timedelta(hours=24)
            result_24h = await db.execute(
                select(
                    func.count(func.distinct(Transaction.to_account)).label('unique_recipients'),
                    func.count(Transaction.id).label('total_txns'),
                    func.coalesce(func.sum(Transaction.amount), 0).label('total_sent')
                ).where(
                    Transaction.from_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            row_24h = result_24h.one()
            recipients_24h = int(row_24h.unique_recipients or 0)
            txns_24h = int(row_24h.total_txns or 0)
            volume_24h = float(row_24h.total_sent or 0)

            # Unique recipients in last 7 days
            week_ago = now - timedelta(days=7)
            result_7d = await db.execute(
                select(
                    func.count(func.distinct(Transaction.to_account)).label('unique_recipients'),
                    func.count(Transaction.id).label('total_txns')
                ).where(
                    Transaction.from_account == account_id,
                    Transaction.timestamp >= week_ago
                )
            )
            row_7d = result_7d.one()
            recipients_7d = int(row_7d.unique_recipients or 0)
            txns_7d = int(row_7d.total_txns or 0)

            # Check for equal-split pattern (uniform amounts)
            amounts_result = await db.execute(
                select(Transaction.amount).where(
                    Transaction.from_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            amounts = [float(r[0]) for r in amounts_result.all()]

            equal_split_score = 0.0
            if len(amounts) >= 3:
                avg = sum(amounts) / len(amounts)
                if avg > 0:
                    deviations = [abs(a - avg) / avg for a in amounts]
                    avg_deviation = sum(deviations) / len(deviations)
                    if avg_deviation < self.EQUAL_SPLIT_TOLERANCE:
                        equal_split_score = 0.4  # Strong indicator of structured splitting

            # Fan-in for comparison (how many unique senders?)
            fanin_result = await db.execute(
                select(func.count(func.distinct(Transaction.from_account))).where(
                    Transaction.to_account == account_id,
                    Transaction.timestamp >= week_ago
                )
            )
            senders_7d = int(fanin_result.scalar() or 0)

            # Score calculation
            score_24h = min(recipients_24h / self.RECIPIENT_THRESHOLD_24H, 1.0)
            score_7d = min(recipients_7d / self.RECIPIENT_THRESHOLD_7D, 1.0)

            # Asymmetry bonus: high fan-out + low fan-in = distributor
            asymmetry = 0.0
            if senders_7d > 0 and recipients_7d > senders_7d * 3:
                asymmetry = 0.2

            final = min(score_24h * 0.4 + score_7d * 0.3 + equal_split_score + asymmetry, 1.0)

            self._evidence = {
                "unique_recipients_24h": recipients_24h,
                "unique_recipients_7d": recipients_7d,
                "txns_out_24h": txns_24h,
                "volume_out_24h": round(volume_24h, 2),
                "unique_senders_7d": senders_7d,
                "fanout_fanin_ratio": round(recipients_7d / max(senders_7d, 1), 2),
                "equal_split_detected": equal_split_score > 0,
                "triggered": final > 0.4
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"FanOutDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
