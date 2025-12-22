from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import BackgroundTasks

from app.models.pr import PullRequest
from app.models.repo import Repo
from app.models.user import User
from app.models.issue import Issue, ValidationResult
from app.schemas.models import PRSummary
from app.services.github import github_service
from app.services.assistant_service import assistant

class PRService:
    # ... (lines 13-113)

        # 4. AI Analysis (Verify Change Layer)
        r = await assistant.verify_change(pr_doc.title, description, diff, checklist_items)
        
        # 5. Update PR
        pr_doc.code_health = r.get("code_health", [])
        pr_doc.suggested_tests = r.get("suggested_tests", [])
        pr_doc.health_score = r.get("health_score", 0)
        pr_doc.summary = r.get("summary", "")
        
        manifest_items = []
        validated_lookup = {item.get("id"): item for item in r.get("checklist_items", []) if item.get("id")}
        
        for item in issue.checklist:
             res = validated_lookup.get(item.id)
             # Default to pending if AI didn't return it
             status = res["status"] if res and "status" in res else "pending"
             manifest_items.append({
                 "id": item.id,
                 "text": item.text,
                 "required": item.required,
                 "status": res["status"] if res else "pending",
                 "evidence": res.get("evidence") if res else None,
                 "reasoning": res.get("reasoning") if res else None,
                 "linked_tests": []
             })
             
        pr_doc.manifest = {"checklist_items": manifest_items}
        all_passed = all(i["status"] == "passed" for i in manifest_items)
        pr_doc.validation_status = "validated" if all_passed and manifest_items else "needs_work"
        pr_doc.updated_at = datetime.utcnow()
        await pr_doc.save()
        
        # 6. Update Issue History
        self._update_issue_history(issue, pr_number, validated_lookup)
        await issue.save()
        
        return pr_doc

    def _update_issue_history(self, issue: Issue, pr_number: int, result_map: dict):
        summary_updated = False
        for item in issue.checklist:
            res = result_map.get(item.id)
            if res:
                val = ValidationResult(
                    pr_number=pr_number,
                    status=res["status"],
                    evidence=res.get("evidence"),
                    reasoning=res.get("reasoning")
                )
                item.latest_validation = val
                item.validations.append(val)
                item.status = res["status"]
                summary_updated = True
        
        if summary_updated:
            issue.checklist_summary.total = len(issue.checklist)
            issue.checklist_summary.passed = sum(1 for i in issue.checklist if i.status == 'passed')
            issue.checklist_summary.failed = sum(1 for i in issue.checklist if i.status == 'failed')
            issue.checklist_summary.pending = sum(1 for i in issue.checklist if i.status == 'pending')

pr_service = PRService()
