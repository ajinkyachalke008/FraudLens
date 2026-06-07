"""
Pydantic schemas for Blacklist & Watchlist management (Feature 8).
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime, date


# ──── Blacklist Schemas ──────────────────────────────────────────

class BlacklistEntry(BaseModel):
    """Single blacklisted account."""
    id: UUID4
    account_id: str
    reason: str
    evidence_transaction_ids: Optional[str] = None
    added_by: UUID4
    case_reference: Optional[UUID4] = None
    is_active: bool = True
    bank_notified: bool = False
    bank_notification_date: Optional[datetime] = None
    court_order_ref: Optional[str] = None
    propagation_complete: bool = False
    added_at: datetime


class BlacklistAddRequest(BaseModel):
    """Request to add an account to the blacklist."""
    account_id: str = Field(..., min_length=3, max_length=50)
    reason: str = Field(..., min_length=5)
    evidence_transaction_ids: Optional[str] = None  # Comma-separated UUIDs
    case_id: Optional[UUID4] = None
    propagate: bool = True  # Auto-propagate to linked accounts


class BlacklistResponse(BaseModel):
    """Response with blacklisted accounts."""
    entries: List[BlacklistEntry]
    total: int


# ──── Watchlist Schemas ──────────────────────────────────────────

class WatchlistEntry(BaseModel):
    """Single watched account."""
    id: UUID4
    account_id: str
    reason: str
    watch_level: str  # PASSIVE | ACTIVE | URGENT
    assigned_investigator: Optional[UUID4] = None
    review_date: Optional[date] = None
    notes: Optional[str] = None
    last_activity: Optional[datetime] = None
    source: str = "manual"  # manual | propagation | alert
    source_account_id: Optional[str] = None
    added_by: Optional[UUID4] = None
    added_at: datetime
    updated_at: datetime


class WatchlistAddRequest(BaseModel):
    """Request to add an account to the watchlist."""
    account_id: str = Field(..., min_length=3, max_length=50)
    reason: str = Field(..., min_length=5)
    watch_level: str = Field("PASSIVE", pattern="^(PASSIVE|ACTIVE|URGENT)$")
    assigned_investigator: Optional[UUID4] = None
    review_date: Optional[date] = None
    notes: Optional[str] = None


class WatchlistUpdateRequest(BaseModel):
    """Request to update a watchlist entry."""
    watch_level: Optional[str] = Field(None, pattern="^(PASSIVE|ACTIVE|URGENT)$")
    assigned_investigator: Optional[UUID4] = None
    review_date: Optional[date] = None
    notes: Optional[str] = None


class WatchlistResponse(BaseModel):
    """Response with watched accounts."""
    entries: List[WatchlistEntry]
    total: int


# ──── Account Check Schemas ──────────────────────────────────────

class AccountCheckResult(BaseModel):
    """Result of checking an account against blacklist + watchlist."""
    account_id: str
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None
    blacklist_date: Optional[datetime] = None
    is_watched: bool = False
    watch_level: Optional[str] = None
    watch_reason: Optional[str] = None


class BulkCheckRequest(BaseModel):
    """Request to check multiple accounts."""
    account_ids: List[str] = Field(..., min_length=1, max_length=200)


class BulkCheckResponse(BaseModel):
    """Response with check results for multiple accounts."""
    results: List[AccountCheckResult]
    blacklisted_count: int
    watched_count: int


class PropagationResult(BaseModel):
    """Result of blacklist propagation to linked accounts."""
    source_account_id: str
    first_degree_added: int
    second_degree_added: int
    total_watchlist_entries_created: int
    investigators_notified: int
