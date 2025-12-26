"""
Control Plane - Orchestrator

Routes internal events to appropriate pipelines.
"""
from typing import Callable, Dict, List
from app.models.events import InternalEvent
from app.models.repo import Repo
from app.models.pr import PullRequest
from app.models.issue import Issue
from datetime import datetime


class Orchestrator:
    """
    Routes internal events to pipelines.
    
    Contract:
    - Input: InternalEvent
    - Output: Pipeline execution(s)
    - Marks event as processed
    """
    
    def __init__(self):
        # Event routing table
        self.routing_map: Dict[str, List[Callable]] = {
            "PR_OPENED": [self._trigger_pr_validation],
            "PR_UPDATED": [self._trigger_partial_validation],
            "PR_MERGED": [self._freeze_verdict],
            "PR_CLOSED": [self._freeze_verdict],
            "PR_REOPENED": [self._invalidate_pr],
            "ISSUE_CREATED": [self._generate_checklist],
            "ISSUE_UPDATED": [self._regenerate_checklist],
            "ISSUE_CLOSED": [self._mark_issue_closed],
            "ISSUE_REOPENED": [self._mark_issue_reopened],
            "PUSH": [self._invalidate_audits]
        }
    
    async def route_event(self, event: InternalEvent) -> None:
        """
        Route event to appropriate handlers.
        
        Marks event as processed after routing.
        """
        handlers = self.routing_map.get(event.event_type, [])
        
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Handler {handler.__name__} failed for {event.event_type}: {e}")
        
        # Mark as processed
        event.processed = True
        event.processed_at = datetime.utcnow()
        await event.save()
    
    # Event Handlers (Contract: Keep logic minimal, delegate to pipelines)
    
    async def _trigger_pr_validation(self, event: InternalEvent):
        """PR opened - run full validation pipeline"""
        from app.pipelines.pr_validation import pr_validation_pipeline
        
        pr_number = int(event.entity_id)
        
        # Get PR from DB
        pr = await PullRequest.find_one(
            PullRequest.repo_id == event.repo_id,
            PullRequest.pr_number == pr_number
        )
        
        if pr:
            try:
                # Trigger validation pipeline
                await pr_validation_pipeline.run(pr)
                print(f"Orchestrator: PR validation triggered for PR #{pr_number}")
            except Exception as e:
                print(f"Orchestrator: PR validation failed for PR #{pr_number}: {e}")
    
    async def _trigger_partial_validation(self, event: InternalEvent):
        """PR updated (new commits) - partial re-validation"""
        pr_number = int(event.entity_id)
        
        pr = await PullRequest.find_one(
            PullRequest.repo_id == event.repo_id,
            PullRequest.pr_number == pr_number
        )
        
        if pr:
            # Invalidate validation (already implemented in webhook.py)
            pr.validation_status = "pending"
            pr.recommended_for_merge = False
            pr.last_synced_at = datetime.utcnow()
            await pr.save()
            
            # Could trigger partial re-validation here
            # await pr_validation_pipeline.run_partial(pr)
    
    async def _freeze_verdict(self, event: InternalEvent):
        """PR closed/merged - freeze final state"""
        pr_number = int(event.entity_id)
        
        pr = await PullRequest.find_one(
            PullRequest.repo_id == event.repo_id,
            PullRequest.pr_number == pr_number
        )
        
        if pr:
            merged = event.payload.get("merged", False)
            pr.github_state = "closed"
            pr.closed_at = datetime.utcnow()
            
            if merged:
                pr.merged = True
                pr.merged_at = datetime.utcnow()
            
            pr.last_synced_at = datetime.utcnow()
            await pr.save()
    
    async def _invalidate_pr(self, event: InternalEvent):
        """PR reopened - invalidate all analysis"""
        pr_number = int(event.entity_id)
        
        pr = await PullRequest.find_one(
            PullRequest.repo_id == event.repo_id,
            PullRequest.pr_number == pr_number
        )
        
        if pr:
            # Reopen and invalidate
            pr.github_state = "open"
            pr.merged = False
            pr.closed_at = None
            pr.merged_at = None
            pr.validation_status = "pending"
            pr.health_score = 0
            pr.code_health = []
            pr.suggested_tests = []
            pr.summary = None
            pr.last_synced_at = datetime.utcnow()
            await pr.save()
    
    async def _generate_checklist(self, event: InternalEvent):
        """Issue created - create issue record and generate checklist via Quantum"""
        issue_number = int(event.entity_id)
        
        # Get or create Issue document
        issue = await Issue.find_one(
            Issue.repo_id == event.repo_id,
            Issue.issue_number == issue_number
        )
        
        if not issue:
            # Create new issue record
            issue = Issue(
                repo_id=event.repo_id,
                issue_number=issue_number,
                title=event.payload.get("title", ""),
                description=event.payload.get("body", ""),
                status="open",
                github_url=event.payload.get("html_url", ""),
                github_state="open",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_synced_at=datetime.utcnow(),
                checklist=[],
                checklist_summary={"total": 0, "passed": 0, "failed": 0, "pending": 0}
            )
            await issue.save()
            print(f"Orchestrator: Created Issue #{issue_number}")
        
        # Generate checklist in background
        from app.services.issue_service import issue_service
        try:
            await issue_service.generate_checklist_now(issue)
            print(f"Orchestrator: Generated checklist for Issue #{issue_number}")
        except Exception as e:
            print(f"Orchestrator: Checklist generation failed for Issue #{issue_number}: {e}")
    
    async def _regenerate_checklist(self, event: InternalEvent):
        """Issue edited - update issue record and regenerate checklist if needed"""
        issue_number = int(event.entity_id)
        
        # Get or create Issue document
        issue = await Issue.find_one(
            Issue.repo_id == event.repo_id,
            Issue.issue_number == issue_number
        )
        
        if issue:
            # Update existing issue
            old_title = issue.title
            old_desc = issue.description
            
            issue.title = event.payload.get("title", issue.title)
            issue.description = event.payload.get("body", issue.description)
            issue.updated_at = datetime.utcnow()
            issue.last_synced_at = datetime.utcnow()
            await issue.save()
            
            # Regenerate checklist if title or description changed significantly
            if issue.title != old_title or issue.description != old_desc:
                from app.services.issue_service import issue_service
                try:
                    await issue_service.generate_checklist_now(issue)
                    print(f"Orchestrator: Regenerated checklist for Issue #{issue_number}")
                except Exception as e:
                    print(f"Orchestrator: Checklist regeneration failed for Issue #{issue_number}: {e}")
        else:
            # Issue not found, create it (fallback)
            await self._generate_checklist(event)
    
    async def _mark_issue_closed(self, event: InternalEvent):
        """Issue closed - update state"""
        issue_number = int(event.entity_id)
        
        issue = await Issue.find_one(
            Issue.repo_id == event.repo_id,
            Issue.issue_number == issue_number
        )
        
        if issue:
            issue.github_state = "closed"
            issue.closed_at = datetime.utcnow()
            issue.last_synced_at = datetime.utcnow()
            await issue.save()
    
    async def _mark_issue_reopened(self, event: InternalEvent):
        """Issue reopened - update state"""
        issue_number = int(event.entity_id)
        
        issue = await Issue.find_one(
            Issue.repo_id == event.repo_id,
            Issue.issue_number == issue_number
        )
        
        if issue:
            issue.github_state = "open"
            issue.closed_at = None
            issue.last_synced_at = datetime.utcnow()
            await issue.save()
    
    async def _invalidate_audits(self, event: InternalEvent):
        """Push to main - invalidate cached audits and trigger new audit"""
        from app.pipelines.repo_audit import repo_audit_pipeline
        from app.models.repo import Repo
        
        commit_sha = event.entity_id
        
        # Get repo
        repo = await Repo.find_one(Repo.id == event.repo_id)
        
        if repo:
            try:
                # Trigger new audit for this commit
                branch = event.payload.get("ref", "").split("/")[-1]  # Extract branch name
                await repo_audit_pipeline.run(repo, commit_sha, branch)
                print(f"Orchestrator: Audit triggered for commit {commit_sha[:7]}")
            except Exception as e:
                print(f"Orchestrator: Audit failed for {commit_sha[:7]}: {e}")


# Singleton instance
orchestrator = Orchestrator()
