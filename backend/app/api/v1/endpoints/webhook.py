from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.models.repo import Repo
from app.models.user import User
from app.services.pr_service import pr_service
from app.services.issue_service import issue_service

router = APIRouter(prefix="/webhook", tags=["webhooks"])

@router.post("")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle GitHub Webhooks.
    
    V2: Routes events through Control Plane.
    - EventIngestor: Normalizes GitHub event
    - Orchestrator: Routes to appropriate pipeline
    """
    try:
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event")
        
        if not event_type:
            return {"status": "ignored", "reason": "No event type"}

        if event_type == "ping":
            return {"status": "ok", "message": "Pong!"}

        # Extract Repo Info
        if "repository" not in payload:
            return {"status": "ignored"}
            
        repo_data = payload["repository"]
        full_name = repo_data.get("full_name")
        owner_login = repo_data.get("owner", {}).get("login")
        repo_name = repo_data.get("name")
        
        if not full_name:
            return {"status": "ignored"}

        # Add task to background - process through Control Plane
        background_tasks.add_task(
            process_via_control_plane,
            event_type,
            payload,
            full_name
        )
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"status": "error", "message": str(e)}


async def process_via_control_plane(event_type: str, payload: dict, full_name: str):
    """
    Process webhook via Control Plane.
    
    Flow:
    1. Find repo in DB
    2. EventIngestor: Normalize GitHub event → InternalEvent
    3. Orchestrator: Route InternalEvent → Pipeline handlers
    """
    from app.control_plane.event_ingestor import event_ingestor
    from app.control_plane.orchestrator import orchestrator
    
    try:
        # 1. Find Repo in DB
        repo_doc = await Repo.find_one(Repo.repo_full_name == full_name)
        if not repo_doc:
            print(f"Webhook: Repo {full_name} not found in DB. Skipping.")
            return

        # 2. Normalize GitHub event → Internal event
        internal_event = await event_ingestor.process_github_event(
            event_type,
            payload,
            repo_doc.id
        )
        
        if not internal_event:
            # Event type not handled
            return
        
        print(f"Control Plane: Created {internal_event.event_type} for {full_name}")
        
        # 3. Route to orchestrator
        await orchestrator.route_event(internal_event)
        
        print(f"Control Plane: Processed {internal_event.event_type}")

    except Exception as e:
        print(f"Control Plane Error: {str(e)}")


# V2: State Change Handlers

async def handle_pr_closed(repo_doc: Repo, pr_number: int, merged: bool):
    """Mark PR as closed/merged and freeze validation state."""
    from app.models.pr import PullRequest
    from datetime import datetime
    
    pr = await PullRequest.find_one(
        PullRequest.repo_id == repo_doc.id,
        PullRequest.pr_number == pr_number
    )
    
    if not pr:
        return
    
    pr.github_state = "closed"
    pr.closed_at = datetime.utcnow()
    pr.last_synced_at = datetime.utcnow()
    
    if merged:
        pr.merged = True
        pr.merged_at = datetime.utcnow()
        # Freeze health score - it's final
        print(f"PR #{pr_number} merged with final health score: {pr.health_score}")
    
    await pr.save()


async def handle_pr_reopened(repo_doc: Repo, pr_number: int, user):
    """Reopen PR and invalidate all cached analysis."""
    from app.models.pr import PullRequest
    from datetime import datetime
    
    pr = await PullRequest.find_one(
        PullRequest.repo_id == repo_doc.id,
        PullRequest.pr_number == pr_number
    )
    
    if not pr:
        return
    
    # Reopen state
    pr.github_state = "open"
    pr.merged = False
    pr.closed_at = None
    pr.merged_at = None
    
    # INVALIDATE all analysis - force re-validation
    pr.validation_status = "pending"
    pr.health_score = 0
    pr.code_health = []
    pr.suggested_tests = []
    pr.summary = None
    pr.recommended_for_merge = False
    
    pr.last_synced_at = datetime.utcnow()
    await pr.save()
    
    print(f"PR #{pr_number} reopened - all analysis invalidated")


async def handle_pr_updated(repo_doc: Repo, pr_number: int):
    """Handle new commits pushed to PR - invalidate validation."""
    from app.models.pr import PullRequest
    from datetime import datetime
    
    pr = await PullRequest.find_one(
        PullRequest.repo_id == repo_doc.id,
        PullRequest.pr_number == pr_number
    )
    
    if not pr:
        return
    
    # Invalidate validation since code changed
    pr.validation_status = "pending"
    pr.recommended_for_merge = False
    pr.last_synced_at = datetime.utcnow()
    
    await pr.save()
    print(f"PR #{pr_number} updated - validation reset to pending")


async def handle_issue_closed(repo_doc: Repo, issue_number: int):
    """Mark issue as closed."""
    from app.models.issue import Issue
    from datetime import datetime
    
    issue = await Issue.find_one(
        Issue.repo_id == repo_doc.id,
        Issue.issue_number == issue_number
    )
    
    if not issue:
        return
    
    issue.github_state = "closed"
    issue.closed_at = datetime.utcnow()
    issue.last_synced_at = datetime.utcnow()
    
    await issue.save()
    print(f"Issue #{issue_number} marked as closed")


async def handle_issue_reopened(repo_doc: Repo, issue_number: int):
    """Mark issue as reopened."""
    from app.models.issue import Issue
    from datetime import datetime
    
    issue = await Issue.find_one(
        Issue.repo_id == repo_doc.id,
        Issue.issue_number == issue_number
    )
    
    if not issue:
        return
    
    issue.github_state = "open"
    issue.closed_at = None
    issue.last_synced_at = datetime.utcnow()
    
    await issue.save()
    print(f"Issue #{issue_number} reopened")
