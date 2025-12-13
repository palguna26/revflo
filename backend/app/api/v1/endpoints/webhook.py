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
    """
    try:
        # 1. Find Repo in DB
        repo_doc = await Repo.find_one(Repo.repo_full_name == full_name)
        if not repo_doc:
            print(f"Webhook: Repo {full_name} not found in DB. Skipping.")
            return

        # 2. Find Valid User Token
        # Try to find the repo owner first, then fallback to any admin
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
            if action in ["opened", "synchronize", "reopened"]:
                print(f"Webhook: Syncing PR #{pr_number} for {full_name}")
                await pr_service.get_or_sync_pr(owner, repo_name, pr_number, user)
                
                # Check for "re-validation" or initial validation trigger if logic exists?
                # Scheduler handles pending, but we can trigger it here for faster response.
                # For now, get_or_sync just saves it. Validation happens via scheduler or manual trigger.
                pass

        elif event_type == "issues":
            action = payload.get("action")
            issue_number = payload.get("issue", {}).get("number")
            if action in ["opened", "edited", "reopened"]:
                print(f"Webhook: Syncing Issue #{issue_number} for {full_name}")
                # We need a dummy BG task here if the function requires it, 
                # or modify service to accept None. 
                # Current issue_service.get_or_sync_issue requires bg_tasks.
                # We can't pass the request's bg_tasks here since we are ALREADY in a bg task.
                # We need to run it directly.
                
                # Hack: IssueService expects BackgroundTasks to add "generation" task.
                # We can manually trigger the generation task if needed or mock the bg_tasks.
                
                # Simplified: Just fetch and save.
                # We will call a simplified sync method or mock the bg task behavior.
                # Let's use a workaround:
                
                class MockBG:
                    def add_task(self, func, *args, **kwargs):
                        # Create generic asyncio task
                        import asyncio
                        asyncio.create_task(func(*args, **kwargs))
                
                await issue_service.get_or_sync_issue(owner, repo_name, issue_number, user, MockBG())

    except Exception as e:
        print(f"Async Webhook Processing Error: {str(e)}")
