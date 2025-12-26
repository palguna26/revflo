
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
from app.models.audit import AuditRun, AuditFinding
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
            # V2: Add github_state and last_synced_at
            is_open = i != 2  # Issue #2 will be closed for demo
            issue = Issue(
                repo_id=repo.id,
                issue_number=i,
                title=f"Demo Issue {i} for {r_data['name']}",
                status="open" if is_open else "completed",
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow(),
                checklist_summary=IssueChecklistSummary(total=5, passed=3, failed=1, pending=1),
                checklist=[
                    ChecklistItem(id="1", text="Unit tests included", required=True, status="passed"),
                    ChecklistItem(id="2", text="Documentation updated", required=True, status="failed" if is_open else "passed"),
                    ChecklistItem(id="3", text="Lint check passed", required=True, status="passed"),
                    ChecklistItem(id="4", text="Integration tests", required=False, status="pending"),
                    ChecklistItem(id="5", text="Code review passed", required=True, status="passed"),
                ],
                github_url=f"https://github.com/{r_data['full_name']}/issues/{i}",
                # V2: Control Plane sync fields
                github_state="open" if is_open else "closed",
                closed_at=None if is_open else datetime.utcnow() - timedelta(hours=5),
                last_synced_at=datetime.utcnow() - timedelta(seconds=30)
            )
            await issue.save()

        # Create some PRs for this repo
        # Delete existing demo PRs
        await PullRequest.find(PullRequest.repo_id == repo.id).delete()

        print(f"  Creating PRs for {r_data['name']}...")
        
        # Create multiple PRs with different states for demo
        prs_to_create = [
            {
                "number": 101,
                "title": "Feature: Add new database schema",
                "state": "open",
                "merged": False,
                "health_score": r_data["health_score"],
                "validation_status": "validated" if r_data["health_score"] > 80 else "needs_work",
                "days_ago": 1
            },
            {
                "number": 102,
                "title": "Fix: Resolve security vulnerability",
                "state": "closed",
                "merged": True,
                "health_score": 95,
                "validation_status": "validated",
                "days_ago": 3
            },
            {
                "number": 103,
                "title": "Refactor: Improve API response time",
                "state": "open",
                "merged": False,
                "health_score": 72,
                "validation_status": "pending",
                "days_ago": 0.5
            }
        ]
        
        for pr_data in prs_to_create:
            pr = PullRequest(
                repo_id=repo.id,
                pr_number=pr_data["number"],
                title=pr_data["title"],
                author="dev-contributor",
                created_at=datetime.utcnow() - timedelta(days=pr_data["days_ago"]),
                github_url=f"https://github.com/{r_data['full_name']}/pull/{pr_data['number']}",
                health_score=pr_data["health_score"],
                validation_status=pr_data["validation_status"],
                recommended_for_merge=pr_data["health_score"] > 80,
                test_results=[
                    TestResult(test_id="t1", name="test_db_connection", status="passed", duration_ms=120),
                    TestResult(test_id="t2", name="test_schema_migration", status="passed", duration_ms=450),
                ],
                code_health=[
                    CodeHealthIssue(severity="medium", message="Function too long", file_path="db/models.py", line_number=45),
                ] if pr_data["health_score"] < 90 else [],
                # V2: Control Plane sync fields
                github_state=pr_data["state"],
                merged=pr_data["merged"],
                merged_at=datetime.utcnow() - timedelta(days=2) if pr_data["merged"] else None,
                closed_at=datetime.utcnow() - timedelta(days=2) if pr_data["state"] == "closed" else None,
                last_synced_at=datetime.utcnow() - timedelta(seconds=45)
            )
            await pr.save()

    # Update user managed repos
    user.managed_repos = created_repo_names
    await user.save()
    
    # ========================================
    # CREATE AUDIT RUNS & FINDINGS (Issue-agnostic)
    # ========================================
    print("\nCreating audit runs and findings...")
    
    for repo_info in repos_data:
        repo = await Repo.find_one(Repo.repo_full_name == repo_info["full_name"])
        if not repo:
            continue
            
        # Delete existing audit runs for clean state
        await AuditRun.find(AuditRun.repo_id == repo.id).delete()
        
        # Create completed audit run
        print(f"  Creating audit for {repo_info['name']}...")
        audit_run = AuditRun(
            repo_id=repo.id,
            commit_sha=f"abc{repo_info['name'][:3]}123",  # Fake but unique SHA
            branch="main",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(minutes=30),
            metrics={
                "critical_count": 2 if repo_info["health_score"] < 60 else 0,
                "high_count": 4 if repo_info["health_score"] < 80 else 1,
                "medium_count": 8 if repo_info["health_score"] < 90 else 3,
                "low_count": 12
            }
        )
        await audit_run.insert()
        
        # Generate findings based on repo type
        findings_templates = []
        
        # Security findings (all repos)
        findings_templates.extend([
            {
                "severity": "critical",
                "category": "security",
                "rule": "hardcoded_secret",
                "file_path": "config.py" if repo_info["language"] == "Python" else "config.js",
                "line_number": 42,
                "description": "API key hardcoded in configuration file",
                "recommendation": "Move secrets to environment variables using .env file"
            },
            {
                "severity": "high",
                "category": "security",
                "rule": "sql_injection_risk",
                "file_path": "database/queries.py" if repo_info["language"] == "Python" else "db/queries.ts",
                "line_number": 156,
                "description": "Potential SQL injection vulnerability in user input handling",
                "recommendation": "Use parameterized queries or ORM to prevent SQL injection"
            }
        ])
        
        if repo_info["health_score"] < 80:
            # Low health repos get more critical issues
            findings_templates.append({
                "severity": "critical",
                "category": "security",
                "rule": "exposed_credentials",
                "file_path": ".env.example",
                "line_number": 5,
                "description": "Production credentials committed to version control",
                "recommendation": "Remove credentials immediately and rotate all exposed secrets"
            })
        
        # Code quality findings
        findings_templates.extend([
            {
                "severity": "medium",
                "category": "code_quality",
                "rule": "high_complexity",
                "file_path": "api/handlers.py" if repo_info["language"] == "Python" else "src/handlers.ts",
                "line_number": 234,
                "description": "Function has cyclomatic complexity of 15 (threshold: 10)",
                "recommendation": "Refactor into smaller functions with single responsibilities"
            },
            {
                "severity": "low",
                "category": "code_quality",
                "rule": "code_duplication",
                "file_path": "utils/helpers.py" if repo_info["language"] == "Python" else "utils/helpers.js",
                "line_number": 89,
                "description": "Duplicate code block found in validation logic (12 lines)",
                "recommendation": "Extract common logic into reusable helper function"
            },
            {
                "severity": "medium",
                "category": "code_quality",
                "rule": "long_function",
                "file_path": "services/processor.py" if repo_info["language"] == "Python" else "services/processor.ts",
                "line_number": 67,
                "description": "Function exceeds 200 lines, reducing maintainability",
                "recommendation": "Break down into smaller, focused functions"
            }
        ])
        
        # Dependency findings
        if repo_info["language"] == "Python":
            findings_templates.extend([
                {
                    "severity": "high",
                    "category": "dependencies",
                    "rule": "known_cve",
                    "file_path": "requirements.txt",
                    "line_number": 8,
                    "description": "requests==2.25.0 has known CVE-2023-32681",
                    "recommendation": "Upgrade to requests>=2.31.0 to patch vulnerability"
                },
                {
                    "severity": "medium",
                    "category": "dependencies",
                    "rule": "outdated_package",
                    "file_path": "requirements.txt",
                    "line_number": 15,
                    "description": "django==3.1.0 is 24 months old (latest: 4.2.0)",
                    "recommendation": "Upgrade to latest stable version for security patches"
                }
            ])
        else:  # TypeScript
            findings_templates.extend([
                {
                    "severity": "high",
                    "category": "dependencies",
                    "rule": "known_cve",
                    "file_path": "package.json",
                    "line_number": 12,
                    "description": "axios@0.21.1 has known CVE-2021-3749",
                    "recommendation": "Upgrade to axios>=0.21.2 to fix vulnerability"
                },
                {
                    "severity": "low",
                    "category": "dependencies",
                    "rule": "deprecated_package",
                    "file_path": "package.json",
                    "line_number": 18,
                    "description": "Package 'request' is deprecated and unmaintained",
                    "recommendation": "Migrate to 'axios' or 'node-fetch' for HTTP requests"
                }
            ])
        
        # Performance findings
        findings_templates.extend([
            {
                "severity": "medium",
                "category": "performance",
                "rule": "n_plus_one_query",
                "file_path": "api/views.py" if repo_info["language"] == "Python" else "api/routes.ts",
                "line_number": 45,
                "description": "N+1 query detected in list endpoint (100+ queries per request)",
                "recommendation": "Use eager loading or batch queries to reduce database calls"
            },
            {
                "severity": "low",
                "category": "performance",
                "rule": "inefficient_loop",
                "file_path": "utils/data_processor.py" if repo_info["language"] == "Python" else "utils/processor.ts",
                "line_number": 123,
                "description": "Nested loop with O(n²) complexity on large dataset",
                "recommendation": "Use hashmap/dictionary for O(n) lookup instead"
            }
        ])
        
        # Architecture findings
        if repo_info["health_score"] < 70:
            findings_templates.append({
                "severity": "high",
                "category": "architecture",
                "rule": "tight_coupling",
                "file_path": "core/service.py" if repo_info["language"] == "Python" else "core/service.ts",
                "line_number": 78,
                "description": "Business logic tightly coupled with database layer",
                "recommendation": "Introduce repository pattern to separate concerns"
            })
        
        # Test coverage findings
        findings_templates.extend([
            {
                "severity": "medium",
                "category": "tests",
                "rule": "low_coverage",
                "file_path": "api/auth.py" if repo_info["language"] == "Python" else "src/auth.ts",
                "line_number": 1,
                "description": "Authentication module has only 45% test coverage",
                "recommendation": "Add unit tests for all authentication flows"
            },
            {
                "severity": "low",
                "category": "tests",
                "rule": "missing_tests",
                "file_path": "services/payment.py" if repo_info["language"] == "Python" else "services/payment.ts",
                "line_number": 1,
                "description": "Critical payment logic has no test coverage",
                "recommendation": "Add comprehensive test suite for payment processing"
            }
        ])
        
        # Store findings
        for finding_data in findings_templates:
            finding = AuditFinding(
                audit_run_id=audit_run.id,
                **finding_data
            )
            await finding.insert()
    
    print("Done! Demo data populated with audit findings.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(populate_data())
