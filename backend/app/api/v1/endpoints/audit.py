from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from beanie import PydanticObjectId

from app.api.v1.endpoints.me import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.scan import ScanResult
from app.models.audit_schema import AuditResult, AuditCategories, Finding
# from app.services.audit.scanner import audit_scanner # We will implement inline or mock for now as per instructions
from app.core.security import decrypt_token

router = APIRouter(prefix="/repos", tags=["audit"])

# Helper to map ScanResult (DB) to AuditResult (API Response)
def map_to_audit_result(scan: ScanResult, repo_id: str) -> AuditResult:
    return AuditResult(
        audit_id=str(scan.id),
        repo_id=str(repo_id),
        commit_sha=scan.commit_sha or "HEAD",
        overall_score=scan.overall_score,
        risk_level=scan.risk_level,
        engine_version=scan.engine_version,
        created_at=scan.started_at,
        categories=scan.categories,
        findings=scan.findings,
        loc=0, # TODO: Store LOC in ScanResult
        language="TypeScript" # Placeholder
    )

@router.get("/{owner}/{repo}/audit", response_model=AuditResult)
async def get_repo_audit(
    owner: str, 
    repo: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest completed audit report for a repository.
    Does NOT trigger a new scan.
    """
    # 1. Resolve Repo
    r = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not r:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 2. Find latest completed scan
    scan = await ScanResult.find_one(
        ScanResult.repo_id == r.id,
        ScanResult.status == "completed",
        sort=[("started_at", -1)]
    )
    
    if not scan:
        # Return 204 or specific structure? API contract says "Frontend Must support empty".
        # Let's return 404 for "No audit found" so frontend handles it explicitly, 
        # or return a default empty structure.
        # User prompt: "If no audit exists: UI shows Empty State"
        # 404 is semantically correct for "Audit not found".
        raise HTTPException(status_code=404, detail="No audit found for this repository.")

    return map_to_audit_result(scan, str(r.id))

@router.post("/{repo_id}/audit/scan", response_model=ScanResult)
async def trigger_scan(
    repo_id: PydanticObjectId, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Explicitly trigger a new Codebase Health Audit.
    Constraint: 1 scan per 24 hours per repo (unless force=true, but we stick to rules).
    """
    repo = await Repo.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 1. Check Rate Limit
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_scan = await ScanResult.find_one(
        ScanResult.repo_id == repo_id,
        ScanResult.started_at > cutoff,
        ScanResult.status != "failed"
    )

    if recent_scan:
        raise HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. You can only scan this repository once every 24 hours."
        )

    # 2. Create Pending Scan Record
    new_scan = ScanResult(
        repo_id=repo_id,
        status="processing", # Start processing immediately in background
        commit_sha="HEAD", # In real app, fetch from GitHub
        started_at=datetime.utcnow()
    )
    await new_scan.save()

    # 3. Queue Background Task
    token = decrypt_token(current_user.access_token)
    background_tasks.add_task(run_static_analysis_task, str(new_scan.id), f"https://github.com/{repo.owner}/{repo.name}", token)
    
    return new_scan

async def run_static_analysis_task(scan_id: str, repo_url: str, token: str):
    """
    Mock Static Analysis + Heuristics (AST/Regex).
    Updates the ScanResult with findings.
    """
    scan = await ScanResult.get(scan_id)
    if not scan:
        return

    try:
        # Simulate Analysis Delay
        # await asyncio.sleep(2)
        
        # MOCKED RESULTS FOR DEMO/MVP
        # In a real impl, we would clone repo, run AST parse, check dependencies.
        
        # 1. Categories
        scan.categories = AuditCategories(
            security=85,
            performance=92,
            code_quality=78,
            architecture=60,
            maintainability=70,
            dependencies=88
        )
        
        # 2. Findings (Mock)
        scan.findings = [
            Finding(
                id="sec-1",
                severity="critical",
                file_path="backend/app/core/security.py",
                line=45,
                description="Hardcoded secret key detected",
                explanation="Detected a string literal that resembles an API key or secret."
            ),
            Finding(
                id="arch-1",
                severity="high",
                file_path="frontend/src/App.tsx",
                line=12,
                description="Circular dependency detected",
                explanation="App.tsx imports Dashboard, which imports App components."
            )
        ]
        
        scan.overall_score = 82
        scan.risk_level = "medium"
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        await scan.save()
        
    except Exception as e:
        print(f"Scan failed: {e}")
        scan.status = "failed"
        scan.summary = str(e)
        await scan.save()
