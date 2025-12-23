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

@router.post("/pr/{pr_number}/post-comments")
async def post_audit_to_pr(
    owner: str,
    repo: str,
    pr_number: int,
    severity_filter: str = "critical_high",  # Query param: all, critical_high, critical
    current_user: User = Depends(get_current_user)
):
    """
    Post the latest audit findings as comments on a GitHub PR.
    V2 Feature: PR Comment Integration
    
    Args:
        severity_filter: Filter for which findings to post
            - "all": All findings
            - "critical_high": Only critical and high severity (default)
            - "critical": Only critical severity
    """
    from app.services.pr_audit_service import pr_audit_service
    from app.services.github import github_service
    
    # Get the repository
    repo_doc = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not repo_doc:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get the latest completed audit scan
    scan = await ScanResult.find_one(
        ScanResult.repo_id == repo_doc.id,
        ScanResult.status == "completed"
    ).sort([("created_at", -1)])
    
    if not scan:
        raise HTTPException(
            status_code=404, 
            detail="No completed audit scans found. Please run an audit scan first."
        )
    
    # Ensure we have audit report with findings
    if not scan.report or not scan.report.top_risks:
        raise HTTPException(
            status_code=400,
            detail="Audit scan has no findings to post"
        )
    
    # Fetch PR details to get commit SHA
    try:
        pr_data = await github_service.fetch_pr(owner, repo, pr_number, current_user)
        if not pr_data:
            raise HTTPException(status_code=404, detail="Pull request not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch PR details: {str(e)}")
    
    commit_sha = pr_data["head"]["sha"]
    
    # Post findings to PR
    try:
        result = await pr_audit_service.post_audit_to_pr(
            owner, repo, pr_number,
            scan.report.top_risks,
            commit_sha,
            current_user,
            severity_filter
        )
        
        return {
            "status": "success",
            "pr_number": pr_number,
            "commit_sha": commit_sha[:7],
            "audit_id": str(scan.id),
            "posted_count": result["posted_count"],
            "error_count": result["error_count"],
            "warnings": result.get("warnings", []),
            "filtered_findings_count": result.get("filtered_findings_count", 0),
            "total_findings_count": result.get("total_findings_count", 0),
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post audit comments: {str(e)}"
        )
