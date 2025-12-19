from typing import Optional
from datetime import datetime
from beanie import Document
from pydantic import Field

class Repo(Document):
    repo_full_name: str
    owner: str
    name: str
    health_score: int = 0
    is_installed: bool = False
    pr_count: int = 0
    issue_count: int = 0
    private: bool = False
    description: Optional[str] = None
    html_url: Optional[str] = None
    last_activity: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "repos"
