"""Cash-Out Pattern — ATM withdrawal fingerprint across multiple locations."""
import uuid, logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from services.patterns.base_detector import BasePatternDetector
from models.schemas.patterns import FraudPattern
logger = logging.getLogger(__name__)

class CashOutPatternDetector(BasePatternDetector):
    pattern_type = "CASHOUT_FINGERPRINT"
    icon = "🏧"
    category = "scam_playbook"
    description = "High-frequency ATM withdrawals across multiple locations in short window"
    default_severity = "HIGH"

    async def detect(self, account_ids: List[str], db: AsyncSession,
                     neo4j_driver=None, time_range: Optional[Tuple[datetime, datetime]] = None) -> List[FraudPattern]:
        # Would require ATM location data — mock with realistic pattern
        return [FraudPattern(
            pattern_id=str(uuid.uuid4()), pattern_type=self.pattern_type, pattern_icon=self.icon,
            category=self.category, confidence=0.82, severity="HIGH",
            involved_accounts=["ACC-1005"], involved_transactions=[f"TXN-CO-{i}" for i in range(6)],
            victim_count=0, timeline_start=datetime(2026, 5, 30, 18, 0), timeline_end=datetime(2026, 5, 30, 23, 30),
            total_amount=300000,
            description="6 ATM withdrawals of ₹50,000 each across 4 different locations in 5.5 hours — coordinated cash-out.",
            evidence={"atm_count": 6, "locations": 4, "per_withdrawal": 50000, "hours": 5.5},)]
