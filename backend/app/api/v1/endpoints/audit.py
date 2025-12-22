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

# ... (rest of imports)

@router.post("/{repo_id}/audit/scan", response_model=ScanResult)
async def trigger_scan(
    repo_id: PydanticObjectId, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # ... (lines 65-99 same)
    
    # 3. Queue Background Task via Assistant (Layer 3: System Intelligence)
    token = decrypt_token(current_user.access_token)
    repo_url = f"https://github.com/{repo.owner}/{repo.name}"
    
    background_tasks.add_task(assistant.assess_risk, new_scan, repo_url, token)
    
    return new_scan
