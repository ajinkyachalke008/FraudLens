"""Reverse Funnel Detector — Many small → one large → many small again."""
import uuid, logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from services.patterns.base_detector import BasePatternDetector
from models.schemas.patterns import FraudPattern
logger = logging.getLogger(__name__)

class ReverseFunnelDetector(BasePatternDetector):
    pattern_type = "REVERSE_FUNNEL"
    icon = "🔻"
    category = "structural"
    description = "Many small inflows → collect → scatter to many small outflows"
    default_severity = "CRITICAL"

    async def detect(self, account_ids: List[str], db: AsyncSession,
                     neo4j_driver=None, time_range: Optional[Tuple[datetime, datetime]] = None) -> List[FraudPattern]:
        # Mock — real implementation combines SQL fan-in/fan-out analysis with Neo4j path verification
        return [FraudPattern(
            pattern_id=str(uuid.uuid4()), pattern_type=self.pattern_type, pattern_icon=self.icon,
            category=self.category, confidence=0.79, severity="CRITICAL",
            involved_accounts=["ACC-1001", "ACC-1002", "ACC-1003", "ACC-1004", "ACC-1005"],
            involved_transactions=[f"TXN-RF-{i}" for i in range(8)],
            timeline_start=datetime(2026, 5, 20), timeline_end=datetime(2026, 5, 21),
            total_amount=450000, victim_count=5,
            description="5 victims → ACC-1001 (collection hub, ₹4.5L) → scattered to 3 mule accounts.",
            evidence={"collection_hub": "ACC-1001", "victim_count": 5, "scatter_count": 3},)]
