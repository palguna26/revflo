from typing import List

from fastapi import APIRouter, Depends
from app.models.notification import Notification
from app.models.user import User
from app.api.v1.endpoints.me import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[Notification])
async def list_notifications(current_user: User = Depends(get_current_user)):
    # Assuming user_id stored as string in Notification.user_id 
    # (based on previous model/schema). 
    # Beanie model has user_id: str
    return await Notification.find(
        Notification.user_id == str(current_user.id)
    ).sort("-created_at").to_list()
