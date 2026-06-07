"""
Time Anomaly Detector — Flags transactions at unusual hours.
Indian banking hours: 9AM-6PM. Suspicious: 12AM-5AM (midnight ops).
Night-time transactions correlate with mule operations and unauthorized access.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Hour ranges (24h format)
SUSPICIOUS_HOURS = set(range(0, 5))     # 12AM - 5AM
HIGH_RISK_HOURS = set(range(0, 4))       # 12AM - 4AM (highest risk)
NORMAL_HOURS = set(range(9, 18))         # 9AM - 6PM (business hours)


class TimeAnomalyDetector:
    """
    Detects transactions occurring at abnormal hours.
    Midnight-to-dawn transactions are high-risk, especially for
    business accounts that should only operate during banking hours.
    """

    NIGHT_TXN_THRESHOLD = 3  # 3+ night txns in a week = suspicious
    NIGHT_VOLUME_THRESHOLD = 50000  # ₹50k+ moved at night = suspicious

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            week_ago = datetime.utcnow() - timedelta(days=7)

            # Count transactions per hour bucket in last 7 days
            result = await db.execute(
                select(
                    extract('hour', Transaction.timestamp).label('hr'),
                    func.count(Transaction.id).label('cnt'),
                    func.coalesce(func.sum(Transaction.amount), 0).label('vol')
                ).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= week_ago
                ).group_by('hr')
            )
            hour_data = {int(row.hr): {'count': int(row.cnt), 'volume': float(row.vol)} for row in result.all()}

            if not hour_data:
                self._evidence = {"night_txns": 0, "triggered": False}
                return 0.0

            # Count night transactions (12AM-5AM)
            night_count = sum(hour_data.get(h, {}).get('count', 0) for h in SUSPICIOUS_HOURS)
            night_volume = sum(hour_data.get(h, {}).get('volume', 0) for h in SUSPICIOUS_HOURS)
            total_count = sum(d['count'] for d in hour_data.values())

            # High-risk hours (12AM-4AM) — even more suspicious
            deep_night_count = sum(hour_data.get(h, {}).get('count', 0) for h in HIGH_RISK_HOURS)

            # Night ratio
            night_ratio = night_count / total_count if total_count > 0 else 0

            # Score components
            count_score = min(night_count / (self.NIGHT_TXN_THRESHOLD * 2), 1.0)
            volume_score = min(night_volume / (self.NIGHT_VOLUME_THRESHOLD * 3), 1.0)
            deep_night_bonus = min(deep_night_count / 3, 0.3)  # Extra weight for 12-4AM

            final = min(count_score * 0.4 + volume_score * 0.3 + night_ratio * 0.2 + deep_night_bonus, 1.0)

            self._evidence = {
                "night_txns_7d": night_count,
                "night_volume_7d": round(night_volume, 2),
                "deep_night_txns_7d": deep_night_count,
                "night_ratio": round(night_ratio, 3),
                "total_txns_7d": total_count,
                "peak_hour": max(hour_data, key=lambda h: hour_data[h]['count']) if hour_data else None,
                "hour_distribution": {str(h): d['count'] for h, d in sorted(hour_data.items())},
                "triggered": final > 0.4
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"TimeAnomalyDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
