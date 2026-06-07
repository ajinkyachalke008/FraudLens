"""
Multi-Format Ingestion API — Upload PDF/Excel/Word files, preview
extracted transactions, and commit to PostgreSQL + Neo4j graph.
"""
import os
import uuid
import tempfile
import logging
import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.sql.ingestion_session import IngestionSession, IngestionFile
from models.sql.user import User
from models.schemas.ingestion_multi import (
    MultiUploadResponse, SessionDetailResponse, PreviewResponse,
    CommitResponse, ParseError, FileDetail, NormalizedTransaction
)
from services.ingestion.universal_parser import validate_file, parse_file
from api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-multi", response_model=MultiUploadResponse, status_code=202)
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Up to 20 files (PDF, Excel, CSV, Word)"),
    case_id: str = Query(None, description="Optional case ID to link ingested data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts multiple files, parses each for transaction data, and stores
    results for preview. Call /sessions/{id}/commit to write to graph.
    """
    if len(files) > 20:
        raise HTTPException(400, "Maximum 20 files per upload")
    if len(files) == 0:
        raise HTTPException(400, "No files provided")

    # Create ingestion session
    session = IngestionSession(
        uploaded_by=current_user.id,
        files_count=0,
        status="parsing",
        case_id=uuid.UUID(case_id) if case_id else None
    )
    db.add(session)
    await db.flush()

    accepted = 0
    rejected = 0
    rejection_reasons: List[ParseError] = []
    total_txns = 0

    for file in files:
        content = await file.read()
        file_size = len(content)

        # Validate
        error = validate_file(file.filename, file_size)
        if error:
            rejected += 1
            rejection_reasons.append(error)
            continue

        # Save to temp file
        ext = os.path.splitext(file.filename)[1]
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(tmp_fd)
        try:
            with open(tmp_path, "wb") as f:
                f.write(content)

            # Parse
            start_time = time.time()
            transactions, parse_errors = await parse_file(tmp_path, file.filename)
            duration_ms = int((time.time() - start_time) * 1000)

            # Create file record
            ing_file = IngestionFile(
                session_id=session.id,
                filename=os.path.basename(tmp_path),
                original_filename=file.filename,
                file_format=ext.lstrip('.').lower(),
                mime_type=file.content_type,
                size_bytes=file_size,
                transactions_found=len(transactions),
                accounts_found=len(set(
                    acc for t in transactions
                    for acc in [t.from_account, t.to_account]
                )),
                parse_status="parsed" if transactions else ("error" if parse_errors else "empty"),
                parse_duration_ms=duration_ms,
                error_message=parse_errors[0].reason if parse_errors else None,
                preview_data=[t.model_dump(mode='json') for t in transactions]
            )
            db.add(ing_file)

            total_txns += len(transactions)
            accepted += 1
            rejection_reasons.extend([e for e in parse_errors if e.severity == "error"])

        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    session.files_count = accepted
    session.transactions_extracted = total_txns
    session.status = "preview" if accepted > 0 else "failed"
    await db.commit()

    return MultiUploadResponse(
        session_id=session.id,
        status=session.status,
        files_accepted=accepted,
        files_rejected=rejected,
        rejection_reasons=[r for r in rejection_reasons if r.severity == "error"]
    )


@router.get("/sessions", response_model=List[SessionDetailResponse])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List past ingestion sessions for current user."""
    result = await db.execute(
        select(IngestionSession)
        .where(IngestionSession.uploaded_by == current_user.id)
        .order_by(IngestionSession.created_at.desc())
        .limit(limit).offset(offset)
    )
    sessions = result.scalars().all()
    return [_session_to_response(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detail of a specific ingestion session."""
    session = await _get_session(session_id, db)
    return _session_to_response(session)


@router.get("/sessions/{session_id}/preview", response_model=PreviewResponse)
async def get_session_preview(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all extracted transactions for review before committing to graph."""
    session = await _get_session(session_id, db)

    all_transactions: List[NormalizedTransaction] = []
    warnings: List[ParseError] = []

    for file in session.files:
        if file.preview_data:
            for txn_data in file.preview_data:
                txn = NormalizedTransaction(**txn_data)
                txn.source_file = file.original_filename
                all_transactions.append(txn)
                if txn.confidence < 0.8:
                    warnings.append(ParseError(
                        filename=file.original_filename,
                        reason=f"Low confidence ({txn.confidence:.0%}) — ₹{txn.amount:,.0f} on {txn.timestamp}",
                        severity="warning"
                    ))

    return PreviewResponse(
        session_id=session.id,
        total_transactions=len(all_transactions),
        transactions=all_transactions,
        warnings=warnings,
        low_confidence_count=sum(1 for t in all_transactions if t.confidence < 0.8)
    )


@router.post("/sessions/{session_id}/commit", response_model=CommitResponse)
async def commit_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Commit parsed transactions to PostgreSQL + Neo4j graph."""
    session = await _get_session(session_id, db)

    if session.status not in ("preview", "partial_error"):
        raise HTTPException(400, f"Session is '{session.status}', expected 'preview'")

    session.status = "committing"
    await db.flush()

    # Collect all transactions from preview data
    from models.schemas.ingest import TransactionRow
    all_rows: List[TransactionRow] = []
    for file in session.files:
        if file.preview_data:
            for txn_data in file.preview_data:
                all_rows.append(TransactionRow(
                    transaction_ref=txn_data["transaction_ref"],
                    timestamp=txn_data["timestamp"],
                    amount=txn_data["amount"],
                    from_account=txn_data["from_account"],
                    to_account=txn_data["to_account"],
                    transaction_type=txn_data.get("transaction_type"),
                    upi_id=txn_data.get("upi_id"),
                    narration=txn_data.get("narration"),
                ))

    if not all_rows:
        session.status = "complete"
        await db.commit()
        return CommitResponse(
            session_id=session.id, transactions_committed=0,
            graph_nodes_created=0, graph_edges_created=0,
            new_accounts_discovered=0, duplicate_transactions_skipped=0,
            status="complete"
        )

    # Write to PostgreSQL + Neo4j
    try:
        from services.ingestion.graph_writer import GraphWriter
        from core.neo4j import get_neo4j_credentials

        neo4j_uri, neo4j_user, neo4j_pass = get_neo4j_credentials()
        writer = GraphWriter(db, neo4j_uri, neo4j_user, neo4j_pass)

        batch_size = 500
        for i in range(0, len(all_rows), batch_size):
            batch = all_rows[i:i + batch_size]
            await writer.write_batch(batch, str(session.case_id) if session.case_id else None)

        await writer.close()

        unique_accounts = set()
        for r in all_rows:
            unique_accounts.add(r.from_account)
            unique_accounts.add(r.to_account)

        session.status = "complete"
        session.graph_nodes_created = len(unique_accounts)
        session.graph_edges_created = len(all_rows)
        session.new_accounts_discovered = len(unique_accounts)
        session.completed_at = datetime.utcnow()

        for file in session.files:
            file.parse_status = "committed"

        await db.commit()

    except Exception as e:
        logger.error(f"Commit failed for session {session_id}: {e}", exc_info=True)
        session.status = "partial_error"
        session.error_summary = str(e)[:500]
        await db.commit()

        return CommitResponse(
            session_id=session.id, transactions_committed=0,
            graph_nodes_created=0, graph_edges_created=0,
            new_accounts_discovered=0, duplicate_transactions_skipped=0,
            status="partial_error"
        )

    return CommitResponse(
        session_id=session.id,
        transactions_committed=len(all_rows),
        graph_nodes_created=session.graph_nodes_created,
        graph_edges_created=session.graph_edges_created,
        new_accounts_discovered=session.new_accounts_discovered,
        duplicate_transactions_skipped=session.duplicate_transactions,
        status="complete"
    )


# ──── Helpers ──────────────────────────────────────────────────

async def _get_session(session_id: uuid.UUID, db: AsyncSession) -> IngestionSession:
    result = await db.execute(
        select(IngestionSession).where(IngestionSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Ingestion session not found")
    return session


def _session_to_response(s: IngestionSession) -> SessionDetailResponse:
    return SessionDetailResponse(
        session_id=s.id,
        status=s.status,
        files_count=s.files_count,
        transactions_extracted=s.transactions_extracted,
        new_accounts_discovered=s.new_accounts_discovered,
        duplicate_transactions=s.duplicate_transactions,
        files=[FileDetail(
            file_id=f.id,
            filename=f.original_filename,
            format=f.file_format or "unknown",
            size_bytes=f.size_bytes,
            transactions_found=f.transactions_found,
            parse_status=f.parse_status,
            parse_duration_ms=f.parse_duration_ms,
            error_message=f.error_message
        ) for f in (s.files or [])],
        created_at=s.created_at,
        completed_at=s.completed_at
    )
