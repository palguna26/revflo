from typing import List
from bson import ObjectId
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.user import User
from app.models.repo import Repo
from app.models.pr import PullRequest
from app.models.issue import Issue
from app.schemas.models import User as UserSchema

router = APIRouter(tags=["me"])

async def get_current_user(request: Request) -> User:
    """
    Resolve the current user from the HTTP-only session cookie.
    """
    user_id = request.cookies.get("qr_session")
    
    # Fallback to Authorization header
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_id = auth_header.split(" ")[1]

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    
    try:
        # PydanticObjectId can just parse the string
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        # Invalid ObjectId
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


@router.get("/me", response_model=UserSchema)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/managed_repos", response_model=UserSchema)
async def update_managed_repos(
    managed_repos: List[str], current_user: User = Depends(get_current_user)
):
    """
    Update which repositories are managed by QuantumReview for this user.
    Frontend sends a list of repo_full_name strings (e.g. 'owner/name').
    """
    current_user.managed_repos = managed_repos
    await current_user.save()
    return current_user


@router.get("/me/recent-activity")
async def get_recent_activity(current_user: User = Depends(get_current_user)):
    """
    Get aggregated recent activity (PRs and Issues) across all managed repositories.
    """
    if not current_user.managed_repos:
        return {"prs": [], "issues": []}

    # 1. Get Repo IDs
    repos = await Repo.find(
        {"repo_full_name": {"$in": current_user.managed_repos}}
    ).to_list()
    repo_ids = [r.id for r in repos]
    
    # Map for easy lookup of repo name by ID
    repo_map = {r.id: {"owner": r.owner, "name": r.name} for r in repos}

    # 2. Fetch Recent PRs
    prs = await PullRequest.find(
        {"repo_id": {"$in": repo_ids}}
    ).sort("-created_at").limit(5).to_list()

    # 3. Fetch Recent Issues
    issues = await Issue.find(
        {"repo_id": {"$in": repo_ids}}
    ).sort("-created_at").limit(5).to_list()

    # 4. Format Result
    # (We return simplified structures similar to what PRCard/IssueCard expect)
    pr_data = []
    for pr in prs:
        repo_info = repo_map.get(pr.repo_id)
        if repo_info:
            pr_data.append({
                "pr_number": pr.pr_number,
                "title": pr.title,
                "author": pr.author,
                "health_score": pr.health_score or 0,
                "validation_status": pr.validation_status or "pending",
                "repo_owner": repo_info["owner"],
                "repo_name": repo_info["name"],
                "created_at": pr.created_at
            })

    issue_data = []
    for i in issues:
        repo_info = repo_map.get(i.repo_id)
        if repo_info:
            issue_data.append({
                "issue_number": i.issue_number,
                "title": i.title,
                "status": i.status,
                "checklist_summary": i.checklist_summary or {"total": 0, "passed": 0, "failed": 0, "pending": 0},
                "created_at": i.created_at,
                "repo_owner": repo_info["owner"],
                "repo_name": repo_info["name"]
            })

    # 5. Extract AI Insights from recent PRs
    insights = []
    seen_hashes = set()
    
    for pr in prs:
        repo_info = repo_map.get(pr.repo_id)
        if not repo_info: continue
        
        # Add Code Health Issues (Collect all, sort by severity later)
        for issue in pr.code_health:
            # Dedup based on message and file
            unique_key = f"{issue.message}-{issue.file_path}"
            if unique_key in seen_hashes: continue
            seen_hashes.add(unique_key)
            
            # severity map for sorting
            severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(issue.severity, 4)
            
            insights.append({
                "id": issue.id or str(ObjectId()),
                "type": "security" if "security" in str(issue.category).lower() else "optimization",
                "message": issue.message,
                "repo": f"{repo_info['owner']}/{repo_info['name']}",
                "severity": issue.severity,
                "file_path": issue.file_path,
                "_rank": severity_rank
            })
            
    # Sort by severity (Critical -> Low)
    insights.sort(key=lambda x: x["_rank"])
    
    # Limit to 5 top insights and remove temp rank
    insights = insights[:5]
    for i in insights:
        i.pop("_rank", None)

    return {
        "prs": pr_data,
        "issues": issue_data,
        "insights": insights
    }
