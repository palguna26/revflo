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
    Respond 200 OK immediately and process in background.
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

        # Add task to background
        background_tasks.add_task(
            process_webhook_event, 
            event_type, 
            payload, 
            full_name, 
            owner_login, 
            repo_name
        )
        
        return {"status": "received"}
        
    except Exception as e:
        print(f"Webhook Error: {e}")
        # Return 200 even on error to prevent GitHub from retrying endlessly
        return {"status": "error", "message": str(e)}

async def process_webhook_event(event_type: str, payload: dict, full_name: str, owner: str, repo_name: str):
    """
    Async implementation of webhook logic.
    V2: Full state sync with GitHub
    """
    try:
        # 1. Find Repo in DB
        repo_doc = await Repo.find_one(Repo.repo_full_name == full_name)
        if not repo_doc:
            print(f"Webhook: Repo {full_name} not found in DB. Skipping.")
            return

        # 2. Find Valid User Token
        user = await User.find_one(User.login == owner)
        if not user or not user.access_token:
            user = await User.find_one(User.access_token != None)
        
        if not user:
            print(f"Webhook: No valid user token found for {full_name}.")
            return

        # 3. Route Event
        if event_type == "pull_request":
            action = payload.get("action")
            pr_number = payload.get("number")
            pr_data = payload.get("pull_request", {})
            
            if action in ["opened", "synchronize", "reopened"]:
                print(f"Webhook: Syncing PR #{pr_number} for {full_name}")
                await pr_service.get_or_sync_pr(owner, repo_name, pr_number, user)
                
                # V2: Smart invalidation on synchronize (new commits)
                if action == "synchronize":
                    await handle_pr_updated(repo_doc, pr_number)
                    
            elif action == "closed":
                merged = pr_data.get("merged", False)
                print(f"Webhook: PR #{pr_number} {'merged' if merged else 'closed'} for {full_name}")
                await handle_pr_closed(repo_doc, pr_number, merged)
                
            elif action == "reopened":
                print(f"Webhook: PR #{pr_number} reopened for {full_name}, invalidating analysis")
                await handle_pr_reopened(repo_doc, pr_number, user)

        elif event_type == "issues":
            action = payload.get("action")
            issue_number = payload.get("issue", {}).get("number")
            
            if action in ["opened", "edited", "reopened"]:
                print(f"Webhook: Syncing Issue #{issue_number} for {full_name}")
                
                class MockBG:
                    def add_task(self, func, *args, **kwargs):
                        import asyncio
                        asyncio.create_task(func(*args, **kwargs))
                
                await issue_service.get_or_sync_issue(owner, repo_name, issue_number, user, MockBG())
                
            elif action == "closed":
                print(f"Webhook: Issue #{issue_number} closed for {full_name}")
                await handle_issue_closed(repo_doc, issue_number)
                
            elif action == "reopened":
                print(f"Webhook: Issue #{issue_number} reopened for {full_name}")
                await handle_issue_reopened(repo_doc, issue_number)

    except Exception as e:
        print(f"Async Webhook Processing Error: {str(e)}")


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
