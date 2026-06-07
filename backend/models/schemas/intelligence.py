"""
Pydantic schemas for the Risk Intelligence Engine (Feature 2).
Covers 15-signal risk profiles, batch scoring, and high-risk account queries.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class SignalEvidence(BaseModel):
    """Evidence details for a single risk signal."""
    triggered: bool = False
    details: Dict[str, Any] = {}


class AccountRiskProfile(BaseModel):
    """
    Full 15-dimensional risk profile for a single account.
    Each signal score ranges from 0.0 (safe) to 1.0 (maximum risk).

    Signals grouped by detection category:

    BEHAVIORAL (transaction patterns):
    - velocity: Transaction burst speed
    - structuring: Sub-₹50k smurfing splits
    - rapid_succession: Sub-minute rapid-fire bursts
    - amount_anomaly: Statistical deviation from normal

    NETWORK (graph topology):
    - roundtrip: Circular money flows (A→B→C→A)
    - shell: Pass-through / funnel accounts
    - fanout: One-to-many scatter distribution
    - fanin: Many-to-one victim collection
    - centrality: PageRank in fraud subgraph
    - crossbank: Multi-bank layering chains

    TEMPORAL (time-based):
    - dormancy: Inactive-to-active spike
    - time_anomaly: Midnight / off-hours activity
    - weekend_holiday: Weekend / public holiday activity

    ML (model-based):
    - gnn: FraudSAGE graph neural network score
    - isolation: Isolation Forest anomaly score
    """
    account_id: str

    # ── Behavioral Signal Scores (0.0 - 1.0) ─────────────────────
    velocity_score: float = Field(0.0, ge=0.0, le=1.0, description="Transaction burst speed anomaly")
    structuring_score: float = Field(0.0, ge=0.0, le=1.0, description="Sub-₹50k threshold evasion (smurfing)")
    rapid_succession_score: float = Field(0.0, ge=0.0, le=1.0, description="Sub-minute rapid-fire transaction bursts")
    amount_anomaly_score: float = Field(0.0, ge=0.0, le=1.0, description="Statistical z-score deviation from normal amounts")

    # ── Network Signal Scores ─────────────────────────────────────
    roundtrip_score: float = Field(0.0, ge=0.0, le=1.0, description="Circular money flow detection (graph cycles)")
    shell_score: float = Field(0.0, ge=0.0, le=1.0, description="Pass-through / funnel account pattern")
    fanout_score: float = Field(0.0, ge=0.0, le=1.0, description="One-to-many scatter distribution (mule payout)")
    fanin_score: float = Field(0.0, ge=0.0, le=1.0, description="Many-to-one victim collection (honey pot)")
    centrality_score: float = Field(0.0, ge=0.0, le=1.0, description="PageRank centrality in fraud subgraph")
    crossbank_score: float = Field(0.0, ge=0.0, le=1.0, description="Multi-bank layering chain detection")

    # ── Temporal Signal Scores ────────────────────────────────────
    dormancy_score: float = Field(0.0, ge=0.0, le=1.0, description="Dormant account reactivation spike")
    time_anomaly_score: float = Field(0.0, ge=0.0, le=1.0, description="Midnight / off-hours transaction activity")
    weekend_holiday_score: float = Field(0.0, ge=0.0, le=1.0, description="Weekend / public holiday activity anomaly")

    # ── ML Signal Scores ──────────────────────────────────────────
    gnn_score: float = Field(0.0, ge=0.0, le=1.0, description="FraudSAGE GNN embedding risk score")
    isolation_score: float = Field(0.0, ge=0.0, le=1.0, description="Isolation Forest multivariate anomaly score")

    # ── Composite ─────────────────────────────────────────────────
    final_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Weighted ensemble of all 15 signals")
    risk_tier: Literal["CLEAN", "WATCH", "ALERT", "CRITICAL"] = "CLEAN"

    # Behavioral tags derived from active signals
    tags: List[str] = []
    # Possible tags: MULE, SHELL, STRUCTURING, VELOCITY_SPIKE, ROUND_TRIP,
    #                DORMANCY_BREAK, LAYERING, FAN_OUT, FAN_IN, NIGHT_OPS,
    #                RAPID_FIRE, AMOUNT_SPIKE, WEEKEND_OPS, CROSS_BANK, COLLECTOR

    # Per-signal evidence (detailed breakdowns)
    evidence: Dict[str, Any] = {}

    # Metadata
    scored_at: Optional[str] = None
    model_version: str = "v2.0"
    signals_active: int = Field(0, description="Number of signals scoring > 0.3")
    signal_count: int = Field(15, description="Total number of risk signals evaluated")


class BatchRiskScoreRequest(BaseModel):
    """Request body for batch risk scoring."""
    account_ids: List[str] = Field(..., min_length=1, max_length=100)


class BatchRiskScoreResponse(BaseModel):
    """Response with risk profiles for multiple accounts."""
    profiles: List[AccountRiskProfile]
    total_scored: int
    scoring_duration_ms: int


class HighRiskAccountsResponse(BaseModel):
    """Paginated list of high-risk accounts."""
    accounts: List[AccountRiskProfile]
    total: int
    tier_filter: Optional[str] = None


class RiskScanResponse(BaseModel):
    """Response after triggering a full risk scan."""
    job_id: str
    status: str  # "started" | "running" | "complete"
    accounts_to_scan: int
    message: str
