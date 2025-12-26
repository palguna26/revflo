"""
Control Plane - Event Ingestor

Receives GitHub webhook events and normalizes them into internal events.
"""
from typing import Optional
from app.models.events import InternalEvent
from app.models.repo import Repo
from beanie import PydanticObjectId


class EventIngestor:
    """
    Normalizes GitHub webhooks into internal events.
    
    Contract:
    - Input: GitHub webhook (event_type, payload)
    - Output: InternalEvent stored in DB
    - Responsibility: Parsing only, no business logic
    """
    
    async def process_github_event(
        self,
        event_type: str,
        payload: dict,
        repo_id: PydanticObjectId
    ) -> Optional[InternalEvent]:
        """
        Normalize GitHub event → Internal event.
        
        Returns None if event should be ignored.
        """
        normalizer = self._get_normalizer(event_type)
        if not normalizer:
            return None
        
        internal_event = await normalizer(payload, repo_id)
        if internal_event:
            await internal_event.insert()
        
        return internal_event
    
    def _get_normalizer(self, event_type: str):
        """Route to appropriate normalizer"""
        normalizers = {
            "pull_request": self._normalize_pull_request,
            "issues": self._normalize_issues,
            "push": self._normalize_push,
        }
        return normalizers.get(event_type)
    
    async def _normalize_pull_request(
        self,
        payload: dict,
        repo_id: PydanticObjectId
    ) -> Optional[InternalEvent]:
        """Normalize pull_request events"""
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        pr_number = payload.get("number")
        
        if not pr_number:
            return None
        
        # Map GitHub action → Internal event type
        event_mapping = {
            "opened": "PR_OPENED",
            "synchronize": "PR_UPDATED",
            "reopened": "PR_REOPENED",
            "closed": "PR_MERGED" if pr_data.get("merged") else "PR_CLOSED"
        }
        
        event_type = event_mapping.get(action)
        if not event_type:
            return None
        
        return InternalEvent(
            event_type=event_type,
            repo_id=repo_id,
            entity_id=str(pr_number),
            payload={
                "pr_number": pr_number,
                "title": pr_data.get("title"),
                "author": pr_data.get("user", {}).get("login"),
                "merged": pr_data.get("merged", False),
                "base_sha": pr_data.get("base", {}).get("sha"),
                "head_sha": pr_data.get("head", {}).get("sha")
            }
        )
    
    async def _normalize_issues(
        self,
        payload: dict,
        repo_id: PydanticObjectId
    ) -> Optional[InternalEvent]:
        """Normalize issues events"""
        action = payload.get("action")
        issue_data = payload.get("issue", {})
        issue_number = issue_data.get("number")
        
        if not issue_number:
            return None
        
        event_mapping = {
            "opened": "ISSUE_CREATED",
            "edited": "ISSUE_UPDATED",
            "closed": "ISSUE_CLOSED",
            "reopened": "ISSUE_REOPENED"
        }
        
        event_type = event_mapping.get(action)
        if not event_type:
            return None
        
        return InternalEvent(
            event_type=event_type,
            repo_id=repo_id,
            entity_id=str(issue_number),
            payload={
                "issue_number": issue_number,
                "title": issue_data.get("title"),
                "body": issue_data.get("body"),
                "state": issue_data.get("state"),
                "html_url": issue_data.get("html_url")
            }
        )
    
    async def _normalize_push(
        self,
        payload: dict,
        repo_id: PydanticObjectId
    ) -> Optional[InternalEvent]:
        """Normalize push events"""
        ref = payload.get("ref", "")
        
        # Only process pushes to default branch
        if not ref.endswith("/main") and not ref.endswith("/master"):
            return None
        
        head_commit = payload.get("head_commit", {})
        commit_sha = head_commit.get("id")
        
        if not commit_sha:
            return None
        
        return InternalEvent(
            event_type="PUSH",
            repo_id=repo_id,
            entity_id=commit_sha,
            payload={
                "commit_sha": commit_sha,
                "message": head_commit.get("message"),
                "author": head_commit.get("author", {}).get("name"),
                "ref": ref
            }
        )


# Singleton instance
event_ingestor = EventIngestor()
