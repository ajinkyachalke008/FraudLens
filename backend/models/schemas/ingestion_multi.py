"""
Pydantic schemas for the Universal File Ingestion Engine (Feature 1).
Covers multi-file upload, parse preview, and graph commit flows.
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime


class ParseError(BaseModel):
    """Represents a parsing error or warning for a specific file."""
    filename: str
    line_number: Optional[int] = None
    reason: str
    severity: str = "error"  # "error" | "warning"


class NormalizedTransaction(BaseModel):
    """
    Unified output from any parser — PDF, Excel, Word.
    Every parser converts its output to this format.
    """
    transaction_ref: str
    timestamp: datetime
    amount: float
    currency: str = "INR"
    direction: str = "DEBIT"  # DEBIT | CREDIT
    from_account: str
    to_account: str
    transaction_type: Optional[str] = None  # UPI | IMPS | RTGS | NEFT | ATM
    upi_id: Optional[str] = None
    bank_ref: Optional[str] = None
    narration: Optional[str] = None
    source_file: str = ""
    confidence: float = 1.0  # Parser confidence (1.0=Excel, 0.6-0.9=PDF regex)
    parser_notes: Optional[str] = None  # "Extracted via table row 14"


class MultiUploadResponse(BaseModel):
    """Response after uploading multiple files for parsing."""
    session_id: UUID4
    status: str
    files_accepted: int
    files_rejected: int
    rejection_reasons: List[ParseError] = []


class FileDetail(BaseModel):
    """Detail about a single file within an ingestion session."""
    file_id: UUID4
    filename: str
    format: str
    size_bytes: int
    transactions_found: int
    parse_status: str
    parse_duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class SessionDetailResponse(BaseModel):
    """Full detail of an ingestion session."""
    session_id: UUID4
    status: str
    files_count: int
    transactions_extracted: int
    new_accounts_discovered: int
    duplicate_transactions: int
    files: List[FileDetail] = []
    created_at: datetime
    completed_at: Optional[datetime] = None


class PreviewResponse(BaseModel):
    """Extracted transactions for review before committing to graph."""
    session_id: UUID4
    total_transactions: int
    transactions: List[NormalizedTransaction] = []
    warnings: List[ParseError] = []
    low_confidence_count: int = 0  # Transactions with confidence < 0.8


class TransactionEdit(BaseModel):
    """User correction to a parsed transaction before commit."""
    transaction_ref: str
    field: str  # "from_account" | "to_account" | "amount" | "timestamp"
    new_value: str


class CommitResponse(BaseModel):
    """Response after committing parsed transactions to PostgreSQL + Neo4j."""
    session_id: UUID4
    transactions_committed: int
    graph_nodes_created: int
    graph_edges_created: int
    new_accounts_discovered: int
    duplicate_transactions_skipped: int
    status: str
