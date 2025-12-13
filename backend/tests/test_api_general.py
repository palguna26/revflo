import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    # Depending on if we have a root endpoint, strictly we have app mount at /api/v1
    # Often docs are at /api/v1/docs
    resp = await client.get("/api/v1/docs")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_auth_redirect(client: AsyncClient):
    resp = await client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert resp.status_code == 307
    assert "github.com/login/oauth" in resp.headers["location"]
