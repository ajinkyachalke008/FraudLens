import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_number = Column(String, unique=True, nullable=False, index=True)
    bank_name = Column(String)
    account_type = Column(String)
    registered_name = Column(String)
    phone_number = Column(String)
    pan_number = Column(String)
    ifsc_code = Column(String)
    state = Column(String)
    city = Column(String)
    account_label = Column(String, index=True)
    is_frozen = Column(Boolean, default=False)
    freeze_date = Column(DateTime(timezone=True))
    freeze_reason = Column(String)
    neo4j_node_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
