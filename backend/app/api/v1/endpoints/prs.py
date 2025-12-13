from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.models.pr import PullRequest
from app.models.user import User
from app.schemas.models import PRSummary
from app.api.v1.endpoints.me import get_current_user
from app.services.pr_service import pr_service

router = APIRouter(prefix="/repos/{owner}/{repo}/prs", tags=["prs"])

@router.get("", response_model=List[PRSummary])
async def list_prs(
    owner: str, 
    repo: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="No GitHub token")
    try:
        return await pr_service.list_prs(owner, repo, current_user, background_tasks)
    except Exception as e:
        print(f"Error listing PRs: {str(e)}")
        return []

@router.get("/{pr_number}", response_model=PullRequest)
async def get_pr(
    owner: str, repo: str, pr_number: int, current_user: User = Depends(get_current_user)
):
    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="No GitHub token")
        
    pr = await pr_service.get_or_sync_pr(owner, repo, pr_number, current_user)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    return pr
    return pr

@router.post("/{pr_number}/revalidate")
async def revalidate_pr(
    owner: str, 
    repo: str, 
    pr_number: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Re-runs validation if the PR was previously validated against an Issue.
    """
    from app.models.issue import Issue
    # Find the issue that has this PR in its validations
    # We query for an Issue where ANY checklist item has a validation with this pr_number
    issue = await Issue.find_one({
        "checklist.validations.pr_number": pr_number,
        "repo_id": (await pr_service.get_or_sync_pr(owner, repo, pr_number, current_user)).repo_id
    })
    
    if not issue:
        raise HTTPException(status_code=400, detail="This PR has not been linked/validated against any Issue yet.")

    return await pr_service.run_review(owner, repo, issue.issue_number, pr_number, current_user)
