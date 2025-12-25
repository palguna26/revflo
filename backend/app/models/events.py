"""
Control Plane - Internal Event Model

Normalizes GitHub webhook events into internal events for orchestration.
"""
from typing import Literal, Optional, Any
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field


class InternalEvent(Document):
    """
    Internal event model - GitHub events normalized for RevFlo processing.
    
    Contract:
    - event_type: Standardized event name
    - repo_id: Reference to Repo document
    - entity_id: PR number, issue number, or commit SHA
    - payload: Normalized event data
    - processed: Orchestrator marks true after routing
    """
    event_type: Literal[
        "PR_OPENED",
        "PR_CLOSED", 
        "PR_MERGED",
        "PR_UPDATED",
        "PR_REOPENED",
        "ISSUE_CREATED",
        "ISSUE_UPDATED",
        "ISSUE_CLOSED",
        "ISSUE_REOPENED",
        "PUSH"
    ]
    
    repo_id: PydanticObjectId
    entity_id: str  # PR#, Issue#, or commit SHA
    
    payload: dict  # Normalized data
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processed_at: Optional[datetime] = None
    
    class Settings:
        name = "internal_events"
        indexes = [
            "repo_id",
            "event_type",
            "processed",
            "created_at"
        ]
