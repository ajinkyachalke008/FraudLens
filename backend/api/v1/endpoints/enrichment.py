from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import logging

from services.enrichment.ifsc_lookup import _IFSC_CACHE

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/ifsc/search")
async def search_ifsc(
    query: str = Query(..., min_length=2, description="Search by Bank Name, Branch, or IFSC code"),
    limit: int = Query(10, le=50)
) -> List[Dict[str, Any]]:
    """
    Lightning-fast in-memory search over the static IFSC dictionary.
    """
    results = []
    q = query.lower()
    
    for ifsc, data in _IFSC_CACHE.items():
        if (q in ifsc.lower() or 
            q in data.get("bank", "").lower() or 
            q in data.get("branch", "").lower()):
            
            result_item = {"ifsc": ifsc, **data}
            results.append(result_item)
            
            if len(results) >= limit:
                break
                
    return results

@router.get("/osint/{entity_type}")
async def get_osint_intelligence(
    entity_type: str,
    entity_value: str = Query(..., description="The exact IP, Phone, Email, or Domain to investigate"),
):
    """
    Unified OSINT Endpoint. Routes the entity to the simulated intelligence engine.
    """
    from services.enrichment.osint_engine import OSINTEngine
    
    result = await OSINTEngine.enrich_entity(entity_type, entity_value)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result
