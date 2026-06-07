"""
Ingestion Session & File models — tracks multi-file upload sessions,
parse progress, and preview data before graph commit.
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class IngestionSession(Base):
    __tablename__ = "ingestion_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    files_count = Column(Integer, default=0)
    transactions_extracted = Column(Integer, default=0)
    new_accounts_discovered = Column(Integer, default=0)
    duplicate_transactions = Column(Integer, default=0)
    graph_nodes_created = Column(Integer, default=0)
    graph_edges_created = Column(Integer, default=0)
    status = Column(String(20), default='uploading')
    # Status lifecycle: uploading → parsing → preview → committing → complete | partial_error | failed
    error_summary = Column(Text, nullable=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey('cases.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    files = relationship("IngestionFile", back_populates="session", lazy="selectin",
                         cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IngestionSession {self.id} status={self.status} files={self.files_count}>"


class IngestionFile(Base):
    __tablename__ = "ingestion_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('ingestion_sessions.id'), nullable=False)
    filename = Column(String, nullable=False)           # Temp filename on disk
    original_filename = Column(String, nullable=False)  # User's original filename
    file_format = Column(String(10))                    # pdf | xlsx | xls | csv | docx
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, default=0)
    transactions_found = Column(Integer, default=0)
    accounts_found = Column(Integer, default=0)
    parse_status = Column(String(20), default='pending')
    # Parse status: pending → parsing → parsed → committed | error
    parse_duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    # Store parsed-but-uncommitted transactions as JSON for preview
    preview_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("IngestionSession", back_populates="files")

    def __repr__(self):
        return f"<IngestionFile {self.original_filename} status={self.parse_status}>"
