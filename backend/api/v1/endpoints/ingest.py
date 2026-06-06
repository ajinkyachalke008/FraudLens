import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.neo4j import get_neo4j_credentials
from models.schemas.ingest import IngestionResponse, TransactionCreate
from services.ingestion.excel_parser import parse_excel_to_rows
from services.ingestion.graph_writer import GraphWriter
from streaming.producer import producer_client
from models.sql.user import User
from api.deps import get_current_user
from fastapi_limiter.depends import RateLimiter

router = APIRouter()

async def process_ingestion_background(file_path: str, db: AsyncSession, case_id: str = None):
    try:
        # Configuration for Neo4j connection
        neo4j_uri, neo4j_user, neo4j_pass = get_neo4j_credentials()
        writer = GraphWriter(db, neo4j_uri, neo4j_user, neo4j_pass)
        
        # 1. Parse Excel into normalized rows (generator)
        row_generator = parse_excel_to_rows(file_path)
        
        # 2. Batch write to databases
        batch = []
        batch_size = 1000
        total_processed = 0
        
        for row in row_generator:
            batch.append(row)
            if len(batch) >= batch_size:
                await writer.write_batch(batch, case_id)
                total_processed += len(batch)
                batch.clear()
                
        # Write any remaining rows
        if batch:
            await writer.write_batch(batch, case_id)
            total_processed += len(batch)
            
        print(f"Successfully processed {total_processed} rows from {file_path}")
        
    except Exception as e:
        print(f"Ingestion failed for {file_path}: {str(e)}")
        # In a full system, update the ingestion_jobs table status to 'failed'
    finally:
        await writer.close()
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/transaction", response_model=Dict[str, Any])
async def ingest_single_transaction(transaction: TransactionCreate, current_user: User = Depends(get_current_user)):
    """
    Ingests a single transaction and pushes it to Kafka for Real-Time ML processing.
    """
    try:
        # Convert Pydantic model to dict
        data = transaction.model_dump()
        
        # Publish to Kafka / Queue
        await producer_client.send_transaction("fraudlens.transactions.raw", data)
        
        return {"status": "success", "message": "Transaction submitted to streaming pipeline"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")

@router.post("/upload", response_model=IngestionResponse, status_code=202)
async def upload_transactions(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    case_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported.")
        
    job_id = uuid.uuid4()
    
    # Save uploaded file to a temporary location for background processing
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(tmp_fd)
    
    with open(tmp_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    # Kick off background task
    background_tasks.add_task(process_ingestion_background, tmp_path, db, case_id)
    
    return IngestionResponse(
        job_id=job_id,
        status="accepted",
        message="File uploaded successfully. Processing in background."
    )
