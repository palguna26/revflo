import os
import shutil
import subprocess
import asyncio
import logging
import httpx
from datetime import datetime
from collections import Counter
from typing import Dict, List, Any
from pathlib import Path
from beanie import PydanticObjectId
from groq import AsyncGroq

from app.models.scan import ScanResult, AuditReport, AuditSummary, FragilityMap, Roadmap
from app.models.repo import Repo
from app.core.config import get_settings
from app.services.audit.risk_engine import risk_engine
from app.services.audit.ai_audit import AuditAI

settings = get_settings()

logger = logging.getLogger(__name__)

def calculate_score(findings: List) -> int:
    """
    Calculate audit score from findings using V1 deterministic algorithm.
    
    V1 CONTRACT: This function must remain unchanged to preserve determinism.
    - Start at 100
    - Deduct per finding severity:
      - Critical: -15
      - High: -10
      - Medium: -5
      - Low: -2
    - Floor at 0
    
    Args:
        findings: List of RiskItem objects with severity attribute
        
    Returns:
        int: Score between 0-100
    """
    score = 100
    for risk in findings:
        if risk.severity == "critical": 
            score -= 15
        elif risk.severity == "high": 
            score -= 10
        elif risk.severity == "medium": 
            score -= 5
        elif risk.severity == "low": 
            score -= 2
    return max(0, score)  # Clamp to 0


