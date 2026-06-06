import uuid
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    neo4j_rel_id = Column(String)
    transaction_ref = Column(String, unique=True, nullable=False)
    from_account = Column(String, nullable=False, index=True)
    to_account = Column(String, nullable=False, index=True)
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String, default='INR')
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    transaction_type = Column(String)
    upi_id = Column(String)
    bank_ref = Column(String)
    narration = Column(String)
    source_file = Column(String)
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), index=True)
    risk_flag = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
