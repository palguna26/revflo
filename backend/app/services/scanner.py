import asyncio
from datetime import datetime
from beanie import PydanticObjectId
from app.models.scan import ScanResult, Vulnerability
from app.models.repo import Repo

class ScannerService:
    async def trigger_scan(self, repo_id: PydanticObjectId):
        # Create a pending scan record
        scan = ScanResult(
            repo_id=repo_id,
            status="pending"
        )
        await scan.save()
        
        # Start background task (simulated here, but could be celery/rq)
        asyncio.create_task(self._process_scan(scan.id))
        return scan

    async def _process_scan(self, scan_id: PydanticObjectId):
        scan = await ScanResult.get(scan_id)
        if not scan:
            return

        scan.status = "processing"
        await scan.save()
        
        # Simulate scanning delay
        await asyncio.sleep(5)
        
        # Mock results
        # In real impl, we would pull repo, run 'pip-audit' or 'bandit'
        vulnerabilities = [
            Vulnerability(
                id="VULN-001",
                severity="medium",
                package_name="requests",
                description="Old version of requests has known CVE",
                fixed_version="2.31.0"
            )
        ]
        
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        scan.vulnerabilities = vulnerabilities
        scan.summary = "Found 1 vulnerability."
        await scan.save()

scanner_service = ScannerService()
