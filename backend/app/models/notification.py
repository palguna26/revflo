from datetime import datetime
from typing import Optional, Literal
from beanie import Document
from pydantic import Field

class Notification(Document):
    user_id: str  # Could be ObjectId link, but keeping as string to match previous pattern
    type: Literal["info", "warning", "error", "success"]
    message: str
    repo_full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False

    class Settings:
        name = "notifications"
