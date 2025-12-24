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

@router.get("/history")
async def get_audit_history(
    owner: str,
    repo: str,
    days: int = 90,  # Default to last 90 days
    current_user: User = Depends(get_current_user)
):
    """
    Get historical audit data for time-series visualization.
    V2 Feature: Dashboard Time-Series
    
    Returns completed scans from the last N days with key metrics.
    """
    from datetime import datetime, timedelta
    
    repo_doc = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not repo_doc:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Calculate date threshold
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Query completed scans since date
    scans = await ScanResult.find(
        ScanResult.repo_id == repo_doc.id,
        ScanResult.status == "completed",
        ScanResult.started_at >= since_date
    ).sort("started_at").to_list()
    
    # Transform to time-series format
    history = []
    for scan in scans:
        # Count findings by severity
        findings_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        if scan.report and scan.report.top_risks:
            for risk in scan.report.top_risks:
                severity = risk.severity.lower() if hasattr(risk, 'severity') else 'medium'
                if severity in findings_count:
                    findings_count[severity] += 1
        
        history.append({
            "timestamp": scan.started_at.isoformat(),
            "overall_score": scan.overall_score or 0,
            "risk_level": scan.risk_level,
            "categories": {
                "maintainability": scan.categories.maintainability if scan.categories else 0,
                "security": scan.categories.security if scan.categories else 0,
                "performance": scan.categories.performance if scan.categories else 0,
                "code_quality": scan.categories.code_quality if scan.categories else 0,
                "architecture": scan.categories.architecture if scan.categories else 0,
                "dependencies": scan.categories.dependencies if scan.categories else 0
            },
            "findings_count": findings_count,
            "commit_sha": scan.commit_sha or "",
            "engine_version": scan.engine_version or "1.0.0"
        })
    
    return history
