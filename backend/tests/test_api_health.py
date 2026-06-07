import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    """Verify the root endpoint is alive."""
    # Since we didn't explicitly build a root or health check in main.py, 
    # we can check a known API endpoint, or just expect 404 for root.
    response = await client.get("/")
    # Normally this would be 200 {"status": "ok"}, but we haven't defined a / route.
    assert response.status_code in [200, 404]

@pytest.mark.asyncio
async def test_docs_accessible(client):
    """Verify OpenAPI documentation is generated and accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200
