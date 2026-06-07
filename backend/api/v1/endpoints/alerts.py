"""
Alerts API — Feature 7 endpoints.
List, acknowledge, update status, assign, stats.
"""
from fastapi import APIRouter, Query
from typing import Optional
from models.schemas.alerts import (
    AlertResponse, AlertBrief, AlertStats,
    AlertStatusUpdate, AlertAckRequest, AlertAssignRequest,
)
import uuid
from datetime import datetime, timedelta

router = APIRouter()


# ──── Mock Data ──────────────────────────────────────────────

def _mock_alerts():
    now = datetime.utcnow()
    return [
        {"alert_id": str(uuid.uuid4()), "alert_type": "BLACKLIST_HIT", "severity": "EMERGENCY", "title": "Blacklist hit: ACC-1001 → ACC-BL-007", "message": "Transaction of ₹4,50,000 to BLACKLISTED account ACC-BL-007 detected.", "account_id": "ACC-1001", "case_id": "CASE-2026-A8F3", "trigger_data": {"blacklisted_account": "ACC-BL-007", "amount": 450000}, "status": "active", "acknowledged": False, "acknowledged_at": None, "assigned_to": None, "escalation_level": 0, "created_at": (now - timedelta(minutes=2)).isoformat(), "age_minutes": 2},
        {"alert_id": str(uuid.uuid4()), "alert_type": "RISK_THRESHOLD", "severity": "CRITICAL", "title": "ACC-1001 risk 89% (13/15 signals)", "message": "15-signal risk engine scored ACC-1001 at 0.89. Tags: MULE, HIGH_VELOCITY, KNOWN_SYNDICATE.", "account_id": "ACC-1001", "case_id": "CASE-2026-A8F3", "trigger_data": {"risk_score": 0.89, "signals_active": 13}, "status": "active", "acknowledged": False, "acknowledged_at": None, "assigned_to": "DI-SHARMA", "escalation_level": 0, "created_at": (now - timedelta(minutes=5)).isoformat(), "age_minutes": 5},
        {"alert_id": str(uuid.uuid4()), "alert_type": "PATTERN_DETECTED", "severity": "CRITICAL", "title": "🎯 INVESTMENT_SCAM: 2 accounts, ₹24,50,000", "message": "Investment scam: victim ACC-V001 sent 5 escalating payments to ACC-1001.", "account_id": "ACC-1001", "case_id": "CASE-2026-A8F3", "trigger_data": {"pattern_type": "INVESTMENT_SCAM", "confidence": 0.89}, "status": "active", "acknowledged": False, "acknowledged_at": None, "assigned_to": "DI-SHARMA", "escalation_level": 0, "created_at": (now - timedelta(minutes=8)).isoformat(), "age_minutes": 8},
        {"alert_id": str(uuid.uuid4()), "alert_type": "PATTERN_DETECTED", "severity": "HIGH", "title": "📱 OTP_FRAUD: 2 accounts, ₹3,85,000", "message": "OTP fraud: ₹2 test → ₹3,85,000 drained in 13 minutes.", "account_id": "ACC-1002", "case_id": "CASE-2026-A8F3", "trigger_data": {"pattern_type": "OTP_FRAUD", "confidence": 0.95}, "status": "acknowledged", "acknowledged": True, "acknowledged_at": (now - timedelta(minutes=10)).isoformat(), "assigned_to": "DI-SHARMA", "escalation_level": 0, "created_at": (now - timedelta(minutes=15)).isoformat(), "age_minutes": 15},
        {"alert_id": str(uuid.uuid4()), "alert_type": "SHARED_ENTITY", "severity": "HIGH", "title": "Shared PHONE: 9876543210 across 2 cases", "message": "Accounts ACC-1001, ACC-1002, ACC-3091 share phone 9876543210.", "account_id": None, "case_id": None, "trigger_data": {"entity_type": "PHONE", "entity_value": "9876543210"}, "status": "active", "acknowledged": False, "acknowledged_at": None, "assigned_to": None, "escalation_level": 1, "created_at": (now - timedelta(minutes=20)).isoformat(), "age_minutes": 20},
        {"alert_id": str(uuid.uuid4()), "alert_type": "VELOCITY_SPIKE", "severity": "HIGH", "title": "Velocity spike on ACC-1004: 15 txns in 1 hour", "message": "Account ACC-1004 processed 15 transactions totaling ₹7.5L in under 1 hour.", "account_id": "ACC-1004", "case_id": "CASE-2026-A8F3", "trigger_data": {"velocity_score": 0.93, "txn_count": 15}, "status": "investigating", "acknowledged": True, "acknowledged_at": (now - timedelta(minutes=25)).isoformat(), "assigned_to": "DI-PATIL", "escalation_level": 0, "created_at": (now - timedelta(minutes=30)).isoformat(), "age_minutes": 30},
        {"alert_id": str(uuid.uuid4()), "alert_type": "WATCHLIST_ACTIVITY", "severity": "MEDIUM", "title": "Watchlist account ACC-3091 active", "message": "Watchlisted account ACC-3091 has new transaction: ₹25,000 from ACC-V009.", "account_id": "ACC-3091", "case_id": "CASE-2026-B1D7", "trigger_data": {"amount": 25000}, "status": "active", "acknowledged": False, "acknowledged_at": None, "assigned_to": None, "escalation_level": 0, "created_at": (now - timedelta(minutes=45)).isoformat(), "age_minutes": 45},
        {"alert_id": str(uuid.uuid4()), "alert_type": "PATTERN_DETECTED", "severity": "MEDIUM", "title": "📅 WEEKEND_RUSH: ACC-1004", "message": "73% of transactions on weekends (expected ~29%).", "account_id": "ACC-1004", "case_id": "CASE-2026-A8F3", "trigger_data": {"pattern_type": "WEEKEND_RUSH"}, "status": "active", "acknowledged": False, "acknowledged_at": None, "assigned_to": None, "escalation_level": 0, "created_at": (now - timedelta(hours=2)).isoformat(), "age_minutes": 120},
    ]


