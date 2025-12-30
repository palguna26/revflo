"""
Abstract Base Class for V3 Dimension Scanners
Defines the contract all dimension scanners must implement
"""
from abc import ABC, abstractmethod
from typing import Set, Dict, Any, List
from pathlib import Path
from app.models.audit_v3 import DimensionScanResult, Finding


class RepoContext:
    """Context data passed to scanners"""
    def __init__(
        self,
        repo_id: str,
        commit_sha: str,
        scan_dir: Path,
        repo_url: str,
        github_token: str
    ):
        self.repo_id = repo_id
        self.commit_sha = commit_sha
        self.scan_dir = scan_dir
        self.repo_url = repo_url
        self.github_token = github_token


class FileMetrics:
    """File-level metrics from cache"""
    def __init__(
        self,
        file_path: str,
        loc: int = 0,
        complexity: int = 0,
        indent_depth: int = 0,
        churn_90d: int = 0,
        has_test: bool = False,
        language: str = "unknown"
    ):
        self.file_path = file_path
        self.loc = loc
        self.complexity = complexity
        self.indent_depth = indent_depth
        self.churn_90d = churn_90d
        self.has_test = has_test
        self.language = language


class DimensionScanner(ABC):
    """
    Abstract base class for dimension scanners.
    
    Each dimension (Security, Performance, Code Quality, etc.)
    implements this interface.
    
    Key principles:
    1. Scores are deterministic (no AI in scoring)
    2. AI only explains findings, does not discover them
    3. Cache-aware (reuse metrics from FileMetricCache)
    """
    
    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """
        Returns dimension name: 'security', 'performance', 'code_quality',
        'architecture', 'maintainability', 'testing_confidence'
        """
        pass
    
    @abstractmethod
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """
        Run dimension-specific scan.
        
        Args:
            repo_context: Repository metadata and temp directory
            changed_files: Files that changed since last scan (for incremental)
            metric_cache: Pre-computed file metrics (from FileMetricCache)
            
        Returns:
            DimensionScanResult with score, findings, optional AI summary
            
        Implementation must:
        1. Apply deterministic rules to find issues
        2. Calculate score from findings (no AI)
        3. Optionally call AI for explanation (if score < 90)
        """
        pass
    
    @abstractmethod
    def calculate_score(self, findings: List[Finding]) -> int:
        """
        Calculate 0-100 score from findings.
        
        MUST be deterministic - no AI, no randomness.
        
        Typical algorithm:
            score = 100
            for finding in findings:
                if finding.severity == "critical": score -= 20
                elif finding.severity == "high": score -= 10
                elif finding.severity == "medium": score -= 5
                elif finding.severity == "low": score -= 2
            return max(0, score)
        
        Args:
            findings: List of issues discovered
            
        Returns:
            Integer score 0-100
        """
        pass
    
    async def should_run_ai(self, scan_result: DimensionScanResult) -> bool:
        """
        Determine if AI explanation is needed.
        
        Default logic (can be overridden):
        - Skip if no findings
        - Skip if score >= 90 (healthy)
        - Run if findings exist and score < 90
        
        Returns:
            True if AI should run
        """
        if len(scan_result.findings) == 0:
            return False
        
        if scan_result.score >= 90:
            return False
        
        return True
