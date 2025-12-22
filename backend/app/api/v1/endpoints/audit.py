from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from beanie import PydanticObjectId

from app.api.v1.endpoints.me import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.scan import ScanResult
from app.models.audit_schema import AuditResult, AuditCategories, Finding
from app.services.assistant_service import assistant
from app.core.security import decrypt_token

router = APIRouter(prefix="/repos/{owner}/{repo}/audit", tags=["audit"])

@router.post("/scan", response_model=ScanResult)
async def trigger_scan(
    owner: str,
    repo: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    repo_doc = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not repo_doc:
        raise HTTPException(status_code=404, detail="Repo not found")

    new_scan = ScanResult(
        repo_id=repo_doc.id,
        status="pending",
        created_at=datetime.utcnow()
    )
    await new_scan.save()
    
    # Check if user has token
    if not current_user.access_token:
        # Try to find an owner token if current user doesn't have one? 
        # For now assume current user must be auth'd with GitHub
        pass

    # 3. Queue Background Task via Assistant (Layer 3: System Intelligence)
    try:
        token = decrypt_token(current_user.access_token)
    except:
        token = "" # Handle missing token gracefully or let assistant fail
        
    repo_url = f"https://github.com/{owner}/{repo}"
    
    background_tasks.add_task(assistant.assess_risk, new_scan, repo_url, token)
    
    return new_scan

@router.get("", response_model=List[ScanResult])
async def list_audits(
    owner: str, 
    repo: str,
    current_user: User = Depends(get_current_user)
):
    repo_doc = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not repo_doc: return []
    return await ScanResult.find(ScanResult.repo_id == repo_doc.id).sort("-created_at").to_list()

@router.get("/latest", response_model=Optional[ScanResult])
async def get_latest_audit(
    owner: str, 
    repo: str,
    current_user: User = Depends(get_current_user)
):
    repo_doc = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not repo_doc: return None
    return await ScanResult.find(ScanResult.repo_id == repo_doc.id).sort("-created_at").first_or_none()
