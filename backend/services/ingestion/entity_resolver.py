"""
Entity Resolver — Normalizes and deduplicates account numbers, phone numbers,
and UPI VPAs across all parsed transactions using fuzzy matching.
"""
import re
import logging
from typing import List, Dict

from rapidfuzz import fuzz
from models.schemas.ingestion_multi import NormalizedTransaction

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """Normalize Indian phone numbers to 10-digit format."""
    if not phone:
        return phone
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('91') and len(digits) == 12:
        return digits[2:]
    if digits.startswith('0') and len(digits) == 11:
        return digits[1:]
    if len(digits) == 10:
        return digits
    return phone


def normalize_account(account_number: str) -> str:
    """Normalize account number — strip spaces, dashes, leading zeros."""
    if not account_number:
        return account_number
    clean = re.sub(r'[\s\-/]', '', account_number)
    # Don't strip zeros from short account numbers
    if len(clean) > 6:
        clean = clean.lstrip('0') or clean
    return clean


def normalize_upi(vpa: str) -> str:
    """Normalize UPI VPA to lowercase."""
    return vpa.lower().strip() if vpa else ""


def _build_alias_map(accounts: List[str], threshold: int = 90) -> Dict[str, str]:
    """Build a mapping from raw account IDs to canonical versions using fuzzy matching."""
    canonical_map: Dict[str, str] = {}
    canonical_list: List[str] = []

    for acc in accounts:
        if acc in canonical_map:
            continue

        # Check for fuzzy match to existing canonicals
        best_match = None
        best_score = 0
        for canonical in canonical_list:
            score = fuzz.ratio(acc, canonical)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = canonical

        if best_match:
            canonical_map[acc] = best_match
            logger.debug(f"Entity resolution: '{acc}' → '{best_match}' (score={best_score})")
        else:
            canonical_map[acc] = acc
            canonical_list.append(acc)

    return canonical_map


def resolve_entities(transactions: List[NormalizedTransaction]) -> List[NormalizedTransaction]:
    """
    Post-processing pass: normalize account IDs, UPI VPAs, and
    perform fuzzy deduplication of account references.
    """
    # Step 1: Normalize all accounts
    for txn in transactions:
        txn.from_account = normalize_account(txn.from_account)
        txn.to_account = normalize_account(txn.to_account)
        if txn.upi_id:
            txn.upi_id = normalize_upi(txn.upi_id)

    # Step 2: Collect all unique accounts for fuzzy dedup
    all_accounts = set()
    for txn in transactions:
        all_accounts.add(txn.from_account)
        all_accounts.add(txn.to_account)

    # Step 3: Build alias map
    alias_map = _build_alias_map(list(all_accounts))

    # Step 4: Apply canonical mapping
    resolved_count = 0
    for txn in transactions:
        new_from = alias_map.get(txn.from_account, txn.from_account)
        new_to = alias_map.get(txn.to_account, txn.to_account)
        if new_from != txn.from_account or new_to != txn.to_account:
            resolved_count += 1
        txn.from_account = new_from
        txn.to_account = new_to

    if resolved_count > 0:
        logger.info(f"Entity resolution: {resolved_count} transactions had account aliases resolved")

    return transactions
