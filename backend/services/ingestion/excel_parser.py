import pandas as pd
from rapidfuzz import process, fuzz
from typing import List, Dict, Any, Generator
from datetime import datetime
import numpy as np

from models.schemas.ingest import TransactionRow

# Known standard column aliases for fuzzy matching
STANDARD_COLUMNS = {
    "timestamp": ["Txn Dt", "Date", "Date of Transaction", "Transaction Date", "Time", "Timestamp"],
    "amount": ["Amount", "Txn Amount", "Value", "Transaction Amount", "Credit", "Debit", "Withdrawal", "Deposit"],
    "from_account": ["Sender Account", "Remitter Account", "From", "Debit Account", "Source"],
    "to_account": ["Receiver Account", "Beneficiary Account", "To", "Credit Account", "Destination"],
    "transaction_ref": ["Txn Ref", "Reference Number", "RRN", "UTR", "Transaction ID", "Ref No"],
    "upi_id": ["UPI ID", "VPA", "Sender VPA", "Receiver VPA", "UPI"],
    "narration": ["Narration", "Remarks", "Description", "Particulars"],
    "transaction_type": ["Type", "Mode", "Txn Mode", "Channel"]
}

class FuzzyHeaderMatcher:
    def __init__(self, threshold: int = 75):
        self.threshold = threshold

    def map_columns(self, actual_columns: List[str]) -> Dict[str, str]:
        """Maps arbitrary Excel headers to standard schema keys."""
        mapping = {}
        for std_key, aliases in STANDARD_COLUMNS.items():
            best_match = None
            best_score = 0
            
            for actual_col in actual_columns:
                if actual_col in mapping.values():
                    continue # already mapped
                
                # Try matching against all aliases for this standard key
                match_result = process.extractOne(actual_col, aliases, scorer=fuzz.token_set_ratio)
                if match_result:
                    match_str, score, _ = match_result
                    if score > best_score and score >= self.threshold:
                        best_score = score
                        best_match = actual_col
            
            if best_match:
                mapping[std_key] = best_match
                
        return mapping

def clean_amount(val: Any) -> float:
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace('₹', '').replace(',', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def parse_excel_to_rows(file_path: str) -> Generator[TransactionRow, None, None]:
    """Reads Excel, normalizes columns via fuzzy match, yields TransactionRow objects."""
    # Assuming first sheet and headers are somewhat near the top.
    # In a robust system, we might need to find the header row dynamically.
    df = pd.read_excel(file_path, engine='openpyxl')
    
    # Drop completely empty rows and columns
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)
    
    matcher = FuzzyHeaderMatcher()
    col_mapping = matcher.map_columns(list(df.columns))
    
    # Check for critical missing columns
    if "amount" not in col_mapping or "timestamp" not in col_mapping:
        raise ValueError("Could not confidently identify Amount or Timestamp columns in the uploaded file.")
    
    for _, row in df.iterrows():
        # Fallback logic for missing accounts (use UPI ID if present)
        from_acc = str(row.get(col_mapping.get("from_account", ""), ""))
        to_acc = str(row.get(col_mapping.get("to_account", ""), ""))
        upi_id = str(row.get(col_mapping.get("upi_id", ""), ""))
        
        if from_acc == "nan" or not from_acc:
            from_acc = upi_id if (upi_id != "nan" and upi_id) else "UNKNOWN_SENDER"
            
        if to_acc == "nan" or not to_acc:
            to_acc = upi_id if (upi_id != "nan" and upi_id) else "UNKNOWN_RECEIVER"
            
        # Parse timestamp
        raw_ts = row.get(col_mapping.get("timestamp", ""))
        if pd.isna(raw_ts):
            ts = datetime.utcnow()
        elif isinstance(raw_ts, datetime):
            ts = raw_ts
        else:
            try:
                # Basic parsing, can be expanded for specific Indian formats DD/MM/YYYY
                ts = pd.to_datetime(raw_ts, dayfirst=True).to_pydatetime()
            except Exception:
                ts = datetime.utcnow()
                
        # Parse amount
        raw_amount = row.get(col_mapping.get("amount", ""))
        amount = clean_amount(raw_amount)
        if amount == 0:
            continue # Skip 0 amount transactions
            
        # Generate a transaction ref if missing
        tx_ref = str(row.get(col_mapping.get("transaction_ref", ""), ""))
        if tx_ref == "nan" or not tx_ref:
            tx_ref = f"AUTO_REF_{datetime.utcnow().timestamp()}_{amount}"
            
        yield TransactionRow(
            transaction_ref=tx_ref,
            timestamp=ts,
            amount=amount,
            from_account=from_acc,
            to_account=to_acc,
            transaction_type=str(row.get(col_mapping.get("transaction_type", ""), "UNKNOWN")),
            upi_id=upi_id if upi_id != "nan" else None,
            narration=str(row.get(col_mapping.get("narration", ""), "")),
            risk_flag="unknown"
        )
