import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.issue_service import IssueService
from app.models.user import User

@pytest.mark.asyncio
async def test_issue_service_list_issues():
    # Mock GitHub Service
    with patch("app.services.issue_service.github_service") as mock_gh:
        mock_gh.fetch_issues = AsyncMock(return_value=[
            {"number": 1, "title": "Test Issue", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "html_url": "http://github.com/o/r/issues/1"}
        ])
        
        # Mock Repo lookup
        mock_repo_doc = MagicMock()
        mock_repo_doc.id = "64f1c9d8e4b0d1e2f3a4b5c6"
        
        mock_find_future = AsyncMock(return_value=mock_repo_doc)
        
        with patch("app.models.repo.Repo.find_one", side_effect=mock_find_future):
            
            service = IssueService()
            user = User(login="test", access_token="encrypted", managed_repos=[])
            
            issues = await service.list_issues("owner", "repo", user)
            
            assert len(issues) == 1
            assert issues[0].title == "Test Issue"
            assert issues[0].issue_number == 1
