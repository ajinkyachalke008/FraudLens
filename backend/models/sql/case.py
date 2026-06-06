import uuid
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    case_number = Column(String, unique=True, nullable=False)
    status = Column(String, default='open')
    priority = Column(String, default='medium')
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    description = Column(String)
    total_amount = Column(Numeric(20, 2))
    victim_count = Column(Integer, default=0)
    suspect_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))
