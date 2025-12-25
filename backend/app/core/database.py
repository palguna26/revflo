from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import get_settings
from app.models.user import User
from app.models.repo import Repo
from app.models.issue import Issue
from app.models.pr import PullRequest
from app.models.notification import Notification
from app.models.scan import ScanResult
from app.models.events import InternalEvent  # V2: Control Plane
from app.models.validation import Checklist, PRRun, Verdict  # V2: PR Validation Pipeline
from app.models.audit import AuditRun, AuditFinding  # V2: Audit Pipeline

async def init_db():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    
    await init_beanie(
        database=db,
        document_models=[
            User,
            Repo,
            Issue,
            PullRequest,
            Notification,
            ScanResult,
            InternalEvent,  # V2: Control Plane events
            Checklist,      # V2: PR Validation
            PRRun,
            Verdict,
            AuditRun,       # V2: Repo Audit
            AuditFinding
        ]
    )
