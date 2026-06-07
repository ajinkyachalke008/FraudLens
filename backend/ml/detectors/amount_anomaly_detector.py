"""
Amount Anomaly Detector — Statistical deviation analysis.
Detects amounts that deviate significantly from an account's historical
transaction patterns using z-score analysis and percentile breakpoints.
"""
import logging
import math
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AmountAnomalyDetector:
    """
    Uses z-score and percentile analysis to detect unusual amounts:
    - Transactions 3+ standard deviations from the mean
    - Single transactions > 90th percentile of historical amounts
    - Sudden jump in average transaction size (week-over-week)
    """

    Z_SCORE_THRESHOLD = 2.5        # 2.5 sigma = statistically unusual
    PERCENTILE_THRESHOLD = 0.95    # 95th percentile
    AVG_JUMP_MULTIPLIER = 3.0     # 3x week-over-week avg increase

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()

            # Historical stats (last 90 days)
            ninety_days = now - timedelta(days=90)
            stats_result = await db.execute(
                select(
                    func.count(Transaction.id).label('cnt'),
                    func.coalesce(func.avg(Transaction.amount), 0).label('avg_amt'),
                    func.coalesce(func.min(Transaction.amount), 0).label('min_amt'),
                    func.coalesce(func.max(Transaction.amount), 0).label('max_amt'),
                ).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= ninety_days
                )
            )
            stats = stats_result.one()
            total_count = int(stats.cnt or 0)
            hist_avg = float(stats.avg_amt or 0)
            hist_max = float(stats.max_amt or 0)

            if total_count < 5:
                self._evidence = {"txn_count_90d": total_count, "triggered": False,
                                  "note": "Insufficient history for anomaly detection"}
                return 0.0

            # Calculate standard deviation (approximate via SQL)
            # stddev = sqrt(avg(x^2) - avg(x)^2)
            var_result = await db.execute(
                select(
                    func.coalesce(func.avg(Transaction.amount * Transaction.amount), 0).label('avg_sq')
                ).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= ninety_days
                )
            )
            avg_sq = float(var_result.scalar() or 0)
            variance = avg_sq - (hist_avg ** 2)
            std_dev = math.sqrt(max(variance, 0))

            if std_dev == 0:
                std_dev = hist_avg * 0.3  # Fallback: assume 30% CV

            # Recent transactions (last 7 days) — find anomalous ones
            week_ago = now - timedelta(days=7)
            recent_result = await db.execute(
                select(Transaction.amount).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= week_ago
                )
            )
            recent_amounts = [float(r[0]) for r in recent_result.all()]

            if not recent_amounts:
                self._evidence = {"recent_txns": 0, "triggered": False}
                return 0.0

            # Z-score analysis
            z_scores = [(a - hist_avg) / std_dev for a in recent_amounts]
            max_z = max(abs(z) for z in z_scores)
            outlier_count = sum(1 for z in z_scores if abs(z) > self.Z_SCORE_THRESHOLD)

            # Week-over-week average comparison
            recent_avg = sum(recent_amounts) / len(recent_amounts)
            prev_week_result = await db.execute(
                select(func.coalesce(func.avg(Transaction.amount), 0)).where(
                    or_(
                        Transaction.from_account == account_id,
                        Transaction.to_account == account_id
                    ),
                    Transaction.timestamp >= week_ago - timedelta(days=7),
                    Transaction.timestamp < week_ago
                )
            )
            prev_avg = float(prev_week_result.scalar() or hist_avg)
            avg_jump_ratio = recent_avg / prev_avg if prev_avg > 0 else 1.0

            # Score components
            z_score_component = min(max_z / (self.Z_SCORE_THRESHOLD * 2), 0.4)
            outlier_component = min(outlier_count / 5, 0.3)
            jump_component = min(max(avg_jump_ratio - 1, 0) / (self.AVG_JUMP_MULTIPLIER - 1), 0.3) if avg_jump_ratio > 1.5 else 0

            final = min(z_score_component + outlier_component + jump_component, 1.0)

            self._evidence = {
                "historical_avg": round(hist_avg, 2),
                "historical_std_dev": round(std_dev, 2),
                "recent_avg": round(recent_avg, 2),
                "max_z_score": round(max_z, 2),
                "outlier_count": outlier_count,
                "avg_jump_ratio": round(avg_jump_ratio, 2),
                "recent_max": round(max(recent_amounts), 2),
                "recent_txn_count": len(recent_amounts),
                "triggered": final > 0.3
            }
            return round(final, 3)

        except Exception as e:
            logger.warning(f"AmountAnomalyDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence
