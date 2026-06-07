"""
PDF Parser v2.0 — Extracts transaction data from PDF bank statements.
Uses pdfplumber for table extraction and regex for unstructured text.

Supports 25+ Indian bank statement formats:
 ━━ Private Banks ━━━━━━━━━━━━━━━━━━━━━━━
  HDFC Bank, ICICI Bank, Axis Bank, Kotak Mahindra Bank, Yes Bank,
  IndusInd Bank, IDFC First Bank, Federal Bank, Bandhan Bank, RBL Bank

 ━━ Public Sector Banks ━━━━━━━━━━━━━━━━━
  SBI, PNB, Bank of Baroda, Canara Bank, Union Bank of India,
  Indian Bank, Bank of India, Central Bank, UCO Bank, IDBI Bank,
  Bank of Maharashtra, Punjab & Sind Bank

 ━━ Payment Banks / Digital ━━━━━━━━━━━━━
  Paytm Payments Bank, Airtel Payments Bank, India Post Payments Bank

 ━━ Cooperative Banks ━━━━━━━━━━━━━━━━━━━
  Saraswat Bank, SVC Bank, TJSB Bank
"""
import re
import logging
from typing import List, Tuple, Optional, Dict
from datetime import datetime

from models.schemas.ingestion_multi import NormalizedTransaction, ParseError

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
#  BANK SIGNATURE DATABASE
# ──────────────────────────────────────────────────────────────────
# Each bank has:
#   identifier: regex to detect the bank from PDF text
#   date_formats: bank-specific date formats
#   columns: expected column names in tables (aliases)
#   special_notes: any quirks in parsing

