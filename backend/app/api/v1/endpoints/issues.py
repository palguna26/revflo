from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.models.issue import Issue
from app.models.user import User
from app.api.v1.endpoints.me import get_current_user
from app.services.issue_service import issue_service

router = APIRouter(prefix="/repos/{owner}/{repo}/issues", tags=["issues"])

@router.get("", response_model=List[Issue])
async def list_issues(
    owner: str, 
    repo: str, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="No GitHub token stored")
    try:
        return await issue_service.list_issues(owner, repo, current_user, background_tasks)
    except Exception as e:
        # Fallback to empty if DB fails, or propagate error
        # In a real app we might want to log this
        print(f"Error listing issues: {e}")
        return []

@router.get("/{issue_number}", response_model=Issue)
async def get_issue_detail(
    owner: str, repo: str, issue_number: int, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="No GitHub token stored")
        
    issue = await issue_service.get_or_sync_issue(owner, repo, issue_number, current_user, background_tasks)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found (local or GitHub)")
    return issue

@router.post("/{issue_number}/checklist")
async def generate_issue_checklist(
    owner: str, 
    repo: str, 
    issue_number: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Explicitly trigger checklist generation for an issue.
    """
    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="No GitHub token stored")
        
    # We force sync first to ensure we have the body
    issue = await issue_service.get_or_sync_issue(owner, repo, issue_number, current_user, BackgroundTasks())
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
        
    try:
        # Generate and save
        updated_issue = await issue_service.generate_checklist_now(issue)
        return updated_issue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{issue_number}/pulls/{pr_number}/review")
async def run_pr_review_against_issue(
    owner: str, 
    repo: str, 
    issue_number: int, 
    pr_number: int, 
    current_user: User = Depends(get_current_user)
):
    from app.services.pr_service import pr_service
    
    if not current_user.access_token:
         raise HTTPException(status_code=400, detail="No GitHub token")
         
    try:
        pr_doc = await pr_service.run_review(owner, repo, issue_number, pr_number, current_user)
        if not pr_doc:
            raise HTTPException(status_code=404, detail="Repo/Issue/PR not found")
            
        # Refetch issue to return updated state
        issue = await issue_service.get_or_sync_issue(owner, repo, issue_number, current_user, BackgroundTasks())
        return {
            "issue": issue,
            "pr_analysis": pr_doc
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"REVIEW FAILED: {e}")
        raise HTTPException(status_code=500, detail=str(e))
