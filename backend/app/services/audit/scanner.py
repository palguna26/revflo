import os
import shutil
import subprocess
import asyncio
import logging
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
            churn_map = await self._calculate_churn(scan_dir)
            
            # Enrich file_stats with complexity
            for stat in file_stats:
                stat['complexity'] = complexity_map.get(stat['path'], 0)

            # --- Stage 2: Risk Heuristics ---
            top_risks = risk_engine.analyze(file_stats, churn_map)
            
            # --- Stage 3: AI Insight ---
            repo_context = {
                "file_count": len(file_stats),
                "total_churn_commits": sum(churn_map.values()),
                "language_breakdown": self._get_language_breakdown(file_stats)
            }
            
            report = await self.ai_service.generate_insights(top_risks, repo_context)
            
            scan.report = report           
            scan.raw_metrics = {
                "file_count": len(file_stats),
                "complexity_avg": sum(complexity_map.values()) / len(complexity_map) if complexity_map else 0
            }
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
        auth_url = repo_url.replace("https://", f"https://oauth2:{token}@")
        # Full history needed for Churn, but limiting to depth 500 for performance
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "500", auth_url, str(target_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"Git clone failed: {stderr.decode()}")

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

    async def _calculate_churn(self, scan_dir: Path) -> Dict[str, int]:
        try:
            # git log -n 500 --name-only --format=""
            proc = await asyncio.create_subprocess_exec(
                "git", "log", "-n", "500", "--name-only", "--format=",
                cwd=str(scan_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode != 0: return {}
            
            files = stdout.decode().splitlines()
            # Clean empty lines and normalize paths
            cleaned = [f.strip().replace('\\', '/') for f in files if f.strip()]
            return dict(Counter(cleaned))
        except Exception:
            return {}

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