BANK_SIGNATURES = {
    # ──── Private Banks ────────────────────────────────────────────
    "HDFC": {
        "identifier": r"HDFC\s*BANK|HDFC\s*Ltd",
        "ifsc_prefix": "HDFC",
        "date_formats": ["%d/%m/%y", "%d/%m/%Y"],
        "narration_key": "narration",
        "debit_keys": ["withdrawal amt", "debit", "withdrawal"],
        "credit_keys": ["deposit amt", "credit", "deposit"],
        "ref_patterns": [r"Ref\s*No[:\s]*(\d+)", r"UTR[:\s]*([A-Z0-9]+)"],
    },
    "ICICI": {
        "identifier": r"ICICI\s*BANK|ICICI\s*Ltd",
        "ifsc_prefix": "ICIC",
        "date_formats": ["%d-%m-%Y", "%d/%m/%Y", "%d %b %Y"],
        "narration_key": "transaction remarks",
        "debit_keys": ["withdrawal amount", "debit"],
        "credit_keys": ["deposit amount", "credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)", r"UTR[:\s]*([A-Z0-9]+)", r"NEFT[:\s]*([A-Z0-9]+)"],
    },
    "AXIS": {
        "identifier": r"AXIS\s*BANK",
        "ifsc_prefix": "UTIB",
        "date_formats": ["%d-%m-%Y", "%d/%m/%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit", "dr"],
        "credit_keys": ["credit", "cr"],
        "ref_patterns": [r"Txn\s*Ref[:\s]*([A-Z0-9]+)", r"UTR[:\s]*([A-Z0-9]+)"],
    },
    "KOTAK": {
        "identifier": r"KOTAK\s*MAHINDRA|KOTAK\s*BANK",
        "ifsc_prefix": "KKBK",
        "date_formats": ["%d %b %Y", "%d-%m-%Y", "%d/%m/%Y"],
        "narration_key": "description",
        "debit_keys": ["debit", "dr amount"],
        "credit_keys": ["credit", "cr amount"],
        "ref_patterns": [r"Chq/Ref[:\s]*([A-Z0-9]+)"],
    },
    "YES": {
        "identifier": r"YES\s*BANK",
        "ifsc_prefix": "YESB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "narration",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"UTR[:\s]*([A-Z0-9]+)", r"Ref[:\s]*(\d+)"],
    },
    "INDUSIND": {
        "identifier": r"INDUSIND\s*BANK",
        "ifsc_prefix": "INDB",
        "date_formats": ["%d-%m-%Y", "%d/%m/%Y"],
        "narration_key": "transaction description",
        "debit_keys": ["debit", "debit amount"],
        "credit_keys": ["credit", "credit amount"],
        "ref_patterns": [r"Ref[:\s]*([A-Z0-9]+)"],
    },
    "IDFC_FIRST": {
        "identifier": r"IDFC\s*FIRST|IDFC\s*Bank",
        "ifsc_prefix": "IDFB",
        "date_formats": ["%d %b %Y", "%d/%m/%Y"],
        "narration_key": "description",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"UTR[:\s]*([A-Z0-9]+)"],
    },
    "FEDERAL": {
        "identifier": r"FEDERAL\s*BANK",
        "ifsc_prefix": "FDRL",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "BANDHAN": {
        "identifier": r"BANDHAN\s*BANK",
        "ifsc_prefix": "BDBL",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "narration",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"UTR[:\s]*([A-Z0-9]+)"],
    },
    "RBL": {
        "identifier": r"RBL\s*BANK|RATNAKAR",
        "ifsc_prefix": "RATN",
        "date_formats": ["%d-%m-%Y", "%d/%m/%Y"],
        "narration_key": "description",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*([A-Z0-9]+)"],
    },

    # ──── Public Sector Banks ──────────────────────────────────────
    "SBI": {
        "identifier": r"STATE\s*BANK\s*OF\s*INDIA|SBI|\bSBIN\b",
        "ifsc_prefix": "SBIN",
        "date_formats": ["%d %b %Y", "%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "description",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Txn\s*Date[:\s]*\d+\s*Ref[:\s]*(\d+)", r"UTR[:\s]*([A-Z0-9]+)"],
    },
    "PNB": {
        "identifier": r"PUNJAB\s*NATIONAL\s*BANK|PNB|\bPUNB\b",
        "ifsc_prefix": "PUNB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit", "dr"],
        "credit_keys": ["credit", "cr"],
        "ref_patterns": [r"Txn\s*(?:No|Ref)[:\s]*(\d+)"],
    },
    "BOB": {
        "identifier": r"BANK\s*OF\s*BARODA|BOB|\bBARB\b",
        "ifsc_prefix": "BARB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "narration",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "CANARA": {
        "identifier": r"CANARA\s*BANK|\bCNRB\b",
        "ifsc_prefix": "CNRB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit", "dr"],
        "credit_keys": ["credit", "cr"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "UNION": {
        "identifier": r"UNION\s*BANK\s*OF\s*INDIA|\bUBIN\b",
        "ifsc_prefix": "UBIN",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"],
        "narration_key": "narration",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "INDIAN_BANK": {
        "identifier": r"INDIAN\s*BANK|\bIDIB\b",
        "ifsc_prefix": "IDIB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "BOI": {
        "identifier": r"BANK\s*OF\s*INDIA|\bBKID\b",
        "ifsc_prefix": "BKID",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"],
        "narration_key": "narration",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "CENTRAL_BANK": {
        "identifier": r"CENTRAL\s*BANK\s*OF\s*INDIA|\bCBIN\b",
        "ifsc_prefix": "CBIN",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "UCO": {
        "identifier": r"UCO\s*BANK|\bUCBA\b",
        "ifsc_prefix": "UCBA",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "narration",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "IDBI": {
        "identifier": r"IDBI\s*BANK|\bIBKL\b",
        "ifsc_prefix": "IBKL",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"],
        "narration_key": "narration",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Ref[:\s]*([A-Z0-9]+)"],
    },
    "MAHARASHTRA": {
        "identifier": r"BANK\s*OF\s*MAHARASHTRA|\bMAHB\b",
        "ifsc_prefix": "MAHB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
    "PSB": {
        "identifier": r"PUNJAB\s*(?:&|AND)\s*SIND\s*BANK|\bPSIB\b",
        "ifsc_prefix": "PSIB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "narration",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },

    # ──── Payment Banks / Digital ──────────────────────────────────
    "PAYTM": {
        "identifier": r"PAYTM\s*PAYMENTS?\s*BANK|PYTM",
        "ifsc_prefix": "PYTM",
        "date_formats": ["%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"],
        "narration_key": "description",
        "debit_keys": ["debit", "paid"],
        "credit_keys": ["credit", "received"],
        "ref_patterns": [r"Order\s*ID[:\s]*(\d+)", r"UTR[:\s]*([A-Z0-9]+)"],
    },
    "AIRTEL": {
        "identifier": r"AIRTEL\s*PAYMENTS?\s*BANK",
        "ifsc_prefix": "AIRP",
        "date_formats": ["%d/%m/%Y", "%d %b %Y"],
        "narration_key": "description",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*([A-Z0-9]+)"],
    },
    "IPPB": {
        "identifier": r"INDIA\s*POST\s*PAYMENTS?\s*BANK|IPPB",
        "ifsc_prefix": "IPOS",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "narration",
        "debit_keys": ["debit"],
        "credit_keys": ["credit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },

    # ──── Cooperative Banks ────────────────────────────────────────
    "SARASWAT": {
        "identifier": r"SARASWAT\s*(?:CO-?OP|BANK)|\bSRCB\b",
        "ifsc_prefix": "SRCB",
        "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
        "narration_key": "particulars",
        "debit_keys": ["debit", "withdrawal"],
        "credit_keys": ["credit", "deposit"],
        "ref_patterns": [r"Ref[:\s]*(\d+)"],
    },
}

# ──────────────────────────────────────────────────────────────────
#  GENERIC REGEX PATTERNS (fallback when bank is not identified)
# ──────────────────────────────────────────────────────────────────
GENERIC_PATTERNS = {
    "date": r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    "date_long": r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})",
    "amount": r"₹?\s*([\d,]+\.?\d{0,2})",
    "account": r"(?:A/?c|Account|Acc|Acct)[:\s#]*(\d{8,18})",
    "ifsc": r"([A-Z]{4}0[A-Z0-9]{6})",
    "upi": r"([a-zA-Z0-9._\-]+@[a-zA-Z]+)",
    "ref": r"(?:Ref|UTR|RRN|Txn\s*(?:No|ID|Ref)?|CMS\s*Ref)[:\s]*([A-Za-z0-9]+)",
    "mode": r"\b(UPI|IMPS|RTGS|NEFT|ATM|ECS|NACH|FT|FD|MM|BIL|SI|EMI|AEPS|CMS|DD|BBPS|QR)\b",
    "phone": r"\b(\+91\s*)?([6-9]\d{9})\b",
}


# ──────────────────────────────────────────────────────────────────
#  DATE PARSING
# ──────────────────────────────────────────────────────────────────
def _parse_indian_date(date_str: str, bank_formats: List[str] = None) -> datetime:
    """Parse Indian date formats with bank-specific format priority."""
    # Try bank-specific formats first
    if bank_formats:
        for fmt in bank_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

    # Then try all common formats
    all_formats = [
        "%d/%m/%Y", "%d/%m/%y",
        "%d-%m-%Y", "%d-%m-%y",
        "%d %b %Y", "%d %B %Y",
        "%d-%b-%Y", "%d-%B-%Y",
        "%Y-%m-%d", "%Y/%m/%d",
        "%d.%m.%Y", "%d.%m.%y",
    ]
    for fmt in all_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    # Last resort: dateutil
    try:
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(date_str, dayfirst=True)
    except Exception:
        return datetime.utcnow()


def _clean_amount(val: str) -> float:
    """Parse amount string to float, handling ₹ symbol, commas, and various formats."""
    if not val:
        return 0.0
    cleaned = re.sub(r'[₹Rs\.\s,]', '', str(val))
    # Handle 'Dr' / 'Cr' suffix (some banks append direction to amount)
    cleaned = re.sub(r'(?:Dr|Cr|DR|CR)\s*$', '', cleaned)
    try:
        return abs(float(cleaned)) if cleaned else 0.0
    except ValueError:
        return 0.0


# ──────────────────────────────────────────────────────────────────
#  BANK DETECTION
# ──────────────────────────────────────────────────────────────────
def _detect_bank(text: str) -> Optional[str]:
    """Auto-detect which bank the PDF statement belongs to."""
    text_upper = text[:3000].upper()  # Check first ~3000 chars

    for bank_name, sig in BANK_SIGNATURES.items():
        if re.search(sig["identifier"], text_upper, re.IGNORECASE):
            logger.info(f"Bank detected: {bank_name}")
            return bank_name

    logger.info("No specific bank detected — using GENERIC parser")
    return None


# ──────────────────────────────────────────────────────────────────
#  MAIN PARSER
# ──────────────────────────────────────────────────────────────────
async def parse_pdf(
    file_path: str,
    original_filename: str
) -> Tuple[List[NormalizedTransaction], List[ParseError]]:
    """
    Extracts transactions from PDF bank statements.
    Strategy 1: Auto-detect bank → bank-specific table extraction
    Strategy 2: Generic table extraction with smart column mapping
    Strategy 3: Full-text regex extraction (unstructured PDFs)
    """
    transactions: List[NormalizedTransaction] = []
    errors: List[ParseError] = []

    try:
        import pdfplumber
    except ImportError:
        errors.append(ParseError(
            filename=original_filename,
            reason="pdfplumber not installed. Run: pip install pdfplumber",
            severity="error"
        ))
        return transactions, errors

    detected_bank = None
    bank_sig = None

    try:
        with pdfplumber.open(file_path) as pdf:
            # Extract full text first for bank detection
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # Auto-detect bank
            detected_bank = _detect_bank(full_text)
            bank_sig = BANK_SIGNATURES.get(detected_bank) if detected_bank else None

            # Extract account number from statement header
            statement_account = _extract_statement_account(full_text)

            # Strategy 1 & 2: Table extraction
            all_table_rows: List[List] = []
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table:
                            all_table_rows.extend([row for row in table if row])

            if len(all_table_rows) > 2:
                transactions = _parse_tables(
                    all_table_rows, original_filename,
                    bank_sig=bank_sig,
                    detected_bank=detected_bank,
                    statement_account=statement_account
                )
                if transactions:
                    logger.info(
                        f"PDF table extraction ({detected_bank or 'GENERIC'}): "
                        f"{len(transactions)} transactions from {original_filename}"
                    )
                    return transactions, errors

            # Strategy 3: Full-text regex extraction
            if full_text.strip():
                transactions = _parse_text_regex(
                    full_text, original_filename,
                    bank_sig=bank_sig,
                    detected_bank=detected_bank,
                    statement_account=statement_account
                )

            if not transactions:
                errors.append(ParseError(
                    filename=original_filename,
                    reason=(
                        f"No transactions extracted from {detected_bank or 'unknown bank'} statement. "
                        "PDF may be image-based (OCR not supported) or in an unrecognized format."
                    ),
                    severity="warning"
                ))

    except Exception as e:
        logger.error(f"PDF parse error for {original_filename}: {e}", exc_info=True)
        errors.append(ParseError(
            filename=original_filename,
            reason=f"PDF parsing error: {str(e)}",
            severity="error"
        ))

    return transactions, errors


# ──────────────────────────────────────────────────────────────────
#  ACCOUNT EXTRACTION FROM HEADER
# ──────────────────────────────────────────────────────────────────
def _extract_statement_account(text: str) -> Optional[str]:
    """Extract the statement holder's account number from the PDF header."""
    # Try common patterns
    patterns = [
        r"(?:Account\s*(?:No|Number|#)|A/?c\s*No)[.:\s]*(\d{8,18})",
        r"(?:Savings|Current)\s*A/?c[:\s]*(\d{8,18})",
        r"(?:Statement\s*of\s*Account)[:\s]*(\d{8,18})",
    ]
    for pat in patterns:
        match = re.search(pat, text[:2000], re.IGNORECASE)
        if match:
            return match.group(1)
    return None


# ──────────────────────────────────────────────────────────────────
#  TABLE PARSING
# ──────────────────────────────────────────────────────────────────
def _parse_tables(
    table_rows: List[List],
    source_file: str,
    bank_sig: Optional[Dict] = None,
    detected_bank: Optional[str] = None,
    statement_account: Optional[str] = None
) -> List[NormalizedTransaction]:
    """Parse structured table data from PDF with bank-specific column awareness."""
    transactions = []
    header_row: Optional[List[str]] = None

    # All possible header keywords (combined from all bank signatures)
    header_keywords = {
        'date', 'amount', 'debit', 'credit', 'narration', 'particular',
        'description', 'withdrawal', 'deposit', 'balance', 'ref', 'remarks',
        'value date', 'txn date', 'transaction', 'chq', 'dr', 'cr'
    }

    for row in table_rows:
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            continue

        # Clean row
        cleaned = [str(cell or '').strip() for cell in row]
        row_text = ' '.join(cleaned).lower()

        # Detect header row (must contain at least 2 known keywords)
        keyword_matches = sum(1 for kw in header_keywords if kw in row_text)
        if keyword_matches >= 2 and not header_row:
            header_row = [c.lower().strip() for c in cleaned]
            continue

        if not header_row:
            continue

        # Pad row if shorter than header
        while len(cleaned) < len(header_row):
            cleaned.append('')

        # Map columns to values
        row_dict: Dict[str, str] = {}
        for i, cell in enumerate(cleaned):
            if i < len(header_row):
                row_dict[header_row[i]] = cell

        # Extract transaction
        txn = _extract_from_dict(
            row_dict, source_file,
            bank_sig=bank_sig,
            detected_bank=detected_bank,
            statement_account=statement_account
        )
        if txn:
            transactions.append(txn)

    return transactions


def _extract_from_dict(
    row: Dict[str, str],
    source_file: str,
    bank_sig: Optional[Dict] = None,
    detected_bank: Optional[str] = None,
    statement_account: Optional[str] = None
) -> Optional[NormalizedTransaction]:
    """Extract a NormalizedTransaction from a column-mapped dict with bank-aware parsing."""

    # ── Find date (try bank-specific keys first) ──
    date_val = None
    date_keys = ['date', 'txn dt', 'txn date', 'transaction date', 'value date', 'posting date', 'entry date']
    for key in date_keys:
        if key in row and row[key] and len(row[key].strip()) >= 6:
            date_val = row[key].strip()
            break

    if not date_val:
        return None

    # ── Find amount ──
    amount = 0.0
    direction = "DEBIT"

    # Bank-specific debit/credit keys
    debit_keys = (bank_sig.get("debit_keys", []) if bank_sig else []) + ['debit', 'withdrawal', 'debit amount', 'dr', 'dr amount', 'withdrawal amt']
    credit_keys = (bank_sig.get("credit_keys", []) if bank_sig else []) + ['credit', 'deposit', 'credit amount', 'cr', 'cr amount', 'deposit amt']

    for key in debit_keys:
        if key in row:
            amt = _clean_amount(row[key])
            if amt > 0:
                amount = amt
                direction = "DEBIT"
                break

    if amount == 0:
        for key in credit_keys:
            if key in row:
                amt = _clean_amount(row[key])
                if amt > 0:
                    amount = amt
                    direction = "CREDIT"
                    break

    if amount == 0:
        for key in ['amount', 'txn amount', 'transaction amount', 'value']:
            if key in row:
                amt = _clean_amount(row[key])
                if amt > 0:
                    amount = amt
                    break

    if amount == 0:
        return None

    # ── Find narration (bank-specific key) ──
    narration = ""
    narration_key = bank_sig.get("narration_key") if bank_sig else None
    narration_keys = [narration_key] if narration_key else []
    narration_keys += ['narration', 'description', 'particulars', 'remarks', 'transaction remarks', 'transaction description', 'details']
    for key in narration_keys:
        if key and key in row and row[key]:
            narration = row[key]
            break

    # ── Extract transaction mode ──
    combined_text = f"{narration} {' '.join(row.values())}"
    mode_match = re.search(GENERIC_PATTERNS["mode"], combined_text, re.IGNORECASE)
    txn_type = mode_match.group(1).upper() if mode_match else None

    # ── Find reference number (bank-specific patterns first) ──
    ref = ""
    if bank_sig and "ref_patterns" in bank_sig:
        for pat in bank_sig["ref_patterns"]:
            ref_match = re.search(pat, combined_text, re.IGNORECASE)
            if ref_match:
                ref = ref_match.group(1)
                break

    if not ref:
        for key in ['ref', 'reference', 'txn ref', 'ref no', 'ref no.', 'utr', 'rrn', 'chq/ref no']:
            if key in row and row[key] and row[key].strip():
                ref = row[key].strip()
                break

    if not ref:
        ref_match = re.search(GENERIC_PATTERNS["ref"], combined_text, re.IGNORECASE)
        ref = ref_match.group(1) if ref_match else f"PDF-{hash(narration + date_val) % 100000}"

    # ── Extract UPI VPA, phone, IFSC from narration ──
    upi_match = re.search(GENERIC_PATTERNS["upi"], narration)
    phone_match = re.search(GENERIC_PATTERNS["phone"], narration)
    ifsc_match = re.search(GENERIC_PATTERNS["ifsc"], narration)

    # ── Extract counterparty account from narration ──
    counterparty = None
    acct_match = re.search(GENERIC_PATTERNS["account"], narration)
    if acct_match:
        counterparty = acct_match.group(1)

    # ── Determine from/to accounts ──
    holder = statement_account or "STATEMENT_HOLDER"
    if direction == "DEBIT":
        from_acc = holder
        to_acc = counterparty or (upi_match.group(1) if upi_match else "UNKNOWN_RECEIVER")
    else:
        from_acc = counterparty or (upi_match.group(1) if upi_match else "UNKNOWN_SENDER")
        to_acc = holder

    # ── Parse date with bank-specific formats ──
    bank_date_formats = bank_sig.get("date_formats", []) if bank_sig else []
    try:
        timestamp = _parse_indian_date(date_val, bank_date_formats)
    except Exception:
        timestamp = datetime.utcnow()

    # ── Confidence scoring ──
    confidence = 0.90
    if detected_bank:
        confidence = 0.95  # Higher confidence when bank is identified
    if not counterparty and not upi_match:
        confidence -= 0.05  # Lower if we couldn't identify counterparty
    if not ref or ref.startswith("PDF-"):
        confidence -= 0.05  # Lower if no proper reference number

    return NormalizedTransaction(
        transaction_ref=ref,
        timestamp=timestamp,
        amount=amount,
        direction=direction,
        from_account=from_acc,
        to_account=to_acc,
        transaction_type=txn_type,
        upi_id=upi_match.group(1) if upi_match else None,
        narration=narration[:500],
        source_file=source_file,
        confidence=round(max(confidence, 0.5), 2),
        parser_notes=f"PDF table · {detected_bank or 'GENERIC'}" + (f" · IFSC:{ifsc_match.group(1)}" if ifsc_match else "")
    )


# ──────────────────────────────────────────────────────────────────
#  TEXT REGEX PARSING (unstructured fallback)
# ──────────────────────────────────────────────────────────────────
def _parse_text_regex(
    text: str,
    source_file: str,
    bank_sig: Optional[Dict] = None,
    detected_bank: Optional[str] = None,
    statement_account: Optional[str] = None
) -> List[NormalizedTransaction]:
    """Parse unstructured text using regex patterns with bank-aware extraction."""
    transactions = []
    bank_date_formats = bank_sig.get("date_formats", []) if bank_sig else []
    holder = statement_account or "UNKNOWN_PDF"

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if len(line.strip()) < 10:
            continue

        # Try long date format first (DD Mon YYYY)
        date_match = re.search(GENERIC_PATTERNS["date_long"], line, re.IGNORECASE)
        if not date_match:
            date_match = re.search(GENERIC_PATTERNS["date"], line)

        amount_matches = re.findall(GENERIC_PATTERNS["amount"], line)

        if date_match and amount_matches:
            try:
                timestamp = _parse_indian_date(date_match.group(1), bank_date_formats)
                amounts = [_clean_amount(a) for a in amount_matches]
                amounts = [a for a in amounts if a > 0]
                if not amounts:
                    continue
                amount = max(amounts)

                # Extract metadata
                ref_match = re.search(GENERIC_PATTERNS["ref"], line, re.IGNORECASE)
                upi_match = re.search(GENERIC_PATTERNS["upi"], line)
                account_match = re.search(GENERIC_PATTERNS["account"], line, re.IGNORECASE)
                mode_match = re.search(GENERIC_PATTERNS["mode"], line, re.IGNORECASE)
                phone_match = re.search(GENERIC_PATTERNS["phone"], line)
                ifsc_match = re.search(GENERIC_PATTERNS["ifsc"], line)

                counterparty = account_match.group(1) if account_match else None

                txn = NormalizedTransaction(
                    transaction_ref=ref_match.group(1) if ref_match else f"PDF-L{i}-{int(amount)}",
                    timestamp=timestamp,
                    amount=amount,
                    from_account=holder,
                    to_account=counterparty or (upi_match.group(1) if upi_match else "UNKNOWN_RECEIVER"),
                    transaction_type=mode_match.group(1).upper() if mode_match else None,
                    upi_id=upi_match.group(1) if upi_match else None,
                    narration=line.strip()[:500],
                    source_file=source_file,
                    confidence=0.65 if detected_bank else 0.55,
                    parser_notes=f"Regex L{i + 1} · {detected_bank or 'GENERIC'}" + (f" · IFSC:{ifsc_match.group(1)}" if ifsc_match else "")
                )
                transactions.append(txn)
            except Exception:
                continue

    return transactions
