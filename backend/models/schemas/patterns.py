"""
Pydantic schemas for Feature 3: Transaction Pattern Analysis.
Covers 19 pattern types (12 structural + 7 Indian scam playbooks).
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ──── Pattern Output ──────────────────────────────────────────

class FraudPattern(BaseModel):
    """Output from any pattern detector."""
    pattern_id: str
    pattern_type: str                    # "INVESTMENT_SCAM" | "SMURFING" | ...
    pattern_icon: str = "🔍"
    category: str = "structural"         # "structural" | "scam_playbook"
    confidence: float                    # 0.0 - 1.0
    severity: str = "MEDIUM"             # LOW | MEDIUM | HIGH | CRITICAL
    involved_accounts: List[str]
    involved_transactions: List[str]
    timeline_start: datetime
    timeline_end: datetime
    total_amount: float
    victim_count: int = 0
    description: str                     # Human-readable narrative
    evidence_transactions: List[dict] = []  # Specific txns that matched
    evidence: dict = {}                  # Detector-specific proof


# ──── Request/Response ────────────────────────────────────────

class PatternScanRequest(BaseModel):
    account_ids: Optional[List[str]] = None
    case_id: Optional[str] = None
    date_range_from: Optional[datetime] = None
    date_range_to: Optional[datetime] = None
    pattern_types: Optional[List[str]] = None  # Filter to specific patterns


class PatternScanResponse(BaseModel):
    job_id: str
    patterns_found: int
    patterns: List[FraudPattern]
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    scan_duration_ms: int = 0
    alerts_generated: int = 0


class PatternDetail(BaseModel):
    """Full detail for a single pattern (detail drawer)."""
    pattern: FraudPattern
    account_risk_tiers: Dict[str, str] = {}  # {account_id: "CRITICAL"}
    related_patterns: List[str] = []          # Pattern IDs of related patterns
    case_title: Optional[str] = None


class PatternSummary(BaseModel):
    """Aggregated stats for dashboard cards."""
    total_patterns: int
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    top_accounts: List[dict] = []  # [{account_id, pattern_count}]


class PatternStatusUpdate(BaseModel):
    status: str  # investigating | confirmed | false_positive
    notes: Optional[str] = None


class PatternTypeDefinition(BaseModel):
    """Definition of a pattern type for the /types endpoint."""
    type_id: str
    name: str
    icon: str
    description: str
    severity_default: str
    engine: str              # "sql" | "neo4j" | "hybrid"
    category: str            # "structural" | "scam_playbook"
