"""
Base Pattern Detector — Abstract interface for all 19 pattern detectors.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas.patterns import FraudPattern


class BasePatternDetector(ABC):
    """
    Abstract base class for all pattern detectors.
    Each detector must implement detect() and metadata properties.
    """

    @abstractmethod
    async def detect(
        self,
        account_ids: List[str],
        db: AsyncSession,
        neo4j_driver=None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> List[FraudPattern]:
        """
        Run detection and return all found pattern instances.
        Must be fault-tolerant: if data is unavailable, return empty list.
        """
        ...

    @property
    @abstractmethod
    def pattern_type(self) -> str:
        """Pattern identifier: 'SMURFING', 'INVESTMENT_SCAM', etc."""
        ...

    @property
    @abstractmethod
    def icon(self) -> str:
        """Emoji icon for UI display."""
        ...

    @property
    @abstractmethod
    def category(self) -> str:
        """'structural' or 'scam_playbook'"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this pattern detects."""
        ...

    @property
    def default_severity(self) -> str:
        """Default severity when pattern is detected. Override in subclass."""
        return "MEDIUM"
