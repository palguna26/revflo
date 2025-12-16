
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path so we can import app modules
backend_dir = os.path.join(os.path.dirname(__file__), "../backend")
sys.path.append(backend_dir)

# Load .env file manually since we are running from a different directory
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    print(f"Loading env from {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")
else:
    print("Warning: .env not found at", env_path)

from app.core.database import init_db
from app.models.user import User
from app.models.repo import Repo
from app.models.issue import Issue, IssueChecklistSummary, ChecklistItem
from app.models.pr import PullRequest, TestResult, CodeHealthIssue
from app.core.config import get_settings

async def populate_data():
    print("Initializing database...")
    await init_db()
    
    # 1. Create Demo User
    print("Creating demo user...")
    demo_login = "demo-user"
    user = await User.find_one(User.login == demo_login)
    if not user:
        user = User(
            login=demo_login,
            avatar_url="https://ui-avatars.com/api/?name=Demo+User&background=0D8ABC&color=fff",
            name="Demo User",
            email="demo@revflo.ai",
            access_token="demo-token-123", # Dummy token
            managed_repos=[]
        )
        await user.save()
        print(f"Created user: {demo_login}")
    else:
        print(f"User {demo_login} already exists. Updating...")
        user.avatar_url = "https://ui-avatars.com/api/?name=Demo+User&background=0D8ABC&color=fff"
        user.name = "Demo User"
        await user.save()

    # 2. Create Demo Repos
    print("Creating demo repos...")
    repos_data = [
        {
            "full_name": "demo/backend-service",
            "owner": "demo",
            "name": "backend-service",
            "health_score": 92,
            "pr_count": 3,
            "issue_count": 12,
            "description": "Main backend API service built with FastAPI",
            "language": "Python"
        },
        {
            "full_name": "demo/frontend-app",
            "owner": "demo",
            "name": "frontend-app",
            "health_score": 78,
            "pr_count": 5,
            "issue_count": 24,
            "description": "React-based frontend dashboard",
            "language": "TypeScript"
        },
        {
            "full_name": "demo/data-pipeline",
            "owner": "demo",
            "name": "data-pipeline",
            "health_score": 45,
            "pr_count": 8,
            "issue_count": 41,
            "description": "ETL pipeline for analytics",
            "language": "Python"
        }
    ]

    created_repo_names = []
    
    for r_data in repos_data:
        repo = await Repo.find_one(Repo.repo_full_name == r_data["full_name"])
        if not repo:
            repo = Repo(
                repo_full_name=r_data["full_name"],
                owner=r_data["owner"],
                name=r_data["name"],
                health_score=r_data["health_score"],
                is_installed=True,
                pr_count=r_data["pr_count"],
                issue_count=r_data["issue_count"],
                last_activity=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
                updated_at=datetime.utcnow()
            )
            await repo.save()
            print(f"Created repo: {r_data['full_name']}")
        
        created_repo_names.append(r_data["full_name"])

        # Create some Issues for this repo
        # Delete existing demo issues for this repo to avoid duplicates/confusion if re-run
        await Issue.find(Issue.repo_id == repo.id).delete()
        
        print(f"  Creating issues for {r_data['name']}...")
        for i in range(1, 4):
            issue = Issue(
                repo_id=repo.id,
                issue_number=i,
                title=f"Demo Issue {i} for {r_data['name']}",
                status="open",
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow(),
                checklist_summary=IssueChecklistSummary(total=5, passed=3, failed=1, pending=1),
                checklist=[
                    ChecklistItem(id="1", text="Unit tests included", required=True, status="passed"),
                    ChecklistItem(id="2", text="Documentation updated", required=True, status="failed"),
                    ChecklistItem(id="3", text="Lint check passed", required=True, status="passed"),
                    ChecklistItem(id="4", text="Integration tests", required=False, status="pending"),
                    ChecklistItem(id="5", text="Code review passed", required=True, status="passed"),
                ],
                github_url=f"https://github.com/{r_data['full_name']}/issues/{i}"
            )
            await issue.save()

        # Create some PRs for this repo
        # Delete existing demo PRs
        await PullRequest.find(PullRequest.repo_id == repo.id).delete()

        print(f"  Creating PRs for {r_data['name']}...")
        pr = PullRequest(
            repo_id=repo.id,
            pr_number=101,
            title=f"Feature: Add new database schema",
            author="dev-contributor",
            created_at=datetime.utcnow() - timedelta(days=1),
            github_url=f"https://github.com/{r_data['full_name']}/pull/101",
            health_score=r_data["health_score"],
            validation_status="validated" if r_data["health_score"] > 80 else "needs_work",
            test_results=[
                TestResult(test_id="t1", name="test_db_connection", status="passed", duration_ms=120),
                TestResult(test_id="t2", name="test_schema_migration", status="passed", duration_ms=450),
            ],
            code_health=[
                CodeHealthIssue(severity="medium", message="Function too long", file_path="db/models.py", line_number=45),
            ]
        )
        await pr.save()

    # Update user managed repos
    user.managed_repos = created_repo_names
    await user.save()
    
    print("Done! Demo data populated.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(populate_data())
