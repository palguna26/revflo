from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.models.pr import PullRequest
from app.models.repo import Repo
from app.models.user import User
from app.models.issue import Issue
from app.services.assistant_service import assistant
from app.services.github import github_service
from app.services.pr_service import pr_service
from app.services.issue_service import issue_service
from fastapi import BackgroundTasks

scheduler = AsyncIOScheduler()

async def job_sync_github_data():
    """
    Periodically syncs all installed repos.
    """
    print("Syncing GitHub data...")
    repos = await Repo.find(Repo.is_installed == True).to_list()
    for repo in repos:
        try:
            # Find a user with token to perform sync
            user = await User.find_one(User.login == repo.owner)
            if not user or not user.access_token:
                user = await User.find_one(User.access_token != None)
            
            if not user:
                print(f"Skipping sync for {repo.name}: No valid user token found.")
                continue

            # Sync Issues
            # Note: issue_service.list_issues fetches and converts, but doesn't bulk save.
            # We strictly want to 'upsert' recent items.
            gh_issues = await github_service.fetch_issues(repo.owner, repo.name, user)
            for item in gh_issues:
                if "pull_request" in item: continue
                # Trigger get_or_sync logic which saves to DB
                await issue_service.get_or_sync_issue(repo.owner, repo.name, item["number"], user, BackgroundTasks())
            
            # Sync PRs
            gh_prs = await github_service.fetch_prs(repo.owner, repo.name, user)
            for item in gh_prs:
                await pr_service.get_or_sync_pr(repo.owner, repo.name, item["number"], user)
                
            print(f"Synced {repo.name} success.")
            
        except Exception as e:
            print(f"Failed to sync {repo.name}: {e}")

async def job_validate_pending_prs():
    print("Checking for pending PR validations...")
    pending_prs = await PullRequest.find(PullRequest.validation_status == "pending").to_list()
    
    for pr in pending_prs:
        try:
            repo = await Repo.get(pr.repo_id)
            if not repo: 
                print(f"PR #{pr.pr_number}: Repo not found, skipping")
                continue
            
            # 1. User Resolution - Find user with valid token
            user = await User.find_one(User.login == repo.owner)
            if not user or not user.access_token:
                 user = await User.find_one(User.access_token != None)
            
            # If still no valid user/token, skip this PR and mark for manual review
            if not user or not user.access_token:
                print(f"PR #{pr.pr_number} ({repo.owner}/{repo.name}): No valid GitHub token found, marking as needs_manual_review")
                pr.validation_status = "needs_manual_review"
                pr.summary = "Validation could not be performed due to missing GitHub access token. Please review manually."
                await pr.save()
                continue
            
            # 2. Fetch Data via Service (handling decryption)
            try:
                diff_text = await github_service.fetch_pr_diff(repo.owner, repo.name, pr.pr_number, user)
                pr_data = await github_service.fetch_pr(repo.owner, repo.name, pr.pr_number, user)
            except Exception as e:
                # If GitHub API call fails (401, 403, etc.), mark for manual review
                if "401" in str(e) or "Unauthorized" in str(e):
                    print(f"PR #{pr.pr_number}: GitHub authentication failed, marking as needs_manual_review")
                    pr.validation_status = "needs_manual_review"
                    pr.summary = "GitHub API authentication failed. Token may be expired or invalid."
                    await pr.save()
                    continue
                else:
                    # Other errors, re-raise to be caught by outer try/except
                    raise
            
            body = pr_data.get("body", "")
            
            # 3. Find Linked Issues
            # (Logic remains same, can be moved to service but fine here for now)
            import re
            linked_issues = []
            if body:
                issue_numbers = re.findall(r"(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)", body, re.IGNORECASE)
                for num in issue_numbers:
                    issue = await Issue.find_one(Issue.repo_id == repo.id, Issue.issue_number == int(num))
                    if issue: linked_issues.append(issue)

            checklist_definitions = []
            for issue in linked_issues:
                if issue.checklist:
                    for item in issue.checklist:
                        checklist_definitions.append({"id": item.id, "text": item.text})
            
            # 4. Agentic Review
            if not checklist_definitions:
                print(f"PR #{pr.pr_number} has no linked checklist. Skipping review.")
                # Mark as 'skipped' or 'needs_manual_review'? 
                # For now leave pending or set to 'no_checklist'
                continue

            review_result = await assistant.verify_change(pr.title, body, diff_text, checklist_definitions)
            
            # 5. Persist (Code Logic Duplicated from pr_service.run_review - should ideally reuse)
            # For simplicity, we manually update here or call `pr_service` methods if we refactor `run_review` to take data.
            # Let's manually update to match older logic but clean.
            
            pr.summary = review_result.get("summary")
            pr.health_score = review_result.get("health_score")
            pr.code_health = review_result.get("code_health", [])
            pr.suggested_tests = review_result.get("suggested_tests", [])
            
            manifest_items = []
            validated_lookup = {item["id"]: item for item in review_result.get("checklist_items", [])}
            
            for item in checklist_definitions:
                res = validated_lookup.get(item["id"])
                manifest_items.append({
                    "id": item["id"],
                    "text": item["text"],
                    "required": True,
                    "status": res["status"] if res else "pending",
                    "evidence": res.get("evidence"),
                    "reasoning": res.get("reasoning"),
                    "linked_tests": []
                })
            
            pr.manifest = {"checklist_items": manifest_items}
            all_passed = all(i["status"] == "passed" for i in manifest_items)
            pr.validation_status = "validated" if all_passed and manifest_items else "needs_work"
            
            await pr.save()
            
            # Update Issues
            if linked_issues:
                # Reuse the logic from pr_service if possible, but it's private `_update_issue_history`
                # We'll just duplicate the simple loop for now
                for issue in linked_issues:
                    updated = False
                    for item in issue.checklist:
                        res = validated_lookup.get(item.id)
                        if res:
                            item.status = res["status"]
                            updated = True
                    if updated: await issue.save()

            print(f"Validated PR #{pr.pr_number}")
            
        except Exception as e:
            print(f"Validation failed for PR #{pr.pr_number}: {e}")

def start_scheduler():
    scheduler.add_job(job_sync_github_data, 'interval', minutes=60)
    # Run PR validations every 5 minutes instead of every 30 seconds
    scheduler.add_job(job_validate_pending_prs, 'interval', minutes=5)
    scheduler.start()

async def stop_scheduler():
    scheduler.shutdown()
