import httpx
from app.core.security import decrypt_token
from app.models.user import User
from typing import Optional, Dict, Any, List

class GitHubService:
    """
    Centralized GitHub API interactions with Token Decryption.
    """
    
    async def get_client(self, user: User) -> httpx.AsyncClient:
        token = decrypt_token(user.access_token)
        return httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )

    async def fetch_issue(self, owner: str, repo: str, issue_number: int, user: User) -> Optional[Dict]:
        async with await self.get_client(user) as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}")
            if resp.status_code == 404: return None
            resp.raise_for_status()
            return resp.json()

    async def fetch_issues(self, owner: str, repo: str, user: User, state: str="open") -> List[Dict]:
        async with await self.get_client(user) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                params={"state": state, "per_page": 20}
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_pr(self, owner: str, repo: str, pr_number: int, user: User) -> Optional[Dict]:
        async with await self.get_client(user) as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}")
            if resp.status_code == 404: return None
            resp.raise_for_status()
            return resp.json()

    async def fetch_prs(self, owner: str, repo: str, user: User) -> List[Dict]:
        async with await self.get_client(user) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                params={"state": "open", "per_page": 20}
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_pr_diff(self, owner: str, repo: str, pr_number: int, user: User) -> str:
        token = decrypt_token(user.access_token)
        async with httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3.diff"
            },
            follow_redirects=True
        ) as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}")
            resp.raise_for_status()
            return resp.text

    async def fetch_file_commits(self, owner: str, repo: str, file_path: str, token: str, since_days: int = 90) -> int:
        """
        Fetch commit count for a specific file over the past N days.
        Used for churn metric calculation.
        
        Returns: Number of commits touching this file in the time window.
        """
        from datetime import datetime, timedelta
        
        since_date = (datetime.utcnow() - timedelta(days=since_days)).isoformat()
        
        async with httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            timeout=30.0
        ) as client:
            try:
                # GitHub API: Get commits for a specific file
                resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/commits",
                    params={"path": file_path, "since": since_date, "per_page": 100}
                )
                
                if resp.status_code == 404:
                    return 0
                    
                resp.raise_for_status()
                commits = resp.json()
                return len(commits)
                
            except Exception as e:
                # Graceful degradation: if API fails, return 0 (no churn data)
                return 0


github_service = GitHubService()
