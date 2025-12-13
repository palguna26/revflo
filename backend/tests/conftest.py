import pytest
import asyncio
import os
from unittest.mock import patch

# Setup Test Env Vars BEFORE importing app/config
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "test_db"
os.environ["GITHUB_CLIENT_ID"] = "test_client_id"
os.environ["GITHUB_CLIENT_SECRET"] = "test_client_secret"
os.environ["GITHUB_REDIRECT_URI"] = "http://localhost/callback"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["GROQ_API_KEY"] = "test_groq_key"
os.environ["SECRET_KEY"] = "super_secret_test_key_must_be_long_enough_for_security_utils"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

from httpx import AsyncClient
from app.main import app
from app.core.database import init_db
from app.core.config import get_settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    from mongomock_motor import AsyncMongoMockClient
    from app.core.database import init_db
    from app.core.config import get_settings
    
    # Patch the Client in database module or config
    # Since init_db instantiates AsyncIOMotorClient directly, we should patch it.
    with patch("app.core.database.AsyncIOMotorClient", side_effect=AsyncMongoMockClient):
        await init_db()
        yield

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
