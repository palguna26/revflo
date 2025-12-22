from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import BackgroundTasks

from app.models.issue import Issue, IssueChecklistSummary, ChecklistItem
from app.models.repo import Repo
from app.models.user import User
from app.services.github import github_service
from app.services.assistant_service import assistant
from bson import ObjectId

class IssueService:
    # ... (lines 13-103 same)

    async def _generate_checklist_task(self, issue_id: PydanticObjectId, title: str, body: str):
        issue = await Issue.get(issue_id)
        if not issue: return
        
        # Use Assistant - Intent Layer
        checklist_data = await assistant.understand_intent(title, body)
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
        Preserves existing validation statuses if text matches.
        """
        # 1. Generate text items (Intent Layer)
        items = await assistant.understand_intent(issue.title, issue.description or "") 
        
        # 2. Map to ChecklistItem, preserving status
        existing_map = {item.text: item for item in issue.checklist}
        
        new_checklist = []
        import uuid
        
        passed_count = 0
        failed_count = 0
        pending_count = 0
        
        for item in items:
            text = item.get("text", "No description")
            existing = existing_map.get(text)
            
            if existing:
                # Preserve existing item state
                new_item = existing
            else:
                # Create new
                new_item = ChecklistItem(
                    id=str(uuid.uuid4()),
                    text=text,
                    required=item.get("required", True),
                    status="pending"
                )
            
            new_checklist.append(new_item)
            
            # Count stats
            if new_item.status == "passed": passed_count += 1
            elif new_item.status == "failed": failed_count += 1
            else: pending_count += 1
            
        issue.checklist = new_checklist
        
        # Reset summary
        issue.checklist_summary = IssueChecklistSummary(
            total=len(new_checklist),
            passed=passed_count, 
            failed=failed_count, 
            pending=pending_count
        )
        issue.updated_at = datetime.utcnow()
        await issue.save()
        return issue

issue_service = IssueService()