class AuditScanner:
    def __init__(self):
        self.temp_dir = Path("/tmp/revflo_scans")
        if os.name == 'nt':
            self.temp_dir = Path(os.getenv('TEMP')) / "revflo_scans"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        # Initialize AI Service
        self.groq_client = AsyncGroq(api_key=settings.groq_api_key)
        self.ai_service = AuditAI(self.groq_client)

    async def trigger_scan(self, repo_id: PydanticObjectId, repo_url: str, token: str) -> ScanResult:
        scan = ScanResult(repo_id=repo_id, status="pending")
        await scan.save()
        asyncio.create_task(self._process_scan(scan, repo_url, token))
        return scan

    async def _process_scan(self, scan: ScanResult, repo_url: str, token: str):
        scan_dir = self.temp_dir / str(scan.id)
        try:
            scan.status = "processing"
            await scan.save()

            # --- Stage 1: Clone & Index ---
            logger.info(f"Cloning {repo_url}")
            await self._clone_repo(repo_url, token, scan_dir)
            
            file_stats = await self._index_files(scan_dir)
            complexity_map = await self._calculate_complexity(scan_dir)
            
            # Calculate churn using GitHub API (V1 Bug Fix)
            churn_map = await self._calculate_churn(repo_url, token, file_stats)
            
            # V2 Feature: Detect test coverage
            test_coverage_map = await self._detect_test_coverage(scan_dir, file_stats)

            
            # Enrich file_stats with complexity/metrics
            for stat in file_stats:
                m = complexity_map.get(stat['path'], {})
                stat['complexity'] = m.get('complexity', 0)
                stat['loc'] = m.get('loc', 0)
                stat['indent_depth'] = m.get('indent_depth', 0)
                stat['has_test'] = test_coverage_map.get(stat['path'], False)  # V2: Test coverage

            # --- Stage 2: Risk Analysis (Deterministic) ---
            top_risks = risk_engine.analyze(file_stats, churn_map)
            
            # --- Stage 3: Deterministic Scoring ---
            scan.overall_score = calculate_score(top_risks)
            
            # Set Risk Level based on Score
            if scan.overall_score >= 80: scan.risk_level = "low"
            elif scan.overall_score >= 60: scan.risk_level = "medium"
            elif scan.overall_score >= 40: scan.risk_level = "high"
            else: scan.risk_level = "critical"
            
            # --- Stage 4: AI Context & Explanation ---
            snippets = await self._extract_code_snippets(scan_dir, {f['path']: f.get('complexity', 0) for f in file_stats})
            
            repo_context = {
                "file_count": len(file_stats),
                "total_churn_commits": sum(churn_map.values()),
                "language_breakdown": self._get_language_breakdown(file_stats)
            }
            
            # AI explains the deterministic findings
            report = await self.ai_service.generate_insights(top_risks, repo_context, snippets)
            scan.report = report           

            # Set Categories (Heuristic mapping for now, can be refined)
            scan.categories.maintainability = scan.overall_score
            scan.categories.security = scan.overall_score # Placeholder until security scanner integrated
            scan.categories.performance = 80 # Default
            scan.categories.testing_confidence = 50 # Default
            scan.categories.code_quality = scan.overall_score
            scan.categories.architecture = scan.overall_score
            scan.categories.dependencies = 70

            scan.raw_metrics = {
                "file_count": len(file_stats),
                "complexity_avg": sum(complexity_map.values()) / len(complexity_map) if complexity_map else 0
            }
            
            # Get commit SHA for cache invalidation (PRD 6.1 requirement)
            try:
                parts = repo_url.strip("/").split("/")
                owner, repo_name = parts[-2], parts[-1]
                from app.services.github import github_service
                async with httpx.AsyncClient(
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"
                    },
                    timeout=10.0
                ) as client:
                    resp = await client.get(f"https://api.github.com/repos/{owner}/{repo_name}/commits/HEAD")
                    if resp.status_code == 200:
                        commit_data = resp.json()
                        scan.commit_sha = commit_data.get("sha", "")[:7]  # Short SHA
            except Exception as e:
                logger.warning(f"Could not fetch commit SHA: {e}")
            
            scan.status = "completed"
            scan.completed_at = datetime.utcnow()
            await scan.save()

            # Update Repo Metadata
            await self._update_repo_metadata(scan.repo_id, scan.id)

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            scan.status = "failed"
            scan.error_message = str(e)
            await scan.save()
        finally:
            if scan_dir.exists():
                try:
                    def remove_readonly(func, path, excinfo):
                        os.chmod(path, 0o777)
                        func(path)
                    shutil.rmtree(scan_dir, onerror=remove_readonly)
                except Exception:
                    pass

    async def _clone_repo(self, repo_url: str, token: str, target_dir: Path):
        # Fallback to ZIP download if git is not available
        import httpx
        from io import BytesIO
        import zipfile
        
        # repo_url format: https://github.com/owner/repo
        parts = repo_url.strip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        
        zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(zip_url, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"Failed to download repo: {resp.status_code}")
                
            with zipfile.ZipFile(BytesIO(resp.content)) as z:
                z.extractall(target_dir)
                
        # GitHub zipballs extract to a root folder like 'user-repo-sha', move contents up if needed
        # Or just let indexing handle recursive structures (which it already does)
        return

    async def _index_files(self, scan_dir: Path) -> List[Dict]:
        stats = []
        for root, _, files in os.walk(scan_dir):
            if ".git" in root: continue
            for file in files:
                file_path = Path(root) / file
                try:
                    rel_path = str(file_path.relative_to(scan_dir)).replace('\\', '/')
                    stats.append({
                        "path": rel_path,
                        "size": file_path.stat().st_size,
                        "ext": file_path.suffix
                    })
                except Exception:
                    pass
        return stats

    async def _calculate_complexity(self, scan_dir: Path) -> Dict[str, int]:
        metrics = {}
        for root, _, files in os.walk(scan_dir):
            if ".git" in root: continue
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.tsx', '.jsx')):
                    try:
                        path = Path(root) / file
                        rel_path = str(path.relative_to(scan_dir)).replace('\\', '/')
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            # Proxy complexity: Indentation > 4 chars (assuming 4 space indent) * Line Length
                            # Better proxy: count indentation levels
                            score = 0
                            for line in lines:
                                stripped = line.lstrip()
                                indent = len(line) - len(stripped)
                                if indent >= 8: score += 1 # Deep nesting
                                if len(line) > 120: score += 0.5 # Long lines
                            metrics[rel_path] = int(score)
                    except Exception:
                        pass
        return metrics

    async def _extract_code_snippets(self, scan_dir: Path, complexity_map: Dict[str, int]) -> Dict[str, str]:
        snippets = {}
        
        # 1. Always try to get README
        for readme_name in ["README.md", "readme.md", "README.txt"]:
            readme_path = scan_dir / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        snippets["README"] = f.read(2000) # First 2000 chars
                    break
                except: pass
        
        # 2. Get top 3 most complex files
        sorted_files = sorted(complexity_map.items(), key=lambda x: x[1], reverse=True)[:3]
        for rel_path, score in sorted_files:
            try:
                full_path = scan_dir / rel_path
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first 150 lines or 5000 chars
                    content = f.read(5000)
                    lines = content.splitlines()[:150]
                    snippets[rel_path] = "\n".join(lines)
            except: pass
            
        return snippets


    async def _calculate_churn(self, repo_url: str, token: str, file_stats: List[Dict]) -> Dict[str, int]:
        """
        Calculate churn (commit frequency) for files using GitHub API.
        
        Churn = number of commits touching a file in the last 90 days.
        This is a KEY METRIC for Hotspot detection (high complexity + high churn).
        
        V1 Preservation: Deterministic - same repo state → same churn values
        """
        from app.services.github import github_service
        
        # Extract owner/repo from URL
        parts = repo_url.strip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        
        churn_map = {}
        
        # To avoid API rate limits, only calculate churn for top complex files
        # or a sample of files (e.g., top 20 by size/complexity)
        files_to_check = sorted(
            [f for f in file_stats if f['path'].endswith(('.py', '.js', '.ts', '.java', '.cpp', '.tsx', '.jsx'))],
            key=lambda x: x.get('size', 0),
            reverse=True
        )[:20]  # Top 20 largest code files
        
        logger.info(f"Calculating churn for {len(files_to_check)} files...")
        
        for file in files_to_check:
            file_path = file['path']
            try:
                commit_count = await github_service.fetch_file_commits(
                    owner, repo, file_path, token, since_days=90
                )
                churn_map[file_path] = commit_count
                logger.debug(f"Churn for {file_path}: {commit_count} commits")
            except Exception as e:
                logger.warning(f"Could not fetch churn for {file_path}: {e}")
                churn_map[file_path] = 0  # Graceful degradation
        
        return churn_map

    async def _detect_test_coverage(self, scan_dir: Path, file_stats: List[Dict]) -> Dict[str, bool]:
        """
        V2 FEATURE: Detect if source files have corresponding test files.
        
        Test file patterns by language:
        - Python: test_*.py, *_test.py, tests/*.py
        - JavaScript/TypeScript: *.test.js, *.spec.js, *.test.ts, *.spec.ts
        - Java: *Test.java, tests/*
        
        Returns: Dict mapping file paths to boolean (has_test)
        """
        # Collect all test files
        test_files = set()
        test_patterns = [
            '*test*.py', '*spec*.py',
            '*test*.js', '*spec*.js',
            '*test*.ts', '*spec*.ts', '*test*.tsx', '*spec*.tsx',
            '*Test.java', '*Tests.java'
        ]
        
        for root, _, files in os.walk(scan_dir):
            if ".git" in root or "node_modules" in root:
                continue
            for file in files:
                file_lower = file.lower()
                # Check if it's a test file
                if any(pattern.replace('*', '') in file_lower for pattern in ['test', 'spec']):
                    file_path = Path(root) / file
                    try:
                        rel_path = str(file_path.relative_to(scan_dir)).replace('\\', '/')
                        test_files.add(rel_path)
                    except:
                        pass
        
        logger.info(f"Found {len(test_files)} test files")
        
        # Map source files to test coverage
        coverage_map = {}
        for stat in file_stats:
            path = stat['path']
            
            # Skip if it's already a test file
            if 'test' in path.lower() or 'spec' in path.lower():
                continue
            
            # Extract filename without extension
            file_name = Path(path).stem
            
            # Check if there's a corresponding test file
            has_test = any(
                file_name in test_file or test_file in path
                for test_file in test_files
            )
            
            coverage_map[path] = has_test
        
        return coverage_map


    def _get_language_breakdown(self, stats: List[Dict]) -> Dict[str, int]:
        cnt = Counter([s['ext'] for s in stats])
        return dict(cnt.most_common(5))

    async def _update_repo_metadata(self, repo_id: PydanticObjectId, scan_id: PydanticObjectId):
        repo = await Repo.get(repo_id)
        if repo:
            # We don't have latest_scan_id in Repo model yet, assume we might add it or just rely on queries
            # For now, just touch updated_at
            repo.updated_at = datetime.utcnow()
            await repo.save()

audit_scanner = AuditScanner()
