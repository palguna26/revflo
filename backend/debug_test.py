import asyncio
import os
import sys

# Set Mock Env
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "test_db"
os.environ["GITHUB_CLIENT_ID"] = "test"
os.environ["GITHUB_CLIENT_SECRET"] = "test"
os.environ["GITHUB_REDIRECT_URI"] = "http://localhost"
os.environ["FRONTEND_URL"] = "http://localhost"
os.environ["GROQ_API_KEY"] = "test"
os.environ["SECRET_KEY"] = "test_secret_key_12345"

from unittest.mock import AsyncMock, patch, MagicMock

# Add path
sys.path.append(os.getcwd())

from app.services.issue_service import IssueService
from app.models.user import User

async def run():
    try:
        from mongomock_motor import AsyncMongoMockClient
        from app.core.database import init_db
        with patch("app.core.database.AsyncIOMotorClient", side_effect=AsyncMongoMockClient):
            await init_db()
            
        print("Starting manual test...")
        with patch("app.services.issue_service.github_service") as mock_gh:
            mock_gh.fetch_issues = AsyncMock(return_value=[
                {"number": 1, "title": "Test Issue", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "html_url": "http://github.com/o/r/issues/1"}
            ])
            
            # Create a plain mock for the Repo document (not async)
            mock_repo_doc = MagicMock()
            mock_repo_doc.id = "64f1c9d8e4b0d1e2f3a4b5c6"
            
            # Patch find_one to be an AsyncMock that returns the doc
            mock_find_future = AsyncMock(return_value=mock_repo_doc)
            
            with patch("app.models.repo.Repo.find_one", side_effect=mock_find_future):
                
                service = IssueService()
                user = User(login="test", access_token="encrypted", managed_repos=[])
                
                issues = await service.list_issues("owner", "repo", user)
                
                print(f"Retrieved {len(issues)} issues")
                if len(issues) == 1 and issues[0].title == "Test Issue":
                    print("SUCCESS")
                else:
                    print("FAILURE: Validation mismatch")

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
