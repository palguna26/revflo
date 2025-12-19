from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from beanie import PydanticObjectId

from app.api.v1.endpoints.me import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.scan import ScanResult
from app.services.audit.scanner import audit_scanner
from app.core.security import decrypt_token

router = APIRouter(prefix="/repos/{repo_id}/audit", tags=["audit"])

@router.post("/scan", response_model=ScanResult)
async def trigger_scan(
    repo_id: PydanticObjectId, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger a new Codebase Health Audit.
    Constraint: 1 scan per 24 hours per repo.
    """
    repo = await Repo.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 1. Check Rate Limit (Last 24h)
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_scan = await ScanResult.find_one(
        ScanResult.repo_id == repo_id,
        ScanResult.started_at > cutoff,
        ScanResult.status != "failed" # Allow retries on failure? Prompt says "1 scan per day". Let's fail hard.
    )

    if recent_scan:
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. You can only scan this repository once every 24 hours."
        )

    # 2. Get Token (Assume user has access)
    # Ideally, we used the repo's installation token or user's token.
    # Using user's token for now as per GitHubService pattern.
    token = decrypt_token(current_user.access_token)
    repo_url = f"https://github.com/{repo.owner}/{repo.name}"

    # 3. Trigger Scan
    # audit_scanner trigger_scan launches background task itself but we can pass background_tasks if we refactored.
    # Current audit_scanner uses asyncio.create_task. Ideally we should use FastAPI BackgroundTasks for reliability.
    # But for now we call the service which handles it.
    
    scan = await audit_scanner.trigger_scan(repo_id, repo_url, token)
    return scan

@router.get("/latest", response_model=ScanResult)
async def get_latest_audit(
    repo_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest completed audit report.
    """
    scan = await ScanResult.find_one(
        ScanResult.repo_id == repo_id,
        ScanResult.status == "completed",
        sort=[("started_at", -1)]
    )
    if not scan:
        raise HTTPException(status_code=404, detail="No completed audit found.")
    return scan

@router.get("/{scan_id}", response_model=ScanResult)
async def get_audit_detail(
    repo_id: PydanticObjectId,
    scan_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific audit result.
    """
    scan = await ScanResult.find_one(
        ScanResult.id == scan_id,
        ScanResult.repo_id == repo_id
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Audit not found.")
    return scan