# ──── Endpoints ──────────────────────────────────────────────

@router.get("/")
async def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    alert_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List alerts with filters."""
    alerts = _mock_alerts()
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    if acknowledged is not None:
        alerts = [a for a in alerts if a["acknowledged"] == acknowledged]
    if alert_type:
        alerts = [a for a in alerts if a["alert_type"] == alert_type]
    return {"alerts": alerts[:limit], "total": len(alerts)}


@router.get("/stats")
async def alert_stats():
    """Active/unacked counts by severity, avg response time."""
    alerts = _mock_alerts()
    by_severity = {}
    by_type = {}
    unacked = 0
    for a in alerts:
        by_severity[a["severity"]] = by_severity.get(a["severity"], 0) + 1
        by_type[a["alert_type"]] = by_type.get(a["alert_type"], 0) + 1
        if not a["acknowledged"]:
            unacked += 1
    return AlertStats(
        total_active=len([a for a in alerts if a["status"] == "active"]),
        unacknowledged=unacked,
        by_severity=by_severity,
        by_type=by_type,
        avg_response_time_minutes=4.2,
        escalated_count=1,
        resolved_this_week=47,
    )


@router.get("/unacknowledged")
async def unacknowledged_alerts():
    """Unacked alerts sorted by severity then time."""
    severity_order = {"EMERGENCY": 0, "CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
    alerts = [a for a in _mock_alerts() if not a["acknowledged"]]
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 5))
    return {"alerts": alerts, "total": len(alerts)}


@router.get("/{alert_id}")
async def get_alert_detail(alert_id: str):
    """Full alert detail."""
    alert = _mock_alerts()[0]
    alert["alert_id"] = alert_id
    return alert


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge alert."""
    return {"alert_id": alert_id, "acknowledged": True, "acknowledged_at": datetime.utcnow().isoformat()}


@router.patch("/{alert_id}/status")
async def update_alert_status(alert_id: str, update: AlertStatusUpdate):
    """Update alert status."""
    return {"alert_id": alert_id, "status": update.status, "updated": True}


@router.patch("/{alert_id}/assign")
async def assign_alert(alert_id: str, body: AlertAssignRequest):
    """Assign alert to investigator."""
    return {"alert_id": alert_id, "assigned_to": body.assigned_to, "updated": True}
