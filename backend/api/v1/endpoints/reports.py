from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response, StreamingResponse
from typing import Optional
import logging
import uuid
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.sql.user import User
from api.deps import get_current_user

from services.reporting.llm_narrative import generate_case_narrative, stream_case_narrative
from services.reporting.pdf_generator import generate_pdf_report

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stream/{case_id}")
async def stream_dossier(case_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream the AI narrative live.
    """
    # Fetch Live Data
    from core.database import AsyncSessionLocal
    from sqlalchemy import select
    from models.sql.case import Case
    from models.sql.transaction import Transaction

    async with AsyncSessionLocal() as db:
        case_result = await db.execute(select(Case).where(Case.id == case_id))
        case = case_result.scalar_one_or_none()
        
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        txn_result = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
        transactions = txn_result.scalars().all()
        
    dynamic_case_data = {
        "case_id": str(case.id),
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "total_transactions": len(transactions),
        "total_volume_inr": float(case.total_amount) if case.total_amount else 0.0,
        "victim_count": case.victim_count,
        "suspect_count": case.suspect_count,
        "detected_patterns": [
            {"type": "Investment Scam Pipeline", "confidence": 0.94, "severity": "CRITICAL"} # Pattern logic simulated
        ]
    }
    
    async def event_generator():
        async for chunk in stream_case_narrative(dynamic_case_data):
            # Format as Server-Sent Event
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/generate/{case_id}")
async def generate_dossier(case_id: str):
    """
    Generates a full AI narrative Case Dossier and returns it as a PDF.
    In a real app, this would fetch graph/SQL data by case_id.
    """
    # 1. Fetch Mock Case Data for the LLM
    mock_case_data = {
        "case_id": case_id,
        "total_transactions": 254,
        "total_volume_inr": 4500000,
        "detected_patterns": [
            {"type": "Investment Scam", "confidence": 0.94, "severity": "CRITICAL"},
            {"type": "Round Robin", "confidence": 0.88, "severity": "HIGH"}
        ],
        "shared_entities": [
            {"type": "UPI", "value": "returns.invest@ybl", "cross_case": True},
            {"type": "PHONE", "value": "9876543210", "cross_case": False}
        ]
    }
    
    # 2. Call OpenRouter LLM
    logger.info(f"Generating AI narrative for case {case_id}")
    narrative_text = await generate_case_narrative(mock_case_data)
    
    # 3. Generate PDF
    pdf_bytes = generate_pdf_report(
        case_id=case_id,
        narrative_text=narrative_text,
        metadata={"risk_level": "CRITICAL"}
    )
    
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=FraudLens_Dossier_{case_id}.pdf"}
    )

@router.get("/export/fir/{case_id}")
async def export_fir_pdf(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates an official FIR PDF and returns it as a downloadable file."""
    from sqlalchemy import select
    from models.sql.case import Case
    from models.sql.transaction import Transaction
    from services.reporting.export_engine import ExportEngine
    
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    txn_result = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
    transactions = txn_result.scalars().all()
    
    case_data = {
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "total_amount": float(case.total_amount) if case.total_amount else 0.0,
        "victim_count": case.victim_count,
        "suspect_count": case.suspect_count,
        "description": case.description
    }
    
    pdf_buffer = ExportEngine.generate_fir_pdf(case_data, transactions)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=FIR_{case.case_number}.pdf"}
    )

@router.get("/export/chargesheet/{case_id}")
async def export_chargesheet_docx(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates an official Charge Sheet DOCX and returns it as a downloadable file."""
    from sqlalchemy import select
    from models.sql.case import Case
    from models.sql.transaction import Transaction
    from services.reporting.export_engine import ExportEngine
    
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    txn_result = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
    transactions = txn_result.scalars().all()
    
    case_data = {
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "total_amount": float(case.total_amount) if case.total_amount else 0.0,
        "victim_count": case.victim_count,
        "suspect_count": case.suspect_count,
        "description": case.description
    }
    
    docx_buffer = ExportEngine.generate_chargesheet_docx(case_data, transactions)
    
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=ChargeSheet_{case.case_number}.docx"}
    )

@router.post("/export/async/fir/{case_id}")
async def export_fir_async(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers a background Celery task to generate the FIR PDF."""
    from sqlalchemy import select
    from models.sql.case import Case
    from models.sql.transaction import Transaction
    from workers.tasks import generate_fir_pdf_task
    
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    txn_result = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
    transactions = txn_result.scalars().all()
    
    case_data = {
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "total_amount": float(case.total_amount) if case.total_amount else 0.0,
        "victim_count": case.victim_count,
        "suspect_count": case.suspect_count,
        "description": case.description
    }
    
    # We must convert transactions to dicts for Celery JSON serialization
    txns_serialized = [{"id": str(t.id), "amount": float(t.amount), "from_account": t.from_account, "to_account": t.to_account} for t in transactions]
    
    # Dispatch the task
    task = generate_fir_pdf_task.delay(str(case_id), case_data, txns_serialized)
    
    return {"status": "processing", "task_id": task.id}

@router.get("/export/async/status/{task_id}")
async def get_export_status(task_id: str):
    """Polls the status of a Celery export task."""
    from core.celery_app import celery_app
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state == 'PENDING':
        return {"status": "pending"}
    elif result.state == 'SUCCESS':
        return {"status": "completed", "download_url": f"/api/v1/reports/export/download/{task_id}"}
    elif result.state == 'FAILURE':
        return {"status": "failed", "error": str(result.info)}
    else:
        return {"status": result.state}
