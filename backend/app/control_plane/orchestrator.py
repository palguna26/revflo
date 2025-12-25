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
        pr_number = int(event.entity_id)
        # TODO: Trigger PR Validation Pipeline
        print(f"TODO: Run PR validation for PR #{pr_number}")
    
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
        """Issue created - generate checklist via Quantum"""
        issue_number = int(event.entity_id)
        # TODO: Trigger Quantum checklist generation
        print(f"TODO: Generate checklist for Issue #{issue_number}")
    
    async def _regenerate_checklist(self, event: InternalEvent):
        """Issue edited - regenerate checklist if needed"""
        issue_number = int(event.entity_id)
        # TODO: Check if checklist needs regeneration
        print(f"TODO: Check checklist update for Issue #{issue_number}")
    
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
        """Push to main - invalidate cached audits"""
        commit_sha = event.entity_id
        # TODO: Invalidate audit cache for this repo
        print(f"TODO: Invalidate audits for commit {commit_sha}")


# Singleton instance
orchestrator = Orchestrator()
