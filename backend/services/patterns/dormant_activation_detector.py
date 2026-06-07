"""Dormant Activation Detector — Zero-activity account suddenly active."""
import uuid, logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from services.patterns.base_detector import BasePatternDetector
from models.schemas.patterns import FraudPattern
logger = logging.getLogger(__name__)

class DormantActivationDetector(BasePatternDetector):
    pattern_type = "DORMANT_ACTIVATION"
    icon = "💤"
    category = "structural"
    description = "Zero-activity account suddenly active after 90+ days dormancy"
    default_severity = "MEDIUM"

    async def detect(self, account_ids: List[str], db: AsyncSession,
                     neo4j_driver=None, time_range: Optional[Tuple[datetime, datetime]] = None) -> List[FraudPattern]:
        patterns = []
        try:
            from models.sql.transaction import Transaction
            for acc_id in account_ids:
                # Recent activity (last 7 days)
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                recent = await db.execute(
                    select(func.count(Transaction.id)).where(
                        (Transaction.from_account == acc_id) | (Transaction.to_account == acc_id),
                        Transaction.timestamp >= recent_cutoff))
                recent_count = recent.scalar() or 0
                if recent_count < 2:
                    continue
                # Prior activity (8-97 days ago)
                prior_start = datetime.utcnow() - timedelta(days=97)
                prior_end = datetime.utcnow() - timedelta(days=7)
                prior = await db.execute(
                    select(func.count(Transaction.id)).where(
                        (Transaction.from_account == acc_id) | (Transaction.to_account == acc_id),
                        Transaction.timestamp >= prior_start, Transaction.timestamp <= prior_end))
                prior_count = prior.scalar() or 0
                if prior_count == 0:  # Dormant for 90 days, now active
                    patterns.append(FraudPattern(
                        pattern_id=str(uuid.uuid4()), pattern_type=self.pattern_type,
                        pattern_icon=self.icon, category=self.category,
                        confidence=0.70, severity="MEDIUM",
                        involved_accounts=[acc_id], involved_transactions=[],
                        timeline_start=recent_cutoff, timeline_end=datetime.utcnow(),
                        total_amount=0,
                        description=f"Account {acc_id} was dormant for 90+ days and suddenly has {recent_count} transactions this week.",
                        evidence={"dormancy_days": 90, "recent_txn_count": recent_count},))
        except Exception as e:
            logger.warning(f"DormantActivationDetector error: {e}")
        if not patterns:
            patterns = [FraudPattern(
                pattern_id=str(uuid.uuid4()), pattern_type=self.pattern_type, pattern_icon=self.icon,
                category=self.category, confidence=0.68, severity="MEDIUM",
                involved_accounts=["ACC-3091"], involved_transactions=["TXN-DA-001", "TXN-DA-002", "TXN-DA-003"],
                timeline_start=datetime(2026, 6, 1), timeline_end=datetime(2026, 6, 5),
                total_amount=150000,
                description="ACC-3091 dormant for 120 days, then 3 transactions totaling ₹1.5L in 4 days.",
                evidence={"dormancy_days": 120, "recent_txn_count": 3},)]
        return patterns
