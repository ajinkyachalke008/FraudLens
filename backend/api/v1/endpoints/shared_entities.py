"""
Shared Entity API — Feature 4 endpoints.
Entity scanning, cross-case links, branch intelligence.
"""
from fastapi import APIRouter, Query
from typing import Optional, List
from models.schemas.shared_entities import (
    EntityScanRequest, EntityScanResponse, SharedEntityResult,
    CrossCaseLink, BranchIntelligence, EntitySummary, EntitySuppressRequest,
    AccountEntityProfile,
)
import uuid

router = APIRouter()


# ──── Mock Data ──────────────────────────────────────────────

def _mock_entities() -> List[dict]:
    return [
        {"entity_id": str(uuid.uuid4()), "entity_type": "PHONE", "entity_value": "9876543210", "accounts": ["ACC-1001", "ACC-1002", "ACC-3091"], "account_count": 3, "cases": ["CASE-2026-A8F3", "CASE-2026-B1D7"], "case_count": 2, "risk_assessment": "CRITICAL", "is_cross_case": True, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "PHONE", "entity_value": "8765432109", "accounts": ["ACC-1004", "ACC-1005"], "account_count": 2, "cases": ["CASE-2026-A8F3"], "case_count": 1, "risk_assessment": "MEDIUM", "is_cross_case": False, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "UPI_VPA", "entity_value": "fraud.payments@paytm", "accounts": ["ACC-1001", "ACC-1002", "ACC-1004"], "account_count": 3, "cases": ["CASE-2026-A8F3"], "case_count": 1, "risk_assessment": "HIGH", "is_cross_case": False, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "UPI_VPA", "entity_value": "collect.money@ybl", "accounts": ["ACC-1005", "ACC-3091"], "account_count": 2, "cases": ["CASE-2026-B1D7"], "case_count": 1, "risk_assessment": "MEDIUM", "is_cross_case": False, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "IFSC", "entity_value": "HDFC0001234", "accounts": ["ACC-1001", "ACC-1004", "ACC-1005"], "account_count": 3, "cases": ["CASE-2026-A8F3"], "case_count": 1, "risk_assessment": "HIGH", "is_cross_case": False, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "IFSC", "entity_value": "SBIN0009876", "accounts": ["ACC-1002", "ACC-3091"], "account_count": 2, "cases": ["CASE-2026-B1D7"], "case_count": 1, "risk_assessment": "MEDIUM", "is_cross_case": False, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "PAN", "entity_value": "ABCDE1234F", "accounts": ["ACC-1001", "ACC-1004"], "account_count": 2, "cases": ["CASE-2026-A8F3"], "case_count": 1, "risk_assessment": "HIGH", "is_cross_case": False, "has_blacklisted": True},
        {"entity_id": str(uuid.uuid4()), "entity_type": "NAME", "entity_value": "Rajesh Kumar / Raj Kumar", "accounts": ["ACC-1002", "ACC-1004"], "account_count": 2, "cases": ["CASE-2026-A8F3"], "case_count": 1, "risk_assessment": "MEDIUM", "is_cross_case": False, "has_blacklisted": False},
        {"entity_id": str(uuid.uuid4()), "entity_type": "BENEFICIARY", "entity_value": "ACC-HUB-001", "accounts": ["ACC-V001", "ACC-V002", "ACC-V003", "ACC-V004", "ACC-V005"], "account_count": 5, "cases": ["CASE-2026-A8F3", "CASE-2026-B1D7"], "case_count": 2, "risk_assessment": "CRITICAL", "is_cross_case": True, "has_blacklisted": False},
    ]


# ──── Endpoints ──────────────────────────────────────────────

@router.post("/scan", response_model=EntityScanResponse)
async def scan_entities(request: EntityScanRequest):
    """Trigger entity scan for case/accounts."""
    entities = [SharedEntityResult(**e) for e in _mock_entities()]
    by_type = {}
    for e in entities:
        by_type[e.entity_type] = by_type.get(e.entity_type, 0) + 1
    return EntityScanResponse(
        entities_found=len(entities), entities=entities, by_type=by_type,
        cross_case_links=[
            CrossCaseLink(case_a="CASE-2026-A8F3", case_b="CASE-2026-B1D7",
                          entity_type="PHONE", entity_value="9876543210",
                          shared_accounts=["ACC-1001", "ACC-3091"], link_strength=0.85),
        ],
        alerts_generated=2,
    )


