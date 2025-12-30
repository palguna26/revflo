"""
V3 Audit API Endpoints
Feature-flagged endpoints for testing staged multi-scan architecture

Phase 2: Test endpoint for Code Quality scanner
"""
from fastapi import APIRouter, HTTPException, Depends
from beanie import PydanticObjectId
from app.models.audit_v3 import AuditRun, DimensionScanResult
from app.models.repo import Repo
from app.services.audit.orchestrator_v3 import AuditOrchestratorV3
from app.core.config import get_settings
from app.core.auth import get_current_user
from app.models.user import User
import tempfile
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit/v3", tags=["audit-v3"])


@router.post("/repos/{owner}/{repo}/scan")
async def trigger_v3_audit(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger V3 audit scan.
    
    Phase 2: Runs Code Quality scanner if ENABLE_V3_CODE_QUALITY=true
    
    Returns AuditRun entity with pending status.
    """
    settings = get_settings()
    
    # Check feature flag
    if not settings.enable_v3_audit:
        raise HTTPException(
            status_code=503,
            detail="V3 Audit system not enabled. Set ENABLE_V3_AUDIT=true"
        )
    
    # Find repository
    repo_doc = await Repo.find_one(
        Repo.owner == owner,
        Repo.name == repo
    )
    
    if not repo_doc:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    try:
        # Create audit run
        orchestrator = AuditOrchestratorV3()
        
        # Get latest commit (simplified - in production, fetch from GitHub API)
        commit_sha = "HEAD"  # Placeholder
        
        audit_run = await orchestrator.create_audit_run(
            repo_id=repo_doc.id,
            commit_sha=commit_sha
        )
        
        logger.info(f"Created V3 audit run {audit_run.id} for {owner}/{repo}")
        
        # Phase 2: Execute in background (simplified - should use background tasks)
        # For testing, we'll execute synchronously
        
        # Create temp directory
        scan_dir = Path(tempfile.mkdtemp(prefix="v3_audit_"))
        
        try:
            # Clone repo (reuse V2 logic)
            from app.services.audit.scanner import AuditScanner
            v2_scanner = AuditScanner()
            
            repo_url = f"https://github.com/{owner}/{repo}"
            await v2_scanner._clone_repo(repo_url, repo_doc.github_token or "", scan_dir)
            
            # Execute V3 audit
            audit_run = await orchestrator.execute(
                audit_run_id=audit_run.id,
                scan_dir=scan_dir,
                repo_url=repo_url,
                github_token=repo_doc.github_token or ""
            )
            
            logger.info(f"V3 audit run {audit_run.id} completed")
            
        finally:
            # Cleanup temp directory
            if scan_dir.exists():
                shutil.rmtree(scan_dir)
        
        return {
            "audit_run_id": str(audit_run.id),
            "status": audit_run.status,
            "overall_score": audit_run.overall_score,
            "code_quality_scan_id": str(audit_run.code_quality_scan_id) if audit_run.code_quality_scan_id else None
        }
        
    except Exception as e:
        logger.error(f"V3 audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_audit_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get V3 audit run details.
    """
    settings = get_settings()
    
    if not settings.enable_v3_audit:
        raise HTTPException(status_code=503, detail="V3 Audit not enabled")
    
    try:
        audit_run = await AuditRun.get(PydanticObjectId(run_id))
        
        if not audit_run:
            raise HTTPException(status_code=404, detail="Audit run not found")
        
        # Fetch dimension scans
        scans = {}
        
        if audit_run.code_quality_scan_id:
            code_quality = await DimensionScanResult.get(audit_run.code_quality_scan_id)
            if code_quality:
                scans["code_quality"] = {
                    "score": code_quality.score,
                    "status": code_quality.status,
                    "findings_count": len(code_quality.findings),
                    "files_analyzed": code_quality.files_analyzed
                }
        
        return {
            "audit_run": {
                "id": str(audit_run.id),
                "repo_id": str(audit_run.repo_id),
                "commit_sha": audit_run.commit_sha,
                "status": audit_run.status,
                "overall_score": audit_run.overall_score,
                "total_issues": audit_run.total_issues,
                "started_at": audit_run.started_at.isoformat(),
                "completed_at": audit_run.completed_at.isoformat() if audit_run.completed_at else None
            },
            "scans": scans
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch audit run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/dimension/{dimension}")
async def get_dimension_scan(
    run_id: str,
    dimension: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed results for a specific dimension scan.
    """
    settings = get_settings()
    
    if not settings.enable_v3_audit:
        raise HTTPException(status_code=503, detail="V3 Audit not enabled")
    
    audit_run = await AuditRun.get(PydanticObjectId(run_id))
    
    if not audit_run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    
    # Get dimension scan ID
    scan_id = None
    if dimension == "code_quality":
        scan_id = audit_run.code_quality_scan_id
    # Add other dimensions in future phases
    
    if not scan_id:
        raise HTTPException(status_code=404, detail=f"No {dimension} scan found")
    
    scan = await DimensionScanResult.get(scan_id)
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "scan_type": scan.scan_type,
        "score": scan.score,
        "status": scan.status,
        "findings": [
            {
                "id": f.id,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "category": f.category,
                "file_path": f.file_path,
                "title": f.title,
                "description": f.description,
                "metrics": f.metrics
            }
            for f in scan.findings
        ],
        "metrics": scan.metrics,
        "files_analyzed": scan.files_analyzed,
        "duration_ms": scan.duration_ms
    }
