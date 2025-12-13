from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.models.repo import Repo
from app.api.v1.endpoints.me import get_current_user

router = APIRouter(prefix="/repos/{owner}/{repo}/settings", tags=["settings"])

@router.delete("")
async def delete_repo(
    owner: str, repo: str, current_user: User = Depends(get_current_user)
):
    full_name = f"{owner}/{repo}"
    
    # Remove from user managed list
    if full_name in current_user.managed_repos:
        current_user.managed_repos.remove(full_name)
        await current_user.save()
        
    # Optional: Delete the Repo document itself if no other users manage it
    # await Repo.find_one(Repo.repo_full_name == full_name).delete()
    
    return {"status": "deleted"}
