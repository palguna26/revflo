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

@router.post("/sync")
async def sync_issues_from_github(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user)
):
    """
    Manually sync all issues from GitHub for this repository.
    Useful for initial setup or catching up on missed webhooks.
    """
    from app.models.repo import Repo
    from app.core.security import decrypt_token
    import httpx
    from datetime import datetime
    
    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="No GitHub token stored")
    
    # Get repo
    repo_doc = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not repo_doc:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Fetch issues from GitHub
    token = decrypt_token(current_user.access_token)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"GitHub API error: {resp.text}")
        
        gh_issues = resp.json()
    
    # Sync each issue to DB
    synced_count = 0
    for gh_issue in gh_issues:
        # Skip pull requests (they show up in issues API)
        if "pull_request" in gh_issue:
            continue
        
        issue_number = gh_issue.get("number")
        
        # Get or create issue
        issue = await Issue.find_one(
            Issue.repo_id== repo_doc.id,
            Issue.issue_number == issue_number
        )
        
        if not issue:
            issue = Issue(
                repo_id=repo_doc.id,
                issue_number=issue_number,
                title=gh_issue.get("title", ""),
                description=gh_issue.get("body", ""),
                status="open" if gh_issue.get("state") == "open" else "completed",
                github_url=gh_issue.get("html_url", ""),
                github_state=gh_issue.get("state", "open"),
                created_at=datetime.fromisoformat(gh_issue.get("created_at", "").replace("Z", "+00:00")),
                updated_at=datetime.utcnow(),
                last_synced_at=datetime.utcnow(),
                checklist=[],
                checklist_summary={"total": 0, "passed": 0, "failed": 0, "pending": 0}
            )
            await issue.save()
            synced_count += 1
        else:
            # Update existing
            issue.title = gh_issue.get("title", issue.title)
            issue.description = gh_issue.get("body", issue.description)
            issue.github_state = gh_issue.get("state", "open")
            issue.last_synced_at = datetime.utcnow()
            await issue.save()
    
    return {
        "success": True,
        "synced": synced_count,
        "total": len(gh_issues),
        "message": f"Synced {synced_count} new issues from GitHub"
    }

