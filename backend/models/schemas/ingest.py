from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class IngestionResponse(BaseModel):
    job_id: UUID4
    status: str
    message: str
    estimated_time_seconds: Optional[int] = None

class TransactionCreate(BaseModel):
    id: str
    amount: float
    source: str
    target: str
    hour_of_day: int
    velocity_1h: int
    velocity_24h: int

class TransactionRow(BaseModel):
    transaction_ref: str
    timestamp: datetime
    amount: float
    currency: str = "INR"
    from_account: str
    to_account: str
    transaction_type: Optional[str] = None
    upi_id: Optional[str] = None
    bank_ref: Optional[str] = None
    narration: Optional[str] = None
    risk_flag: Optional[str] = "unknown"

class IngestionJobStatus(BaseModel):
    id: UUID4
    file_name: str
    status: str
    total_rows: Optional[int] = None
    processed_rows: int = 0
    errors: Optional[List[Dict[str, Any]]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
