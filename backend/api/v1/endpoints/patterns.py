"""
Pattern Analysis API — Feature 3 endpoints.
Trigger scans, list patterns, get details, update status.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from models.schemas.patterns import (
    PatternScanRequest, PatternScanResponse, PatternSummary,
    PatternStatusUpdate, FraudPattern, PatternTypeDefinition,
)
from ml.patterns.pattern_registry import get_all_pattern_types
import uuid
from datetime import datetime

router = APIRouter()


# ──── Mock Data ──────────────────────────────────────────────

def _mock_patterns() -> List[dict]:
    """Return comprehensive mock patterns for all 19 types."""
    return [
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "INVESTMENT_SCAM", "pattern_icon": "🎯", "category": "scam_playbook", "confidence": 0.89, "severity": "CRITICAL", "involved_accounts": ["ACC-V001", "ACC-1001"], "involved_transactions": ["TXN-IS-001", "TXN-IS-002", "TXN-IS-003"], "victim_count": 1, "timeline_start": "2026-03-01T00:00:00", "timeline_end": "2026-05-15T00:00:00", "total_amount": 2450000, "description": "Investment scam: victim ACC-V001 sent 5 escalating payments to ACC-1001 over 75 days.", "evidence": {"escalation_ratio": 3.2, "span_days": 75}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "ROUND_ROBIN", "pattern_icon": "🔄", "category": "structural", "confidence": 0.91, "severity": "CRITICAL", "involved_accounts": ["ACC-1001", "ACC-1002", "ACC-1004", "ACC-1001"], "involved_transactions": ["TXN-RR-001", "TXN-RR-002", "TXN-RR-003"], "victim_count": 0, "timeline_start": "2026-05-10T00:00:00", "timeline_end": "2026-05-10T23:00:00", "total_amount": 500000, "description": "₹5L circular flow: ACC-1001 → ACC-1002 → ACC-1004 → ACC-1001.", "evidence": {"hops": 3}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "OTP_FRAUD", "pattern_icon": "📱", "category": "scam_playbook", "confidence": 0.95, "severity": "CRITICAL", "involved_accounts": ["ACC-V003", "ACC-1002"], "involved_transactions": ["TXN-OTP-001", "TXN-OTP-002"], "victim_count": 1, "timeline_start": "2026-06-01T03:15:00", "timeline_end": "2026-06-01T03:28:00", "total_amount": 385000, "description": "OTP fraud: ₹2 test at 3:15 AM → ₹3,85,000 drained in 13 minutes.", "evidence": {"test_amount": 2, "drain_total": 385000}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "SMURFING", "pattern_icon": "💸", "category": "structural", "confidence": 0.88, "severity": "HIGH", "involved_accounts": ["ACC-1002", "ACC-1004"], "involved_transactions": ["TXN-SM-001", "TXN-SM-002", "TXN-SM-003", "TXN-SM-004"], "victim_count": 0, "timeline_start": "2026-05-01T00:00:00", "timeline_end": "2026-05-01T18:30:00", "total_amount": 196000, "description": "4 transactions of ₹49,000 each — smurfing below ₹50k threshold.", "evidence": {"txn_count": 4}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "JOB_SCAM", "pattern_icon": "💼", "category": "scam_playbook", "confidence": 0.84, "severity": "HIGH", "involved_accounts": ["ACC-1004"], "involved_transactions": ["TXN-JS-001", "TXN-JS-002", "TXN-JS-003"], "victim_count": 8, "timeline_start": "2026-04-01T00:00:00", "timeline_end": "2026-05-15T00:00:00", "total_amount": 24000, "description": "Job scam: 8 victims paid ₹3,000 each as 'registration fees'.", "evidence": {"victim_count": 8, "avg_fee": 3000}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "MULE_CHAIN", "pattern_icon": "⛓️", "category": "structural", "confidence": 0.87, "severity": "CRITICAL", "involved_accounts": ["ACC-1001", "ACC-1002", "ACC-1004", "ACC-1005", "ACC-3091"], "involved_transactions": ["TXN-MC-001", "TXN-MC-002", "TXN-MC-003", "TXN-MC-004"], "victim_count": 0, "timeline_start": "2026-05-15T00:00:00", "timeline_end": "2026-05-15T20:00:00", "total_amount": 750000, "description": "5-account mule chain: ₹7.5L payout chain.", "evidence": {"hops": 4}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "ROMANCE_SCAM", "pattern_icon": "💕", "category": "scam_playbook", "confidence": 0.76, "severity": "HIGH", "involved_accounts": ["ACC-V005", "ACC-1001"], "involved_transactions": ["TXN-RS-001", "TXN-RS-002"], "victim_count": 1, "timeline_start": "2026-02-14T00:00:00", "timeline_end": "2026-05-20T00:00:00", "total_amount": 890000, "description": "Romance scam: 6 payments over 95 days, escalating.", "evidence": {"span_days": 95}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "AMOUNT_MIRROR", "pattern_icon": "🪞", "category": "structural", "confidence": 0.96, "severity": "HIGH", "involved_accounts": ["ACC-1002"], "involved_transactions": [], "victim_count": 0, "timeline_start": "2026-06-01T00:00:00", "timeline_end": "2026-06-02T00:00:00", "total_amount": 280000, "description": "Pass-through relay: ₹2.8L in ≈ ₹2.78L out (0.5% deviation).", "evidence": {"deviation_pct": 0.5}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "CASHOUT_BURST", "pattern_icon": "🏧", "category": "structural", "confidence": 0.85, "severity": "HIGH", "involved_accounts": ["ACC-1005"], "involved_transactions": ["TXN-CB-001", "TXN-CB-002"], "victim_count": 0, "timeline_start": "2026-05-28T10:00:00", "timeline_end": "2026-05-28T22:00:00", "total_amount": 180000, "description": "UPI credits → 3 ATM withdrawals ₹1.8L in 12 hours.", "evidence": {"atm_count": 3}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "CROSSBANK_HOP", "pattern_icon": "🏦", "category": "structural", "confidence": 0.88, "severity": "CRITICAL", "involved_accounts": ["ACC-1001", "ACC-2001", "ACC-3001", "ACC-4001"], "involved_transactions": [], "victim_count": 0, "timeline_start": "2026-05-10T00:00:00", "timeline_end": "2026-05-11T18:00:00", "total_amount": 900000, "description": "₹9L through 5 banks (HDFC→SBI→ICICI→Axis→Kotak).", "evidence": {"bank_count": 5}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "TIME_CLUSTER", "pattern_icon": "⏱️", "category": "structural", "confidence": 0.78, "severity": "HIGH", "involved_accounts": ["ACC-1001"], "involved_transactions": [f"TXN-TC-{i}" for i in range(12)], "victim_count": 0, "timeline_start": "2026-05-20T02:00:00", "timeline_end": "2026-05-20T02:12:00", "total_amount": 580000, "description": "12 transactions in 12 minutes at 2 AM.", "evidence": {"cluster_size": 12}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "WEEKEND_RUSH", "pattern_icon": "📅", "category": "structural", "confidence": 0.72, "severity": "MEDIUM", "involved_accounts": ["ACC-1004"], "involved_transactions": [], "victim_count": 0, "timeline_start": "2026-05-01T00:00:00", "timeline_end": "2026-06-01T00:00:00", "total_amount": 320000, "description": "73% of transactions on weekends (expected ~29%).", "evidence": {"weekend_pct": 73}},
        {"pattern_id": str(uuid.uuid4()), "pattern_type": "DORMANT_ACTIVATION", "pattern_icon": "💤", "category": "structural", "confidence": 0.68, "severity": "MEDIUM", "involved_accounts": ["ACC-3091"], "involved_transactions": [], "victim_count": 0, "timeline_start": "2026-06-01T00:00:00", "timeline_end": "2026-06-05T00:00:00", "total_amount": 150000, "description": "Dormant 120 days, then 3 txns totaling ₹1.5L.", "evidence": {"dormancy_days": 120}},
    ]


# ──── Endpoints ──────────────────────────────────────────────

@router.post("/analyze", response_model=PatternScanResponse)
async def analyze_patterns(request: PatternScanRequest):
    """Trigger pattern analysis for given accounts/case."""
    mock = _mock_patterns()
    by_type = {}
    by_severity = {}
    for p in mock:
        by_type[p["pattern_type"]] = by_type.get(p["pattern_type"], 0) + 1
        by_severity[p["severity"]] = by_severity.get(p["severity"], 0) + 1
    return PatternScanResponse(
        job_id=str(uuid.uuid4())[:8],
        patterns_found=len(mock),
        patterns=[FraudPattern(**p) for p in mock],
        by_type=by_type,
        by_severity=by_severity,
        scan_duration_ms=234,
        alerts_generated=5,
    )


@router.get("/detected")
async def list_detected_patterns(
    case_id: Optional[str] = None,
    account_id: Optional[str] = None,
    type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
):
    """List all detected patterns with filters."""
    mock = _mock_patterns()
    if type:
        mock = [p for p in mock if p["pattern_type"] == type]
    if severity:
        mock = [p for p in mock if p["severity"] == severity]
    return {"patterns": mock, "total": len(mock)}


@router.get("/types")
async def get_pattern_types():
    """Return all 19 pattern type definitions."""
    return {"types": get_all_pattern_types()}


@router.get("/summary")
async def get_pattern_summary():
    """Aggregated pattern stats for dashboard."""
    mock = _mock_patterns()
    by_type, by_severity, by_status = {}, {}, {"new": 8, "investigating": 3, "confirmed": 2}
    for p in mock:
        by_type[p["pattern_type"]] = by_type.get(p["pattern_type"], 0) + 1
        by_severity[p["severity"]] = by_severity.get(p["severity"], 0) + 1
    return PatternSummary(
        total_patterns=len(mock), by_type=by_type, by_severity=by_severity,
        by_status=by_status,
        top_accounts=[
            {"account_id": "ACC-1001", "pattern_count": 5},
            {"account_id": "ACC-1004", "pattern_count": 3},
        ],
    )


@router.get("/account/{account_id}")
async def get_account_patterns(account_id: str):
    """Patterns involving a specific account."""
    mock = [p for p in _mock_patterns() if account_id in p.get("involved_accounts", [])]
    return {"account_id": account_id, "patterns": mock, "total": len(mock)}


@router.get("/{pattern_id}")
async def get_pattern_detail(pattern_id: str):
    """Full pattern detail with evidence."""
    mock = _mock_patterns()[0]
    mock["pattern_id"] = pattern_id
    return {
        "pattern": mock,
        "account_risk_tiers": {"ACC-1001": "CRITICAL", "ACC-1002": "HIGH"},
        "related_patterns": [],
    }


@router.patch("/{pattern_id}/status")
async def update_pattern_status(pattern_id: str, update: PatternStatusUpdate):
    """Update pattern status."""
    return {"pattern_id": pattern_id, "status": update.status, "updated": True}
