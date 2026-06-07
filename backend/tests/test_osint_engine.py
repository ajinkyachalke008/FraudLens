import pytest
from services.enrichment.osint_engine import OSINTEngine

@pytest.mark.asyncio
async def test_ip_intelligence_live():
    """Verify live IP API returns correct structure for a known IP."""
    result = await OSINTEngine.enrich_entity("IP", "8.8.8.8")
    assert result["type"] == "IP"
    assert "geolocation" in result["data"]
    assert result["data"]["geolocation"]["country"] == "United States"

@pytest.mark.asyncio
async def test_crypto_intelligence_fallback():
    """Verify Crypto engine falls back gracefully when API key is missing."""
    import os
    # Ensure it's not set
    os.environ["CHAINALYSIS_API_KEY"] = ""
    result = await OSINTEngine.enrich_entity("CRYPTO", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert result["type"] == "CRYPTO"
    assert "CHAINALYSIS_API_KEY not configured" in result["error"]

@pytest.mark.asyncio
async def test_unsupported_entity():
    """Verify unknown entity types return an error."""
    result = await OSINTEngine.enrich_entity("UNKNOWN_TYPE", "something")
    assert "error" in result
    assert result["error"] == "Unsupported entity type"
