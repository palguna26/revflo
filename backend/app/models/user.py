from typing import Optional, List
from datetime import datetime
from beanie import Document
from pydantic import Field

class User(Document):
    login: str
    avatar_url: str = ""
    name: Optional[str] = None
    email: Optional[str] = None
    managed_repos: List[str] = []
    access_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
