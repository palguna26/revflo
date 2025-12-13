from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import BackgroundTasks

from app.models.issue import Issue, IssueChecklistSummary, ChecklistItem
from app.models.repo import Repo
from app.models.user import User
from app.services.github import github_service
from app.services.ai_review import ai_service
from bson import ObjectId

class IssueService:
    async def list_issues(self, owner: str, repo_name: str, user: User, bg_tasks: BackgroundTasks = None) -> List[Issue]:
        repo = await Repo.find_one(Repo.owner == owner, Repo.name == repo_name)
        if not repo:
            # If repo not found in DB but user has access, maybe simple list from GitHub? 
            # ideally we should have synced repo list previously.
            # Fallback to sync fetch if vital, or just return empty.
            # Let's try to sync fetching if repo missing? or just return empty.
            # Current flow implies repo must exist.
            return []

        # 1. Return DB Cache immediately
        issues = await Issue.find(Issue.repo_id == repo.id).sort("-issue_number").to_list()
        
        # 2. Trigger Background Sync
        if bg_tasks:
            bg_tasks.add_task(self.sync_issues_bg, owner, repo_name, user, repo.id)
            
        return issues

    async def sync_issues_bg(self, owner: str, repo_name: str, user: User, repo_id: PydanticObjectId):
        try:
            gh_issues = await github_service.fetch_issues(owner, repo_name, user)
            for iss in gh_issues:
                if "pull_request" in iss: continue
                
                # Update or Insert
                existing = await Issue.find_one(Issue.repo_id == repo_id, Issue.issue_number == iss["number"])
                if existing:
                    # Update fields if needed
                    existing.title = iss["title"]
                    existing.updated_at = datetime.strptime(iss["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                    existing.status = "open" # Reset to open if found in open list
                    await existing.save()
                else:
                    new_issue = Issue(
                        repo_id=repo_id,
                        issue_number=iss["number"],
                        title=iss["title"],
                        status="open",
                        created_at=datetime.strptime(iss["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                        updated_at=datetime.strptime(iss["updated_at"], "%Y-%m-%dT%H:%M:%SZ"),
                        checklist_summary=IssueChecklistSummary(total=0, passed=0, failed=0, pending=0),
                        checklist=[],
                        github_url=iss["html_url"]
                    )
                    await new_issue.save()
                    # Trigger analysis for new issue?
                    # Maybe better to do on-demand or separate loop to avoid spamming LLM
        except Exception as e:
            print(f"Background Sync Error: {e}")

    async def get_or_sync_issue(self, owner: str, repo_name: str, issue_number: int, user: User, bg_tasks: BackgroundTasks) -> Optional[Issue]:
        repo = await Repo.find_one(Repo.owner == owner, Repo.name == repo_name)
        if not repo: return None
        
        # Check DB
        issue = await Issue.find_one(Issue.repo_id == repo.id, Issue.issue_number == issue_number)
        
        if not issue:
            # Sync
            gh_data = await github_service.fetch_issue(owner, repo_name, issue_number, user)
            if not gh_data: return None
            
            issue = Issue(
                repo_id=repo.id,
                issue_number=issue_number,
                title=gh_data["title"],
                status="processing",
                created_at=datetime.strptime(gh_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                updated_at=datetime.strptime(gh_data["updated_at"], "%Y-%m-%dT%H:%M:%SZ"),
                checklist_summary=IssueChecklistSummary(total=0, passed=0, failed=0, pending=0),
                checklist=[],
                github_url=gh_data["html_url"]
            )
            await issue.save()
            
            # Trigger AI Analysis in Background
            bg_tasks.add_task(self._generate_checklist_task, issue.id, issue.title, gh_data.get("body", "") or "")
            
        return issue

    async def _generate_checklist_task(self, issue_id: PydanticObjectId, title: str, body: str):
        issue = await Issue.get(issue_id)
        if not issue: return
        
        checklist_data = await ai_service.generate_checklist(title, body)
        items = []
        for item in checklist_data:
            items.append(ChecklistItem(
                id=str(ObjectId()),
                text=item.get("text", ""),
                required=item.get("required", True),
                status="pending"
            ))
        
        issue.checklist = items
        issue.checklist_summary.total = len(items)
        issue.checklist_summary.pending = len(items)
        issue.status = "open"
        await issue.save()

    async def generate_checklist_now(self, issue: Issue) -> Issue:
        """
        Generates checklist immediately (blocking) for the Issue Page.
        """
        # 1. Generate text items
        items = await ai_service.generate_checklist(issue.title, "") 
        
        # 2. Map to ChecklistItem
        new_checklist = []
        import uuid
        for item in items:
            new_checklist.append(ChecklistItem(
                id=str(uuid.uuid4()),
                text=item.get("text", "No description"),
                required=item.get("required", True),
                status="pending"
            ))
            
        issue.checklist = new_checklist
        
        # Reset summary
        issue.checklist_summary = IssueChecklistSummary(
            total=len(new_checklist),
            passed=0, failed=0, pending=len(new_checklist)
        )
        issue.updated_at = datetime.utcnow()
        await issue.save()
        return issue

issue_service = IssueService()
