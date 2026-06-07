"""
Rapid Succession Detector — Flags rapid-fire transaction bursts.
Detects multiple transactions within seconds or minutes of each other,
indicating automated/scripted fraud or panic cash-out operations.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RapidSuccessionDetector:
    """
    Detects transaction bursts with extremely short inter-transaction gaps.
    - 3+ txns within 5 minutes = suspicious
    - 5+ txns within 10 minutes = high risk
    - Sub-60-second gaps between txns = automated/scripted
    """

    BURST_WINDOW_MINUTES = 10
    MIN_BURST_COUNT = 3
    RAPID_GAP_SECONDS = 60  # Transactions less than 60s apart

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()
            day_ago = now - timedelta(hours=24)

            # Get all transaction timestamps in last 24h, ordered
            result = await db.execute(
                select(Transaction.timestamp, Transaction.amount).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= day_ago
                ).order_by(Transaction.timestamp.asc())
            )
            txn_data = [(row[0], float(row[1])) for row in result.all()]

            if len(txn_data) < self.MIN_BURST_COUNT:
                self._evidence = {"txn_count_24h": len(txn_data), "bursts_found": 0, "triggered": False}
                return 0.0

            # Find rapid-fire bursts
            bursts = []
            rapid_gaps = []
            current_burst = [txn_data[0]]

            for i in range(1, len(txn_data)):
                gap_seconds = (txn_data[i][0] - txn_data[i-1][0]).total_seconds()

                if gap_seconds <= self.BURST_WINDOW_MINUTES * 60:
                    current_burst.append(txn_data[i])
                else:
                    if len(current_burst) >= self.MIN_BURST_COUNT:
                        bursts.append(current_burst)
                    current_burst = [txn_data[i]]

                if gap_seconds <= self.RAPID_GAP_SECONDS and gap_seconds >= 0:
                    rapid_gaps.append(gap_seconds)

            # Don't forget the last burst
            if len(current_burst) >= self.MIN_BURST_COUNT:
                bursts.append(current_burst)

            # Score components
            burst_count = len(bursts)
            max_burst_size = max(len(b) for b in bursts) if bursts else 0
            rapid_gap_count = len(rapid_gaps)
            min_gap = min(rapid_gaps) if rapid_gaps else float('inf')

            # Total volume moved in bursts
            burst_volume = sum(sum(t[1] for t in b) for b in bursts)

            # Score calculation
            burst_score = min(burst_count / 3, 0.4)
            size_score = min(max_burst_size / 10, 0.3)
            rapid_score = min(rapid_gap_count / 8, 0.3)

            # Sub-10-second gaps = almost certainly automated
            automation_bonus = 0.0
            if min_gap < 10:
                automation_bonus = 0.2
            elif min_gap < 30:
                automation_bonus = 0.1

            final = min(burst_score + size_score + rapid_score + automation_bonus, 1.0)

            self._evidence = {
                "txn_count_24h": len(txn_data),
                "bursts_found": burst_count,
                "max_burst_size": max_burst_size,
                "rapid_gap_count": rapid_gap_count,
                "min_gap_seconds": round(min_gap, 1) if min_gap != float('inf') else None,
                "burst_volume": round(burst_volume, 2),
                "possibly_automated": min_gap < 30 if min_gap != float('inf') else False,
                "triggered": final > 0.3
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"RapidSuccessionDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
