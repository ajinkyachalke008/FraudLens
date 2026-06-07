"""
Fan-In Detector — Detects many unique senders paying into one account.
Classic victim-collection pattern: 10+ victims → 1 collection account.
Also detects 'honey pot' accounts used in investment/job scams.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FanInDetector:
    """
    Detects inbound collection patterns:
    - Many unique senders → one receiver in short window
    - Small uniform amounts from many senders (e.g., job scam registration fees)
    - New senders appearing rapidly (growing victim pool)
    """

    SENDER_THRESHOLD_24H = 8     # 8+ unique senders in 24h
    SENDER_THRESHOLD_7D = 20     # 20+ unique senders in 7 days
    SMALL_AMT_THRESHOLD = 25000  # Amounts below ₹25k from many senders = scam

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()

            # Unique senders in last 24 hours
            day_ago = now - timedelta(hours=24)
            result_24h = await db.execute(
                select(
                    func.count(func.distinct(Transaction.from_account)).label('unique_senders'),
                    func.count(Transaction.id).label('total_txns'),
                    func.coalesce(func.sum(Transaction.amount), 0).label('total_received'),
                    func.coalesce(func.avg(Transaction.amount), 0).label('avg_amount')
                ).where(
                    Transaction.to_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            row_24h = result_24h.one()
            senders_24h = int(row_24h.unique_senders or 0)
            txns_24h = int(row_24h.total_txns or 0)
            volume_24h = float(row_24h.total_received or 0)
            avg_amount_24h = float(row_24h.avg_amount or 0)

            # Unique senders in last 7 days
            week_ago = now - timedelta(days=7)
            result_7d = await db.execute(
                select(
                    func.count(func.distinct(Transaction.from_account)).label('unique_senders'),
                    func.count(Transaction.id).label('total_txns'),
                    func.coalesce(func.sum(Transaction.amount), 0).label('total_received')
                ).where(
                    Transaction.to_account == account_id,
                    Transaction.timestamp >= week_ago
                )
            )
            row_7d = result_7d.one()
            senders_7d = int(row_7d.unique_senders or 0)
            txns_7d = int(row_7d.total_txns or 0)
            volume_7d = float(row_7d.total_received or 0)

            # Sender growth rate (new senders appearing recently)
            two_weeks_ago = now - timedelta(days=14)
            result_prev = await db.execute(
                select(func.count(func.distinct(Transaction.from_account))).where(
                    Transaction.to_account == account_id,
                    Transaction.timestamp >= two_weeks_ago,
                    Transaction.timestamp < week_ago
                )
            )
            senders_prev_week = int(result_prev.scalar() or 0)
            growth_rate = (senders_7d - senders_prev_week) / max(senders_prev_week, 1)

            # Small-amount collection pattern (scam indicator)
            small_amt_score = 0.0
            if senders_7d >= 5 and avg_amount_24h > 0 and avg_amount_24h < self.SMALL_AMT_THRESHOLD:
                small_amt_score = min(senders_7d / 15, 0.3)  # More senders + small amounts = scam

            # Score calculation
            score_24h = min(senders_24h / self.SENDER_THRESHOLD_24H, 1.0)
            score_7d = min(senders_7d / self.SENDER_THRESHOLD_7D, 1.0)
            growth_bonus = min(max(growth_rate, 0) * 0.15, 0.2)

            final = min(score_24h * 0.35 + score_7d * 0.3 + small_amt_score + growth_bonus, 1.0)

            self._evidence = {
                "unique_senders_24h": senders_24h,
                "unique_senders_7d": senders_7d,
                "sender_growth_rate": round(growth_rate, 2),
                "txns_in_24h": txns_24h,
                "volume_in_24h": round(volume_24h, 2),
                "volume_in_7d": round(volume_7d, 2),
                "avg_amount": round(avg_amount_24h, 2),
                "small_amount_collection": small_amt_score > 0,
                "triggered": final > 0.4
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"FanInDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
