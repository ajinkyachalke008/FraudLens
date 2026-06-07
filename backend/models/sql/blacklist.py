"""
Blacklist & Watchlist models — persistent institutional memory for 
confirmed fraud accounts and accounts under surveillance.
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    # Evidence: list of transaction IDs that support the blacklisting
    evidence_transaction_ids = Column(Text, nullable=True)  # comma-separated UUIDs
    added_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    case_reference = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=True)
    is_active = Column(Boolean, default=True)  # Soft delete — never truly remove
    bank_notified = Column(Boolean, default=False)
    bank_notification_date = Column(DateTime(timezone=True), nullable=True)
    court_order_ref = Column(String(100), nullable=True)
    propagation_complete = Column(Boolean, default=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    deactivation_reason = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Blacklist {self.account_id} active={self.is_active}>"


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    watch_level = Column(String(10), default='PASSIVE')  # PASSIVE | ACTIVE | URGENT
    assigned_investigator = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    review_date = Column(Date, nullable=True)  # Next scheduled review
    notes = Column(Text, nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    # Source of watchlist entry — manual or propagation from blacklist
    source = Column(String(20), default='manual')  # manual | propagation | alert
    source_account_id = Column(String(50), nullable=True)  # Blacklisted account that triggered propagation
    added_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Watchlist {self.account_id} level={self.watch_level}>"
