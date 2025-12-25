"""
Control Plane - Sync Guard

Prevents stale UI by detecting when DB state diverges from GitHub.
"""
import hashlib
from typing import Literal, Optional
from app.models.pr import PullRequest
from app.models.issue import Issue
from datetime import datetime, timedelta


class SyncGuard:
    """
    Detects staleness between RevFlo DB and GitHub.
    
    Contract:
    - GitHub is source of truth
    - DB is a derived projection
    - When mismatch detected, DB loses
    """
    
    def __init__(self):
        self.staleness_threshold = timedelta(minutes=10)
    
    async def verify_freshness(
        self,
        entity_type: Literal["pr", "issue"],
        repo_id: str,
        entity_number: int
    ) -> dict:
        """
        Check if DB entity matches GitHub state.
        
        Returns:
            {
                "fresh": bool,
                "last_synced": datetime,
                "confidence": "fresh" | "stale" | "unknown"
            }
        """
        if entity_type == "pr":
            entity = await PullRequest.find_one(
                PullRequest.repo_id == repo_id,
                PullRequest.pr_number == entity_number
            )
        else:
            entity = await Issue.find_one(
                Issue.repo_id == repo_id,
                Issue.issue_number == entity_number
            )
        
        if not entity:
            return {"fresh": False, "confidence": "unknown"}
        
        last_synced = getattr(entity, "last_synced_at", None)
        if not last_synced:
            return {"fresh": False, "confidence": "unknown"}
        
        age = datetime.utcnow() - last_synced
        
        if age < timedelta(minutes=1):
            confidence = "fresh"
        elif age < self.staleness_threshold:
            confidence = "stale"
        else:
            confidence = "unknown"
        
        return {
            "fresh": age < self.staleness_threshold,
            "last_synced": last_synced,
            "confidence": confidence
        }
    
    def compute_state_hash(self, entity_data: dict) -> str:
        """
        Compute hash of GitHub state for staleness detection.
        
        Used to quickly detect if state changed without full comparison.
        """
        state_keys = ["state", "merged", "closed_at", "updated_at"]
        state_str = "|".join(str(entity_data.get(k, "")) for k in state_keys)
        
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]


# Singleton instance
sync_guard = SyncGuard()
