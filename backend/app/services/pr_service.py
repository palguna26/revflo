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
from app.services.ai_review import ai_service

class PRService:
    async def list_prs(self, owner: str, repo_name: str, user: User, bg_tasks: BackgroundTasks = None) -> List[PRSummary]:
        repo = await Repo.find_one(Repo.owner == owner, Repo.name == repo_name)
        if not repo:
            return []

        # 1. Return DB Cache immediately
        local_prs = await PullRequest.find(PullRequest.repo_id == repo.id).sort("-pr_number").to_list()
        
        # 2. Trigger Background Sync
        if bg_tasks:
            bg_tasks.add_task(self.sync_prs_bg, owner, repo_name, user, repo.id)
            
        # Map to summary
        results = []
        for pr in local_prs:
            results.append(PRSummary(
                pr_number=pr.pr_number,
                title=pr.title,
                author=pr.author,
                created_at=pr.created_at,
                github_url=pr.github_url,
                health_score=pr.health_score,
                validation_status=pr.validation_status,
                head_sha=pr.head_sha,
                state=pr.state,
                repo_full_name=f"{owner}/{repo_name}"
            ))
        return results

    async def sync_prs_bg(self, owner: str, repo_name: str, user: User, repo_id: PydanticObjectId):
        try:
            gh_prs = await github_service.fetch_prs(owner, repo_name, user)
            for item in gh_prs:
                num = item["number"]
                
                # Fetch or Create
                pr = await PullRequest.find_one(PullRequest.repo_id == repo_id, PullRequest.pr_number == num)
                if not pr:
                    pr = PullRequest(
                        repo_id=repo_id,
                        pr_number=num,
                        title=item["title"],
                        author=item["user"]["login"],
                        created_at=datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                        github_url=item["html_url"],
                        head_sha=item["head"]["sha"] if "head" in item else "0000000",
                        state=item.get("state", "open"),
                        validation_status="pending"
                    )
                else:
                    # Update basics
                    pr.title = item["title"]
                    pr.state = item.get("state", "open")
                    if "head" in item:
                        pr.head_sha = item["head"]["sha"]
                    pr.updated_at = datetime.utcnow()
                
                await pr.save()
        except Exception as e:
            print(f"Background PR Sync Error: {e}")

    async def get_or_sync_pr(self, owner: str, repo_name: str, pr_number: int, user: User) -> Optional[PullRequest]:
        repo = await Repo.find_one(Repo.owner == owner, Repo.name == repo_name)
        if not repo: return None
        
        pr = await PullRequest.find_one(PullRequest.repo_id == repo.id, PullRequest.pr_number == pr_number)
        if not pr:
            gh_data = await github_service.fetch_pr(owner, repo_name, pr_number, user)
            if not gh_data: return None
            
            pr = PullRequest(
                repo_id=repo.id,
                pr_number=pr_number,
                title=gh_data["title"],
                author=gh_data["user"]["login"],
                created_at=datetime.strptime(gh_data["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                github_url=gh_data["html_url"],
                head_sha=gh_data["head"]["sha"] if "head" in gh_data else "0000000",
                state=gh_data.get("state", "open"),
                validation_status="pending"
            )
            await pr.save()
            
        return pr

    async def run_review(self, owner: str, repo_name: str, issue_number: int, pr_number: int, user: User):
        # 1. Fetch Data
        repo = await Repo.find_one(Repo.owner == owner, Repo.name == repo_name)
        if not repo: return None
        
        issue = await Issue.find_one(Issue.repo_id == repo.id, Issue.issue_number == issue_number)
        pr_doc = await self.get_or_sync_pr(owner, repo_name, pr_number, user)
        if not issue or not pr_doc: return None
        
        # 2. Get Diff & Body via Service
        diff = await github_service.fetch_pr_diff(owner, repo_name, pr_number, user)
        # Hack: Get body from PR (we should store it, but for now fetch again or use existing if fresh)
        # Just fetch fresh PR data to be safe on body
        pr_data = await github_service.fetch_pr(owner, repo_name, pr_number, user)
        description = pr_data.get("body", "")
        
        # 3. Prepare Checklist
        checklist_items = [{"id": i.id, "text": i.text} for i in issue.checklist]
        
        # 4. AI Analysis
        r = await ai_service.perform_unified_review(pr_doc.title, description, diff, checklist_items)
        
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
