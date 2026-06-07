"""KYC Fraud — Account details change followed by large transfer within 48h."""
import uuid, logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from services.patterns.base_detector import BasePatternDetector
from models.schemas.patterns import FraudPattern
logger = logging.getLogger(__name__)

class KYCFraudDetector(BasePatternDetector):
    pattern_type = "KYC_FRAUD"
    icon = "🪪"
    category = "scam_playbook"
    description = "Account details change followed by large outbound transfer"
    default_severity = "HIGH"

    async def detect(self, account_ids: List[str], db: AsyncSession,
                     neo4j_driver=None, time_range: Optional[Tuple[datetime, datetime]] = None) -> List[FraudPattern]:
        # KYC changes require account update audit trail — mock for now
        return [FraudPattern(
            pattern_id=str(uuid.uuid4()), pattern_type=self.pattern_type, pattern_icon=self.icon,
            category=self.category, confidence=0.71, severity="HIGH",
            involved_accounts=["ACC-1005"], involved_transactions=["TXN-KYC-001"],
            victim_count=1, timeline_start=datetime(2026, 5, 28), timeline_end=datetime(2026, 5, 29),
            total_amount=500000,
            description="KYC fraud: phone/email changed on ACC-1005 → ₹5,00,000 transferred out within 24h.",
            evidence={"changes": ["phone", "email"], "hours_before_transfer": 18},)]
