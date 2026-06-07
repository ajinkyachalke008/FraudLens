"""
SharedEntity — Stores shared entity detection results.
Finds hidden connections: phone, UPI VPA, IFSC branch, PAN, name, beneficiary.
"""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class SharedEntity(Base):
    __tablename__ = "shared_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    entity_type = Column(String(20), nullable=False, index=True)
    # PHONE | UPI_VPA | IFSC | PAN | NAME | BENEFICIARY | DEVICE

    entity_value = Column(String, nullable=False, index=True)
    # The shared value: "9876543210" | "fraud@paytm" | "HDFC0001234" | "ABCDE1234F"

    accounts = Column(JSON, default=[])  # ["ACC-1001","ACC-1002","ACC-3091"]
    account_count = Column(Integer, default=0)
    cases = Column(JSON, default=[])  # ["CASE-2026-A8F3","CASE-2026-B1D7"]
    case_count = Column(Integer, default=0)

    risk_assessment = Column(String(10), default="LOW")
    # LOW | MEDIUM | HIGH | CRITICAL
    # HIGH if shared across cases, CRITICAL if any account is blacklisted

    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))

    is_suppressed = Column(Boolean, default=False)
    suppressed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    suppression_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
