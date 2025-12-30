"""
V3 Audit Orchestrator (Phase 3)
Coordinates multi-scan execution across dimensions

Phase 3: Runs all 6 dimension scanners in parallel
"""
import logging
import os
import asyncio
from typing import Dict
from pathlib import Path
from datetime import datetime
from beanie import PydanticObjectId
from app.models.audit_v3 import AuditRun
from app.services.audit.git_diff_analyzer import GitDiffAnalyzer
from app.services.audit.file_metric_cache import FileMetricCacheService
from app.services.audit.metric_computer import MetricComputer
from app.services.audit.churn_calculator import ChurnCalculator
from app.services.audit.test_coverage_detector import TestCoverageDetector
from app.services.audit.dimension_scanner import RepoContext, FileMetrics
from app.services.audit.scanners import (
    CodeQualityScanner,
    MaintainabilityScanner,
    TestingConfidenceScanner,
    ArchitectureScanner,
    PerformanceScanner,
    SecurityScanner
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AuditOrchestratorV3:
    """
    Orchestrates V3 audit runs across multiple dimensions.
    
    Phase 3: Runs all 6 dimension scanners in parallel
    """
    
    def __init__(self):
        self.git_analyzer = GitDiffAnalyzer()
        self.cache_service = FileMetricCacheService()
        self.churn_calculator = ChurnCalculator()
        self.test_detector = TestCoverageDetector()
        
        # Initialize all scanners
        self.code_quality_scanner = CodeQualityScanner()
        self.maintainability_scanner = MaintainabilityScanner()
        self.testing_scanner = TestingConfidenceScanner()
        self.architecture_scanner = ArchitectureScanner()
        self.performance_scanner = PerformanceScanner()
        self.security_scanner = SecurityScanner()
        
        self.settings = get_settings()
    
    async def create_audit_run(
        self,
        repo_id: PydanticObjectId,
        commit_sha: str
    ) -> AuditRun:
        """Create a new audit run."""
        audit_run = AuditRun(
            repo_id=repo_id,
            commit_sha=commit_sha,
            status="pending",
            started_at=datetime.utcnow()
        )
        
        await audit_run.save()
        logger.info(f"Created V3 audit run {audit_run.id} for commit {commit_sha[:7]}")
        
        return audit_run
    
    async def execute(
        self,
        audit_run_id: PydanticObjectId,
        scan_dir: Path,
        repo_url: str,
        github_token: str
    ) -> AuditRun:
        """
        Execute audit run - orchestrate all dimension scans in parallel.
        
        Phase 3: Runs all 6 scanners concurrently
        """
        audit_run = await AuditRun.get(audit_run_id)
        
        if not audit_run:
            raise ValueError(f"AuditRun {audit_run_id} not found")
        
        logger.info(f"Executing V3 audit run {audit_run_id}")
        audit_run.status = "running"
        await audit_run.save()
        
        try:
            # Step 1: Compute file metrics
            logger.info("Computing file metrics...")
            metric_cache = await self._compute_metrics(
                audit_run.repo_id,
                audit_run.commit_sha,
                scan_dir,
                repo_url,
                github_token
            )
            
            logger.info(f"Computed metrics for {len(metric_cache)} files")
            
            # Step 2: Create repo context for scanners
            repo_context = RepoContext(
                repo_id=str(audit_run.repo_id),
                commit_sha=audit_run.commit_sha,
                scan_dir=scan_dir,
                repo_url=repo_url,
                github_token=github_token
            )
            
            # Step 3: Run all 6 dimension scanners in parallel
            logger.info("Running all dimension scanners in parallel...")
            
            scanner_tasks = []
            
            # Always run all scanners (feature flags checked inside)
            scanner_tasks.append(
                self.code_quality_scanner.scan(repo_context, set(), metric_cache)
            )
            scanner_tasks.append(
                self.maintainability_scanner.scan(repo_context, set(), metric_cache)
            )
            scanner_tasks.append(
                self.testing_scanner.scan(repo_context, set(), metric_cache)
            )
            scanner_tasks.append(
                self.architecture_scanner.scan(repo_context, set(), metric_cache)
            )
            scanner_tasks.append(
                self.performance_scanner.scan(repo_context, set(), metric_cache)
            )
            scanner_tasks.append(
                self.security_scanner.scan(repo_context, set(), metric_cache)
            )
            
            # Execute all scanners concurrently
            scan_results = await asyncio.gather(*scanner_tasks, return_exceptions=True)
            
            # Step 4: Save scan results and link to audit run
            total_issues = 0
            score_sum = 0
            successful_scans = 0
            
            for result in scan_results:
                if isinstance(result, Exception):
                    logger.error(f"Scanner failed: {result}")
                    continue
                
                # Save scan result
                result.audit_run_id = audit_run.id
                await result.save()
                
                # Link to audit run
                if result.scan_type == "code_quality":
                    audit_run.code_quality_scan_id = result.id
                elif result.scan_type == "maintainability":
                    audit_run.maintainability_scan_id = result.id
                elif result.scan_type == "testing_confidence":
                    audit_run.testing_scan_id = result.id
                elif result.scan_type == "architecture":
                    audit_run.architecture_scan_id = result.id
                elif result.scan_type == "performance":
                    audit_run.performance_scan_id = result.id
                elif result.scan_type == "security":
                    audit_run.security_scan_id = result.id
                
                # Aggregate metrics
                total_issues += len(result.findings)
                score_sum += result.score
                successful_scans += 1
                
                logger.info(f"{result.scan_type.title()} scan: score={result.score}, findings={len(result.findings)}")
            
            # Step 5: Calculate overall score (average of dimension scores)
            if successful_scans > 0:
                audit_run.overall_score = int(score_sum / successful_scans)
            else:
                audit_run.overall_score = 0
            
            audit_run.total_issues = total_issues
            
            # Mark as completed
            audit_run.status = "completed"
            audit_run.completed_at = datetime.utcnow()
            await audit_run.save()
            
            logger.info(
                f"V3 audit run {audit_run_id} completed: "
                f"overall_score={audit_run.overall_score}, "
                f"total_issues={total_issues}, "
                f"successful_scans={successful_scans}/6"
            )
            return audit_run
            
        except Exception as e:
            logger.error(f"V3 audit run {audit_run_id} failed: {e}")
            audit_run.status = "failed"
            await audit_run.save()
            raise
    
    async def _compute_metrics(
        self,
        repo_id: PydanticObjectId,
        commit_sha: str,
        scan_dir: Path,
        repo_url: str = "",
        github_token: str = ""
    ) -> Dict[str, FileMetrics]:
        """
        Compute file metrics for all files in repo.
        
        Phase 4: Includes churn and test coverage
        """
        metrics_dict = {}
        file_paths = []
        
        # Step 1: Compute basic metrics (LOC, complexity, indent depth)
        for root, _, files in os.walk(scan_dir):
            # Skip .git
            if ".git" in root:
                continue
            
            # Skip test directories
            root_lower = root.lower()
            if any(pattern in root_lower for pattern in ['test', 'tests', '__test__', '__tests__', 'spec', 'specs']):
                continue
            
            for file in files:
                # Only analyze code files
                if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.tsx', '.jsx')):
                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(scan_dir)).replace('\\', '/')
                    
                    # Skip test files
                    rel_path_lower = rel_path.lower()
                    if any(pattern in rel_path_lower for pattern in ['test_', '_test.', 'test.', 'spec_', '_spec.', 'spec.']):
                        continue
                    
                    # Compute metrics
                    result = MetricComputer.analyze_file(file_path, rel_path)
                    
                    if result:
                        file_metrics = FileMetrics(
                            file_path=rel_path,
                            loc=result['loc'],
                            complexity=result['complexity'],
                            indent_depth=result['indent_depth'],
                            churn_90d=0,  # To be updated below
                            has_test=False,  # To be updated below
                            language=result['language']
                        )
                        
                        metrics_dict[rel_path] = file_metrics
                        file_paths.append(rel_path)
        
        logger.info(f"Computed basic metrics for {len(metrics_dict)} files")
        
        # Step 2: Calculate churn (Phase 4)
        if repo_url and github_token:
            try:
                logger.info("Calculating churn from GitHub API...")
                churn_map = await self.churn_calculator.calculate_churn(
                    repo_url, github_token, file_paths, days=90
                )
                
                # Update metrics with churn data
                for file_path, churn_count in churn_map.items():
                    if file_path in metrics_dict:
                        metrics_dict[file_path].churn_90d = churn_count
                
                logger.info(f"Updated churn for {len(churn_map)} files")
            except Exception as e:
                logger.warning(f"Churn calculation failed, skipping: {e}")
        
        # Step 3: Detect test coverage (Phase 4)
        try:
            logger.info("Detecting test coverage...")
            coverage_map = self.test_detector.detect_test_coverage(
                scan_dir, file_paths
            )
            
            # Update metrics with test coverage
            for file_path, has_test in coverage_map.items():
                if file_path in metrics_dict:
                    metrics_dict[file_path].has_test = has_test
        except Exception as e:
            logger.warning(f"Test detection failed, skipping: {e}")
        
        # Step 4: Store all metrics in cache
        for rel_path, file_metrics in metrics_dict.items():
            await self.cache_service.set_metrics(
                repo_id, commit_sha, rel_path, file_metrics
            )
        
        return metrics_dict
    
    async def get_audit_run(self, audit_run_id: PydanticObjectId) -> AuditRun:
        """Retrieve an audit run by ID"""
        audit_run = await AuditRun.get(audit_run_id)
        if not audit_run:
            raise ValueError(f"AuditRun {audit_run_id} not found")
        return audit_run
