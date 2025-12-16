from datetime import datetime
from typing import Optional, List

import httpx
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.security import encrypt_token
from app.models.user import User
from app.models.repo import Repo

router = APIRouter(prefix="/auth/github", tags=["auth"])

async def _exchange_code_for_token(code: str) -> str:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed: no token")
    return token


async def _fetch_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def _fetch_github_repos(access_token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            params={
                "per_page": 20,
                "sort": "updated",
                "direction": "desc",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def _upsert_user_and_repos(access_token: str) -> User:
    gh_user = await _fetch_github_user(access_token)
    login = gh_user["login"]
    
    # 1. Update/Create User
    user = await User.find_one(User.login == login)
    if not user:
        user = User(
            login=login,
            avatar_url=gh_user.get("avatar_url", ""),
            name=gh_user.get("name"),
            email=gh_user.get("email"),
            access_token=encrypt_token(access_token),
            managed_repos=[]
        )
    else:
        user.avatar_url = gh_user.get("avatar_url", "")
        user.name = gh_user.get("name")
        user.email = gh_user.get("email")
        user.access_token = encrypt_token(access_token)
        user.updated_at = datetime.utcnow()
    
    # 2. Sync Repos
    raw_repos = await _fetch_github_repos(access_token)
    auto_managed: List[str] = []
    
    for r in raw_repos:
        full_name = r["full_name"]
        auto_managed.append(full_name)
        
        # Upsert Repo
        repo = await Repo.find_one(Repo.repo_full_name == full_name)
        if not repo:
            repo = Repo(
                repo_full_name=full_name,
                owner=r["owner"]["login"],
                name=r["name"],
                health_score=85, # placeholder
                is_installed=True,
                pr_count=r.get("open_issues_count", 0), # rough proxy
                issue_count=r.get("open_issues_count", 0),
                last_activity=r.get("pushed_at"),
                updated_at=datetime.utcnow()
            )
        else:
            repo.updated_at = datetime.utcnow()
            # Could update counts here if we trust the API snapshot
            
        await repo.save()
    
    if not user.managed_repos:
        user.managed_repos = auto_managed
        
    await user.save()
    return user


@router.get("/login")
async def github_login() -> RedirectResponse:
    settings = get_settings()
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "repo read:user user:email",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://github.com/login/oauth/authorize?{query}"
    return RedirectResponse(url)


@router.get("/callback")
async def github_callback(code: Optional[str] = None) -> Response:
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    settings = get_settings()
    access_token = await _exchange_code_for_token(code)
    user = await _upsert_user_and_repos(access_token)

    response = RedirectResponse(f"{settings.frontend_url}/auth/callback?token={user.id}")
    
    # Session cookie: store only the user id (hex string of ObjectId)
    response.set_cookie(
        "qr_session",
        value=str(user.id),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )
    return response


@router.get("/demo-login")
async def demo_login() -> Response:
    """
    Log in as the demo user without OAuth.
    """
    demo_login = "demo-user"
    user = await User.find_one(User.login == demo_login)
    
    if not user:
        # Fallback: create if it doesn't exist, though script is preferred
        # This ensures the button works even if script wasn't run
        user = User(
            login=demo_login,
            avatar_url="https://ui-avatars.com/api/?name=Demo+User&background=0D8ABC&color=fff",
            name="Demo User",
            email="demo@revflo.ai",
            access_token="demo-token-123",
            managed_repos=[]
        )
        await user.save()

    settings = get_settings()
    response = RedirectResponse(f"{settings.frontend_url}/dashboard?token={user.id}")
    
    # Session cookie: store only the user id
    is_prod = settings.environment == "production"
    response.set_cookie(
        "qr_session",
        value=str(user.id),
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
        path="/"
    )
    return response


@router.post("/logout")
async def logout(response: Response):
    """
    Clear the session cookie to log out the user.
    """
    settings = get_settings()
    is_prod = settings.environment == "production"
    response.delete_cookie(
        key="qr_session",
        httponly=True,
        secure=is_prod, 
        samesite="none" if is_prod else "lax",
        path="/"
    )
    return {"status": "logged_out"}
