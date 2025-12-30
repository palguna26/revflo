"""
Git Diff Analyzer
Detects changed files between commits for incremental scans
"""
import logging
import subprocess
from typing import Set
from pathlib import Path

logger = logging.getLogger(__name__)


class GitDiffAnalyzer:
    """Analyzes git diffs to determine changed files"""
    
    async def get_changed_files(
        self,
        prev_commit_sha: str,
        curr_commit_sha: str,
        repo_path: Path
    ) -> Set[str]:
        """
        Get list of files changed between two commits.
        
        Args:
            prev_commit_sha: Previous commit SHA
            curr_commit_sha: Current commit SHA
            repo_path: Path to git repository
            
        Returns:
            Set of file paths (relative to repo root)
        """
        try:
            # Use git diff to get changed files
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    prev_commit_sha,
                    curr_commit_sha
                ],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Git diff failed: {result.stderr}")
                return set()  # Return empty set on error
            
            # Parse output into set of file paths
            changed_files = set()
            for line in result.stdout.splitlines():
                file_path = line.strip()
                if file_path:
                    changed_files.add(file_path)
            
            logger.info(f"Detected {len(changed_files)} changed files between {prev_commit_sha[:7]}..{curr_commit_sha[:7]}")
            return changed_files
            
        except subprocess.TimeoutExpired:
            logger.error("Git diff timed out")
            return set()
        except Exception as e:
            logger.error(f"Git diff error: {e}")
            return set()
    
    async def should_full_scan(
        self,
        prev_commit_sha: str,
        curr_commit_sha: str,
        repo_path: Path
    ) -> bool:
        """
        Determine if a full scan is needed (vs incremental).
        
        Full scan needed if:
        - No previous commit (first scan)
        - Too many files changed (>50% of repo)
        - Branch switch detected
        
        Returns:
            True if full scan recommended
        """
        if not prev_commit_sha:
            logger.info("No previous commit - full scan required")
            return True
        
        try:
            # Get total file count
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            total_files = len(result.stdout.splitlines())
            
            # Get changed files
            changed = await self.get_changed_files(
                prev_commit_sha,
                curr_commit_sha,
                repo_path
            )
            
            # If >50% of files changed, do full scan
            if len(changed) > total_files * 0.5:
                logger.info(f"Large change detected ({len(changed)}/{total_files} files) - full scan")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining scan type: {e}")
            return True  # Default to full scan on error
