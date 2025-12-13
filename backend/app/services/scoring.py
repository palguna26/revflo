from app.models.repo import Repo
from app.models.pr import PullRequest

class ScoringService:
    @staticmethod
    def calculate_repo_health(repo: Repo) -> int:
        score = 100
        # Penalize for open issues (rough heuristic)
        score -= min(repo.issue_count * 2, 20)
        
        # Penalize for inaction
        # TODO: Check last_activity
        
        return max(0, score)

    @staticmethod
    def calculate_pr_health(pr: PullRequest) -> int:
        score = 100
        if pr.validation_status == "needs_work":
            score -= 20
        
        # Penalize for code health issues
        criticals = sum(1 for i in pr.code_health if i.severity == "critical")
        highs = sum(1 for i in pr.code_health if i.severity == "high")
        
        score -= (criticals * 15)
        score -= (highs * 5)
        
        return max(0, score)

scoring_service = ScoringService()
