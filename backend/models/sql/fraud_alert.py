"""
FraudAlert — Real-time alert system with severity, escalation, and assignment.
Triggered by risk thresholds, patterns, blacklist hits, and shared entities.
"""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    alert_type = Column(String(30), nullable=False, index=True)
    # RISK_THRESHOLD | PATTERN_DETECTED | BLACKLIST_HIT |
    # SHARED_ENTITY | WATCHLIST_ACTIVITY | SYNDICATE_JOIN |
    # VELOCITY_SPIKE | INGESTION_ANOMALY

    severity = Column(String(10), nullable=False, index=True)
    # EMERGENCY | CRITICAL | HIGH | MEDIUM | LOW

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    account_id = Column(String, nullable=True, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=True, index=True)
    trigger_data = Column(JSON, default={})
    transaction_ids = Column(JSON, default=[])

    # Status & acknowledgement
    status = Column(String(15), default="active", index=True)
    # active | acknowledged | investigating | resolved | dismissed
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    # Assignment (auto-assigned to case investigator)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Escalation
    escalation_level = Column(Integer, default=0)
    # 0=normal, 1=re-notify, 2=supervisor, 3=broadcast
    escalated_at = Column(DateTime(timezone=True), nullable=True)

    # Suppression & dedup
    suppression_key = Column(String, nullable=True, index=True)
    # Format: "{alert_type}:{account_id}:{date}"

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
