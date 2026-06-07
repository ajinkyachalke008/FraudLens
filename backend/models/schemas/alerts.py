"""
Pydantic schemas for Feature 7: Real-Time Alert System.
Covers alert creation, WebSocket messages, escalation, and stats.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict


# ──── Alert Creation (Internal) ───────────────────────────────

class AlertCreate(BaseModel):
    """Used internally by alert_engine to create alerts."""
    alert_type: str
    severity: str
    title: str
    message: str
    account_id: Optional[str] = None
    case_id: Optional[str] = None
    trigger_data: dict = {}
    transaction_ids: List[str] = []


# ──── Alert Response ──────────────────────────────────────────

class AlertResponse(BaseModel):
    """Full alert for API responses."""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    account_id: Optional[str] = None
    case_id: Optional[str] = None
    trigger_data: dict = {}
    status: str = "active"
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    assigned_to: Optional[str] = None
    escalation_level: int = 0
    created_at: str
    age_minutes: float = 0.0


class AlertBrief(BaseModel):
    """Minimal — for sidebar list and feed."""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    account_id: Optional[str] = None
    status: str = "active"
    escalation_level: int = 0
    created_at: str


# ──── Alert Actions ───────────────────────────────────────────

class AlertAckRequest(BaseModel):
    alert_id: str


class AlertStatusUpdate(BaseModel):
    status: str  # investigating | resolved | dismissed
    resolution_notes: Optional[str] = None


class AlertAssignRequest(BaseModel):
    assigned_to: str  # User UUID


# ──── Alert Stats ─────────────────────────────────────────────

class AlertStats(BaseModel):
    """Dashboard counters."""
    total_active: int = 0
    unacknowledged: int = 0
    by_severity: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    avg_response_time_minutes: float = 0.0
    escalated_count: int = 0
    resolved_this_week: int = 0


# ──── WebSocket Message ───────────────────────────────────────

class AlertWebSocketMessage(BaseModel):
    """Wire format for WS push."""
    type: str = "FRAUD_ALERT"
    data: dict = {}
    # data: {alert_id, alert_type, severity, title, message,
    #        account_id, requires_ack, escalation_level, created_at}
