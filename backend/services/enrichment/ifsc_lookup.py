import os
import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Load the JSON master file into memory on module load
_IFSC_CACHE: Dict[str, dict] = {}
_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ifsc_master.json")

def _load_ifsc_data():
    global _IFSC_CACHE
    if not _IFSC_CACHE:
        try:
            with open(_DATA_FILE, "r", encoding="utf-8") as f:
                _IFSC_CACHE = json.load(f)
            logger.info(f"Loaded {_IFSC_CACHE.__len__()} IFSC records into memory.")
        except Exception as e:
            logger.error(f"Failed to load IFSC master data: {e}")

# Pre-load on import
_load_ifsc_data()

def lookup_ifsc(ifsc_code: str) -> Optional[dict]:
    """
    Lightning fast O(1) lookup of bank details from static JSON.
    Returns a dict with bank, branch, city, state, address, contact.
    """
    if not ifsc_code:
        return None
        
    code = ifsc_code.strip().upper()
    return _IFSC_CACHE.get(code)
