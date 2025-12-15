from datetime import datetime
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.models.repo import Repo
from app.models.user import User
from app.api.v1.endpoints.me import get_current_user
from app.core.security import decrypt_token

router = APIRouter(prefix="/repos", tags=["repos"])


import asyncio
from app.models.pr import PullRequest

async def sync_repo_stats(repo_doc: Repo, access_token: str):
    """
    Fetch fresh stats from GitHub and update local DB.
    Also recalculate health score based on local PR analysis.
    """
    # Token passed in is now decrypted (if called correctly below) OR we assume caller handles it.
    # Actually, looking at list_repos below, we pass current_user.access_token which IS encrypted.
    # So we should decrypt it here or in caller. Let's do it in caller for clarity, OR here.
    # To minimize changes, let's keep signature but assume caller passes decrypted, OR decrypt here.
    # It's safer to decrypt at the usage point if we're not sure.
    # BUT `list_repos` passes `current_user.access_token`. 
    # Let's decrypt it in `list_repos` and pass the raw token here.
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        
        # 1. Fetch PR Count & Issue Count via Search API (most accurate)
        # We run these in parallel
        pr_query = f"repo:{repo_doc.owner}/{repo_doc.name} type:pr state:open"
        issue_query = f"repo:{repo_doc.owner}/{repo_doc.name} type:issue state:open"
        
        try:
            pr_resp, issue_resp, repo_details_resp = await asyncio.gather(
                client.get(f"https://api.github.com/search/issues?q={pr_query}", headers=headers),
                client.get(f"https://api.github.com/search/issues?q={issue_query}", headers=headers),
                client.get(f"https://api.github.com/repos/{repo_doc.owner}/{repo_doc.name}", headers=headers)
            )

            if pr_resp.status_code == 200:
                repo_doc.pr_count = pr_resp.json().get("total_count", 0)
            
            if issue_resp.status_code == 200:
                repo_doc.issue_count = issue_resp.json().get("total_count", 0)
                
            if repo_details_resp.status_code == 200:
                data = repo_details_resp.json()
                repo_doc.last_activity = data.get("pushed_at")

        except Exception as e:
            print(f"Error syncing stats for {repo_doc.repo_full_name}: {e}")

    # 2. Recalculate Health Score based on LOCAL analyzed PRs
    # (We don't want to query GitHub for this, we use our cached analyses)
    local_prs = await PullRequest.find(
        PullRequest.repo_id == repo_doc.id,
        PullRequest.validation_status != "pending" # Only count analyzed PRs
    ).to_list()
    
    if local_prs:
        avg_score = sum(pr.health_score for pr in local_prs) / len(local_prs)
        repo_doc.health_score = int(avg_score)
    else:
        # Keep existing or default to 85 if never analyzed
        pass

    repo_doc.updated_at = datetime.utcnow()
    await repo_doc.save()
    return repo_doc


@router.get("", response_model=List[Repo])
async def list_repos(current_user: User = Depends(get_current_user)):
    repos = await Repo.find(
        {"repo_full_name": {"$in": current_user.managed_repos}}
    ).to_list()
    
    
    if not current_user.access_token:
        # return cached if no token (shouldn't happen for logged in user)
        return repos

    # Decrypt token once
    raw_token = decrypt_token(current_user.access_token)

    # Sync concurrently
    tasks = [sync_repo_stats(r, raw_token) for r in repos]
    synced_repos = await asyncio.gather(*tasks)
    
    return synced_repos


@router.get("/{owner}/{repo}", response_model=Repo)
async def get_repo_detail(
    owner: str, repo: str, current_user: User = Depends(get_current_user)
):
    r = await Repo.find_one(Repo.owner == owner, Repo.name == repo)
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repo not found"
        )
    return r


@router.get("/available", response_model=List[dict])
async def list_available_repos(current_user: User = Depends(get_current_user)):
    """
    List all repositories the user has access to on GitHub.
    Useful for selecting a new repo to add.
    """
    if not current_user.access_token:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GitHub token stored for user",
        )
    
    async with httpx.AsyncClient() as client:
        # Fetch up to 100 repos sorted by updated time
        raw_token = decrypt_token(current_user.access_token)
        resp = await client.get(
            "https://api.github.com/user/repos?sort=updated&per_page=100",
            headers={
                "Authorization": f"Bearer {raw_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"GitHub API error: {resp.text}",
            )
        
        repos = resp.json()
        
        # Return simplified list
        results = []
        for r in repos:
            results.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "private": r.get("private"),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "updated_at": r.get("updated_at")
            })
            
        return results


@router.post("/add", response_model=Repo, status_code=status.HTTP_201_CREATED)
async def add_repo(
    full_name: str = Body(..., embed=True),  # e.g. "owner/name"
    current_user: User = Depends(get_current_user),
):
    """
    Add an extra repository by full name to the user's managed repos.
    This fetches metadata from GitHub and upserts into the repos collection.
    """
    if "access_token" not in current_user.dict() or not current_user.access_token:
         # Note: in Beanie definition I added access_token, hopefully it's populated. 
         # previous code fetched from DB. Current `get_current_user` returns the User doc.
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GitHub token stored for user",
        )
    
    access_token: str = current_user.access_token

    try:
        owner, name = full_name.split("/", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="full_name must be in the form 'owner/name'",
        )

    raw_token = decrypt_token(access_token)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{name}",
            headers={
                "Authorization": f"Bearer {raw_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository not found on GitHub: {resp.text}",
            )
        repo_data = resp.json()

    now = datetime.utcnow()

    # Upsert repo
    repo = await Repo.find_one(Repo.repo_full_name == full_name)
    if not repo:
        repo = Repo(
            repo_full_name=full_name,
            owner=owner,
            name=name,
            health_score=85,
            is_installed=True,
            pr_count=repo_data.get("open_issues_count", 0),
            issue_count=repo_data.get("open_issues_count", 0),
            last_activity=repo_data.get("pushed_at"),
            updated_at=now
        )
    else:
         # Update existing
         repo.pr_count = repo_data.get("open_issues_count", 0)
         repo.issue_count = repo_data.get("open_issues_count", 0)
         repo.last_activity = repo_data.get("pushed_at")
         repo.updated_at = now
    
    await repo.save()

    # Ensure it's in the user's managed list
    if full_name not in current_user.managed_repos:
        current_user.managed_repos.append(full_name)
        current_user.updated_at = now
        await current_user.save()

    return repo
