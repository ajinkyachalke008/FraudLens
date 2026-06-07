"""
Enhanced Excel/CSV parser — wraps the existing excel_parser.py
to conform to the new NormalizedTransaction output format.
"""
import logging
from typing import List, Tuple

from models.schemas.ingestion_multi import NormalizedTransaction, ParseError

logger = logging.getLogger(__name__)


async def parse_spreadsheet(
    file_path: str,
    original_filename: str
) -> Tuple[List[NormalizedTransaction], List[ParseError]]:
    """
    Wraps the existing excel_parser to produce NormalizedTransaction output.
    Supports: .xlsx, .xls, .csv
    """
    transactions: List[NormalizedTransaction] = []
    errors: List[ParseError] = []

    try:
        from services.ingestion.excel_parser import parse_excel_to_rows

        row_count = 0
        for row in parse_excel_to_rows(file_path):
            row_count += 1
            transactions.append(NormalizedTransaction(
                transaction_ref=row.transaction_ref,
                timestamp=row.timestamp,
                amount=row.amount,
                currency=row.currency,
                from_account=row.from_account,
                to_account=row.to_account,
                transaction_type=row.transaction_type,
                upi_id=row.upi_id,
                narration=row.narration,
                source_file=original_filename,
                confidence=1.0,
                parser_notes=f"Excel/CSV structured extraction, row {row_count}"
            ))

        if not transactions:
            errors.append(ParseError(
                filename=original_filename,
                reason="No valid transactions found in spreadsheet (all rows had 0 amount or missing data)",
                severity="warning"
            ))

    except ValueError as e:
        errors.append(ParseError(
            filename=original_filename,
            reason=f"Column mapping error: {str(e)}",
            severity="error"
        ))
    except Exception as e:
        logger.error(f"Spreadsheet parse error for {original_filename}: {e}", exc_info=True)
        errors.append(ParseError(
            filename=original_filename,
            reason=f"Spreadsheet parsing error: {str(e)}",
            severity="error"
        ))

    return transactions, errors
