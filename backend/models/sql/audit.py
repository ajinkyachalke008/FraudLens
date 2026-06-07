import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models.sql.base import Base

class AuditLog(Base):
    """
    Maintains an immutable ledger of actions taken by investigators.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String, nullable=False) # e.g., 'case', 'alert', 'report'
    entity_id = Column(String, nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False) # e.g., 'STATUS_CHANGED', 'NOTE_ADDED'
    metadata_blob = Column(JSONB, nullable=True) # stores old_value, new_value, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
