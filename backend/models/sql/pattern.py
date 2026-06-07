"""
DetectedPattern — Stores forensic pattern detection results.
Covers 19 pattern types: 12 structural + 7 Indian scam playbooks.
"""
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class DetectedPattern(Base):
    __tablename__ = "detected_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    pattern_type = Column(String(40), nullable=False, index=True)
    # Structural: SMURFING | RAPID_LAYERING | ROUND_ROBIN | MULE_CHAIN |
    #   TIME_CLUSTER | AMOUNT_MIRROR | EVEN_SPLIT | CASHOUT_BURST |
    #   REVERSE_FUNNEL | WEEKEND_RUSH | DORMANT_ACTIVATION | CROSSBANK_HOP
    # Scam Playbook: INVESTMENT_SCAM | OTP_FRAUD | JOB_SCAM | ROMANCE_SCAM |
    #   KYC_FRAUD | CASHOUT_FINGERPRINT | MULTI_BANK_LAYERING

    severity = Column(String(10), default="MEDIUM", index=True)
    # LOW | MEDIUM | HIGH | CRITICAL

    confidence = Column(Float, default=0.0)
    accounts_involved = Column(JSON, default=[])
    transactions_involved = Column(JSON, default=[])
    total_value = Column(Numeric(20, 2), default=0)
    victim_count = Column(Integer, default=0)
    time_span_hours = Column(Float, nullable=True)
    timeline_start = Column(DateTime(timezone=True), nullable=True)
    timeline_end = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text)  # Human-readable narrative
    evidence = Column(JSON, default={})

    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=True, index=True)
    detected_by = Column(String, default="system")  # "system" | "manual"
    status = Column(String(20), default="new", index=True)
    # new | investigating | confirmed | false_positive | resolved

    alert_id = Column(UUID(as_uuid=True), ForeignKey('fraud_alerts.id'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