@router.get("/")
async def list_entities(
    entity_type: Optional[str] = None,
    risk: Optional[str] = None,
):
    """List all shared entities with filters."""
    entities = _mock_entities()
    if entity_type:
        entities = [e for e in entities if e["entity_type"] == entity_type]
    if risk:
        entities = [e for e in entities if e["risk_assessment"] == risk]
    return {"entities": entities, "total": len(entities)}


@router.get("/summary")
async def entity_summary():
    """Dashboard stats: counts per entity type."""
    entities = _mock_entities()
    by_type = {}
    for e in entities:
        by_type[e["entity_type"]] = by_type.get(e["entity_type"], 0) + 1
    return EntitySummary(
        total_entities=len(entities), by_type=by_type,
        cross_case_count=2, suppressed_count=0,
    )


@router.get("/cross-case-links")
async def get_cross_case_links():
    """Cases linked by shared entities."""
    return {"links": [
        {"case_a": "CASE-2026-A8F3", "case_b": "CASE-2026-B1D7",
         "entity_type": "PHONE", "entity_value": "9876543210",
         "shared_accounts": ["ACC-1001", "ACC-3091"], "link_strength": 0.85},
        {"case_a": "CASE-2026-A8F3", "case_b": "CASE-2026-B1D7",
         "entity_type": "BENEFICIARY", "entity_value": "ACC-HUB-001",
         "shared_accounts": ["ACC-V001", "ACC-V003"], "link_strength": 0.72},
    ]}


@router.post("/link-analysis")
async def link_analysis(body: dict):
    """Full shared entity report for given accounts."""
    return await scan_entities(EntityScanRequest(account_ids=body.get("account_ids", [])))


@router.get("/branches")
async def list_branches():
    """Branch Intelligence: sorted by fraud risk."""
    return {"branches": [
        {"ifsc": "HDFC0001234", "branch_name": "HDFC Bank Pune Main", "city": "Pune", "account_count": 12, "fraud_account_count": 5, "total_fraud_volume": 2500000, "risk_score": 0.85},
        {"ifsc": "SBIN0009876", "branch_name": "SBI Camp Branch", "city": "Pune", "account_count": 8, "fraud_account_count": 3, "total_fraud_volume": 1200000, "risk_score": 0.65},
        {"ifsc": "ICIC0005432", "branch_name": "ICICI Bank Kothrud", "city": "Pune", "account_count": 6, "fraud_account_count": 2, "total_fraud_volume": 800000, "risk_score": 0.45},
    ]}


@router.get("/branches/{ifsc}")
async def get_branch_detail(ifsc: str):
    """Single branch detail."""
    return {"ifsc": ifsc, "branch_name": "HDFC Bank Pune Main", "city": "Pune",
            "account_count": 12, "fraud_account_count": 5, "total_fraud_volume": 2500000,
            "risk_score": 0.85, "accounts": ["ACC-1001", "ACC-1004", "ACC-1005"]}


@router.get("/account/{account_id}")
async def get_account_entities(account_id: str):
    """All entities linked to an account."""
    entities = [e for e in _mock_entities() if account_id in e.get("accounts", [])]
    linked = set()
    for e in entities:
        linked.update(e.get("accounts", []))
    linked.discard(account_id)
    return AccountEntityProfile(
        account_id=account_id, entities=[SharedEntityResult(**e) for e in entities],
        linked_accounts=list(linked),
    )


@router.get("/{entity_id}")
async def get_entity_detail(entity_id: str):
    """Full entity detail: accounts, cases, timeline."""
    return _mock_entities()[0]


@router.patch("/{entity_id}/suppress")
async def suppress_entity(entity_id: str, body: EntitySuppressRequest):
    """Suppress false positive entity link (global)."""
    return {"entity_id": entity_id, "suppressed": True, "reason": body.reason}
