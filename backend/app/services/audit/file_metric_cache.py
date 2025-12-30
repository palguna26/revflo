"""
File Metric Cache Service
Stores and retrieves file-level metrics to enable incremental scans
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from beanie import PydanticObjectId
from app.models.audit_v3 import FileMetricCache
from app.services.audit.dimension_scanner import FileMetrics

logger = logging.getLogger(__name__)


class FileMetricCacheService:
    """Service for managing file metric cache"""
    
    async def get_metrics(
        self,
        repo_id: PydanticObjectId,
        commit_sha: str,
        file_path: str
    ) -> Optional[FileMetrics]:
        """
        Retrieve cached metrics for a file.
        
        Returns None if cache miss or TTL expired.
        """
        cache_entry = await FileMetricCache.find_one(
            FileMetricCache.repo_id == repo_id,
            FileMetricCache.commit_sha == commit_sha,
            FileMetricCache.file_path == file_path
        )
        
        if not cache_entry:
            logger.debug(f"Cache miss: {file_path} @ {commit_sha[:7]}")
            return None
        
        # Check TTL
        age = datetime.utcnow() - cache_entry.computed_at
        if age.total_seconds() > cache_entry.ttl:
            logger.debug(f"Cache expired: {file_path} (age: {age.days} days)")
            await cache_entry.delete()  # Clean up expired entry
            return None
        
        logger.debug(f"Cache hit: {file_path} @ {commit_sha[:7]}")
        
        return FileMetrics(
            file_path=cache_entry.file_path,
            loc=cache_entry.loc,
            complexity=cache_entry.complexity,
            indent_depth=cache_entry.indent_depth,
            churn_90d=cache_entry.churn_90d,
            has_test=cache_entry.has_test,
            language=cache_entry.language
        )
    
    async def set_metrics(
        self,
        repo_id: PydanticObjectId,
        commit_sha: str,
        file_path: str,
        metrics: FileMetrics
    ) -> None:
        """
        Store metrics in cache.
        
        Upserts if entry already exists.
        """
        cache_entry = FileMetricCache(
            repo_id=repo_id,
            commit_sha=commit_sha,
            file_path=file_path,
            loc=metrics.loc,
            complexity=metrics.complexity,
            indent_depth=metrics.indent_depth,
            churn_90d=metrics.churn_90d,
            has_test=metrics.has_test,
            language=metrics.language,
            computed_at=datetime.utcnow()
        )
        
        # Find existing entry
        existing = await FileMetricCache.find_one(
            FileMetricCache.repo_id == repo_id,
            FileMetricCache.commit_sha == commit_sha,
            FileMetricCache.file_path == file_path
        )
        
        if existing:
            # Update existing
            existing.loc = metrics.loc
            existing.complexity = metrics.complexity
            existing.indent_depth = metrics.indent_depth
            existing.churn_90d = metrics.churn_90d
            existing.has_test = metrics.has_test
            existing.language = metrics.language
            existing.computed_at = datetime.utcnow()
            await existing.save()
            logger.debug(f"Cache updated: {file_path}")
        else:
            # Create new
            await cache_entry.save()
            logger.debug(f"Cache created: {file_path}")
    
    async def get_all_for_commit(
        self,
        repo_id: PydanticObjectId,
        commit_sha: str
    ) -> Dict[str, FileMetrics]:
        """
        Get all cached metrics for a commit.
        
        Returns dict: {file_path: FileMetrics}
        """
        entries = await FileMetricCache.find(
            FileMetricCache.repo_id == repo_id,
            FileMetricCache.commit_sha == commit_sha
        ).to_list()
        
        result = {}
        for entry in entries:
            # Skip expired
            age = datetime.utcnow() - entry.computed_at
            if age.total_seconds() > entry.ttl:
                continue
            
            result[entry.file_path] = FileMetrics(
                file_path=entry.file_path,
                loc=entry.loc,
                complexity=entry.complexity,
                indent_depth=entry.indent_depth,
                churn_90d=entry.churn_90d,
                has_test=entry.has_test,
                language=entry.language
            )
        
        logger.info(f"Loaded {len(result)} cached metrics for commit {commit_sha[:7]}")
        return result
    
    async def invalidate_old_entries(self, days: int = 30) -> int:
        """
        Clean up cache entries older than N days.
        
        Returns number of entries deleted.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        old_entries = await FileMetricCache.find(
            FileMetricCache.computed_at < cutoff
        ).to_list()
        
        count = len(old_entries)
        for entry in old_entries:
            await entry.delete()
        
        logger.info(f"Invalidated {count} cache entries older than {days} days")
        return count
