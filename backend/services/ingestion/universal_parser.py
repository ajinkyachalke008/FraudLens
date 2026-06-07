"""
Universal Parser — Master router that detects file format and delegates
to the correct parser. Handles validation, error recovery, and entity resolution.
"""
import os
import logging
from typing import List, Tuple, Optional

from models.schemas.ingestion_multi import NormalizedTransaction, ParseError

logger = logging.getLogger(__name__)

# Supported formats
SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.pdf', '.docx'}
MAX_FILE_SIZE_MB = 50


def detect_format(filename: str) -> Optional[str]:
    """Detects file format from extension. Returns extension or None."""
    ext = os.path.splitext(filename)[1].lower()
    return ext if ext in SUPPORTED_EXTENSIONS else None


def validate_file(filename: str, size_bytes: int) -> Optional[ParseError]:
    """Pre-flight validation before parsing. Returns error or None."""
    ext = detect_format(filename)
    if not ext:
        return ParseError(
            filename=filename,
            reason=f"Unsupported format. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            severity="error"
        )
    if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        return ParseError(
            filename=filename,
            reason=f"File exceeds {MAX_FILE_SIZE_MB}MB limit ({size_bytes / 1024 / 1024:.1f}MB)",
            severity="error"
        )
    if size_bytes == 0:
        return ParseError(
            filename=filename,
            reason="File is empty (0 bytes)",
            severity="error"
        )
    return None


async def parse_file(
    file_path: str,
    original_filename: str
) -> Tuple[List[NormalizedTransaction], List[ParseError]]:
    """
    Master parser router. Detects format and delegates to the correct parser.
    
    Returns:
        (transactions, errors) — transactions may be partial even if errors exist
    """
    ext = detect_format(original_filename)
    transactions: List[NormalizedTransaction] = []
    errors: List[ParseError] = []

    try:
        if ext in ('.xlsx', '.xls', '.csv'):
            from services.ingestion.excel_parser_v2 import parse_spreadsheet
            transactions, errors = await parse_spreadsheet(file_path, original_filename)

        elif ext == '.pdf':
            from services.ingestion.pdf_parser import parse_pdf
            transactions, errors = await parse_pdf(file_path, original_filename)

        elif ext == '.docx':
            from services.ingestion.docx_parser import parse_docx
            transactions, errors = await parse_docx(file_path, original_filename)

        else:
            errors.append(ParseError(
                filename=original_filename,
                reason=f"No parser available for '{ext}' format",
                severity="error"
            ))

    except Exception as e:
        logger.error(f"Parser crash for {original_filename}: {e}", exc_info=True)
        errors.append(ParseError(
            filename=original_filename,
            reason=f"Unexpected parser error: {str(e)}",
            severity="error"
        ))

    # Post-processing: entity resolution on all extracted transactions
    if transactions:
        try:
            from services.ingestion.entity_resolver import resolve_entities
            transactions = resolve_entities(transactions)
        except Exception as e:
            logger.warning(f"Entity resolution failed for {original_filename}: {e}")
            errors.append(ParseError(
                filename=original_filename,
                reason=f"Entity resolution warning: {str(e)}",
                severity="warning"
            ))

    logger.info(
        f"Parsed {original_filename}: {len(transactions)} transactions, "
        f"{len(errors)} errors/warnings"
    )
    return transactions, errors
