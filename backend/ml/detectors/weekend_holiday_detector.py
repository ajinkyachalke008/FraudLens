"""
Weekend & Holiday Detector — Flags unusual transaction activity on
weekends and Indian public holidays, when business accounts are normally dormant.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Indian national holidays (month, day) — approximate, doesn't vary much
INDIAN_HOLIDAYS = {
    (1, 26),   # Republic Day
    (3, 29),   # Holi (approx)
    (4, 14),   # Ambedkar Jayanti
    (4, 21),   # Ram Navami (approx)
    (5, 1),    # May Day
    (8, 15),   # Independence Day
    (10, 2),   # Gandhi Jayanti
    (10, 24),  # Dussehra (approx)
    (11, 1),   # Diwali (approx)
    (11, 15),  # Guru Nanak Jayanti (approx)
    (12, 25),  # Christmas
}


class WeekendHolidayDetector:
    """
    Detects abnormal weekend/holiday transaction patterns:
    - High-volume weekend transactions (when businesses are closed)
    - Activity on national holidays
    - Weekend-weekday ratio anomaly
    """

    WEEKEND_TXN_THRESHOLD = 5    # 5+ transactions on a single weekend day
    HOLIDAY_VOLUME_THRESHOLD = 100000  # ₹1L+ on a holiday

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()
            month_ago = now - timedelta(days=30)

            # Get transaction counts by day-of-week (0=Mon, 6=Sun)
            # PostgreSQL: 0=Sun, 1=Mon... but extract('dow') varies
            result = await db.execute(
                select(
                    extract('dow', Transaction.timestamp).label('dow'),
                    func.count(Transaction.id).label('cnt'),
                    func.coalesce(func.sum(Transaction.amount), 0).label('vol')
                ).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= month_ago
                ).group_by('dow')
            )
            dow_data = {int(row.dow): {'count': int(row.cnt), 'volume': float(row.vol)} for row in result.all()}

            if not dow_data:
                self._evidence = {"total_txns": 0, "triggered": False}
                return 0.0

            # Weekend activity (0=Sun, 6=Sat in PostgreSQL's DOW)
            weekend_count = dow_data.get(0, {}).get('count', 0) + dow_data.get(6, {}).get('count', 0)
            weekend_volume = dow_data.get(0, {}).get('volume', 0) + dow_data.get(6, {}).get('volume', 0)
            weekday_count = sum(dow_data.get(d, {}).get('count', 0) for d in range(1, 6))

            total_count = weekend_count + weekday_count
            weekend_ratio = weekend_count / total_count if total_count > 0 else 0

            # Normal weekend ratio is ~0.28 (2/7 days). Significantly higher = suspicious
            weekend_excess = max(weekend_ratio - 0.35, 0)

            # Holiday check
            holiday_txns = 0
            holiday_dates = set()
            for month, day in INDIAN_HOLIDAYS:
                holiday_result = await db.execute(
                    select(func.count(Transaction.id)).where(
                        or_(
                            Transaction.from_account == account_id,
                            Transaction.to_account == account_id
                        ),
                        extract('month', Transaction.timestamp) == month,
                        extract('day', Transaction.timestamp) == day
                    )
                )
                count = int(holiday_result.scalar() or 0)
                if count > 0:
                    holiday_txns += count
                    holiday_dates.add(f"{month:02d}-{day:02d}")

            # Score
            weekend_score = min(weekend_count / (self.WEEKEND_TXN_THRESHOLD * 4), 0.5)
            ratio_score = min(weekend_excess * 2, 0.3)
            holiday_score = min(holiday_txns / 10, 0.3)

            final = min(weekend_score + ratio_score + holiday_score, 1.0)

            self._evidence = {
                "weekend_txns_30d": weekend_count,
                "weekday_txns_30d": weekday_count,
                "weekend_ratio": round(weekend_ratio, 3),
                "weekend_volume_30d": round(weekend_volume, 2),
                "holiday_txns": holiday_txns,
                "holidays_active": list(holiday_dates),
                "day_distribution": {str(d): dow_data.get(d, {}).get('count', 0) for d in range(7)},
                "triggered": final > 0.3
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"WeekendHolidayDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
