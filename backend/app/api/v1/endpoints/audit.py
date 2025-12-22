from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from beanie import PydanticObjectId

from app.api.v1.endpoints.me import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.scan import ScanResult
from app.models.audit_schema import AuditResult, AuditCategories, Finding
from app.services.assistant_service import assistant # Unified Service
from app.core.security import decrypt_token

router = APIRouter(prefix="/repos", tags=["audit"])

@router.post("/{repo_id}/audit/scan", response_model=ScanResult)
async def trigger_scan(
    repo_id: PydanticObjectId, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    repo = await Repo.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    new_scan = ScanResult(
        repo_id=repo.id,
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
        
    repo_url = f"https://github.com/{repo.owner}/{repo.name}"
    
    background_tasks.add_task(assistant.assess_risk, new_scan, repo_url, token)
    
    return new_scan

@router.get("/{repo_id}/audit", response_model=List[ScanResult])
async def list_audits(
    repo_id: PydanticObjectId, 
    current_user: User = Depends(get_current_user)
):
    return await ScanResult.find(ScanResult.repo_id == repo_id).sort("-created_at").to_list()

@router.get("/{repo_id}/audit/latest", response_model=Optional[ScanResult])
async def get_latest_audit(
    repo_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    return await ScanResult.find_one(ScanResult.repo_id == repo_id).sort("-created_at")
