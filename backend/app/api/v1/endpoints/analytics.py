from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.models.user import User
from app.models.repo import Repo
from app.api.v1.endpoints.me import get_current_user

router = APIRouter(prefix="/repos/{owner}/{repo}/analytics", tags=["analytics"])

@router.get("/health_history")
async def get_health_history(
    owner: str, repo: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    # Verify access
    full_name = f"{owner}/{repo}"
    # In real app, check permissions more strictly
    
    repo_doc = await Repo.find_one(Repo.repo_full_name == full_name)
    if not repo_doc:
         raise HTTPException(status_code=404, detail="Repo not found")

    # Mock historical data for chart
    return {
        "dates": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "scores": [65, 78, 85],
        "issues_closed": [5, 12, 8]
    }
