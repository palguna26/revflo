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
