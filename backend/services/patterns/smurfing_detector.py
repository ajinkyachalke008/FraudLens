"""
Smurfing Detector — Identifies sub-₹50k structuring patterns.
Multiple transactions just below the reporting threshold that aggregate to large sums.
"""
import uuid
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from services.patterns.base_detector import BasePatternDetector
from models.schemas.patterns import FraudPattern

logger = logging.getLogger(__name__)

THRESHOLD_MIN = 45000
THRESHOLD_MAX = 49999
MIN_COUNT_PER_DAY = 3
MIN_AGGREGATE = 200000


class SmurfingDetector(BasePatternDetector):
    pattern_type = "SMURFING"
    icon = "💸"
    category = "structural"
    description = "Multiple sub-₹50k transactions aggregating to large sums (structuring/smurfing)"
    default_severity = "HIGH"

    async def detect(
        self,
        account_ids: List[str],
        db: AsyncSession,
        neo4j_driver=None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[FraudPattern]:
        patterns = []
        try:
            from models.sql.transaction import Transaction

            query = (
                select(
                    Transaction.from_account,
                    cast(Transaction.timestamp, Date).label("day"),
                    func.count(Transaction.id).label("cnt"),
                    func.sum(Transaction.amount).label("total"),
                    func.min(Transaction.timestamp).label("first_ts"),
                    func.max(Transaction.timestamp).label("last_ts"),
                    func.array_agg(Transaction.transaction_ref).label("refs"),
                )
                .where(
                    Transaction.from_account.in_(account_ids),
                    Transaction.amount >= THRESHOLD_MIN,
                    Transaction.amount <= THRESHOLD_MAX,
                )
                .group_by(Transaction.from_account, "day")
                .having(
                    func.count(Transaction.id) >= MIN_COUNT_PER_DAY,
                    func.sum(Transaction.amount) >= MIN_AGGREGATE,
                )
            )

            if time_range:
                query = query.where(
                    Transaction.timestamp >= time_range[0],
                    Transaction.timestamp <= time_range[1],
                )

            result = await db.execute(query)
            rows = result.all()

            for row in rows:
                confidence = min(row.cnt / (MIN_COUNT_PER_DAY * 2), 1.0)
                patterns.append(FraudPattern(
                    pattern_id=str(uuid.uuid4()),
                    pattern_type=self.pattern_type,
                    pattern_icon=self.icon,
                    category=self.category,
                    confidence=round(confidence, 2),
                    severity="CRITICAL" if row.total > 500000 else "HIGH",
                    involved_accounts=[row.from_account],
                    involved_transactions=row.refs[:20] if row.refs else [],
                    timeline_start=row.first_ts,
                    timeline_end=row.last_ts,
                    total_amount=float(row.total),
                    description=(
                        f"Smurfing detected: {row.cnt} transactions between "
                        f"₹{THRESHOLD_MIN:,}-₹{THRESHOLD_MAX:,} on {row.day}, "
                        f"totaling ₹{float(row.total):,.0f}. Classic structuring pattern."
                    ),
                    evidence={
                        "txn_count": row.cnt,
                        "day": str(row.day),
                        "threshold_range": f"₹{THRESHOLD_MIN:,}-₹{THRESHOLD_MAX:,}",
                    },
                ))

        except Exception as e:
            logger.warning(f"SmurfingDetector error: {e}")

        # Mock fallback
        if not patterns and not account_ids:
            patterns = self._mock_patterns()

        return patterns

    def _mock_patterns(self) -> List[FraudPattern]:
        return [FraudPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=self.pattern_type,
            pattern_icon=self.icon,
            category=self.category,
            confidence=0.88,
            severity="HIGH",
            involved_accounts=["ACC-1002", "ACC-1004"],
            involved_transactions=["TXN-SM-001", "TXN-SM-002", "TXN-SM-003", "TXN-SM-004"],
            timeline_start=datetime(2026, 5, 1),
            timeline_end=datetime(2026, 5, 1, 18, 30),
            total_amount=196000,
            description="4 transactions of ₹49,000 each within 6 hours — classic smurfing below ₹50k threshold.",
            evidence={"txn_count": 4, "day": "2026-05-01", "threshold_range": "₹45,000-₹49,999"},
        )]
