"""
Pydantic schemas for Feature 4: Shared Entity Detection.
Covers phone, UPI VPA, IFSC branch, PAN, name, beneficiary, and device matching.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict


# ──── Entity Results ──────────────────────────────────────────

class SharedEntityResult(BaseModel):
    """A single shared entity finding."""
    entity_id: Optional[str] = None
    entity_type: str               # PHONE | UPI_VPA | IFSC | PAN | NAME | BENEFICIARY | DEVICE
    entity_value: str
    accounts: List[str]
    account_count: int
    cases: List[str] = []
    case_count: int = 0
    risk_assessment: str = "LOW"   # LOW | MEDIUM | HIGH | CRITICAL
    is_cross_case: bool = False
    has_blacklisted: bool = False


class CrossCaseLink(BaseModel):
    """Two cases linked by a shared entity."""
    case_a: str
    case_b: str
    entity_type: str
    entity_value: str
    shared_accounts: List[str]
    link_strength: float = 0.5     # 0.0-1.0 based on number of shared entities


class AccountEntityProfile(BaseModel):
    """All entities associated with one account."""
    account_id: str
    entities: List[SharedEntityResult]
    linked_accounts: List[str] = []  # All accounts sharing any entity
    linked_cases: List[str] = []


class BranchIntelligence(BaseModel):
    """Branch-level fraud intelligence."""
    ifsc: str
    branch_name: str
    city: str = ""
    account_count: int
    fraud_account_count: int = 0
    total_fraud_volume: float = 0.0
    risk_score: float = 0.0
    accounts: List[str] = []


# ──── Request/Response ────────────────────────────────────────

class EntityScanRequest(BaseModel):
    account_ids: Optional[List[str]] = None
    case_id: Optional[str] = None
    entity_types: Optional[List[str]] = None


class EntityScanResponse(BaseModel):
    entities_found: int
    entities: List[SharedEntityResult]
    by_type: Dict[str, int] = {}
    cross_case_links: List[CrossCaseLink] = []
    alerts_generated: int = 0


class EntitySuppressRequest(BaseModel):
    reason: str


class EntitySummary(BaseModel):
    total_entities: int
    by_type: Dict[str, int] = {}
    cross_case_count: int = 0
    suppressed_count: int = 0
