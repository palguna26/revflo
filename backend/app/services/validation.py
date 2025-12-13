from typing import List
from app.models.pr import PullRequest
from app.models.issue import Issue
from app.services.ai_review import ai_service
import asyncio

class ValidationService:
    async def validate_pr_integration(self, pr: PullRequest, issues: List[Issue], diff: str = "") -> tuple[str, List[dict]]:
        """
        Validate if the PR satisfies the checklists of linked issues.
        Returns a tuple of (status string, list of checklist items with updated status).
        """
        if not issues:
            return "validated", [] 
            
        # Collect all pending checklist items
        # We need to map them back to the original items
        checklist_map = {}
        input_items = []
        
        for issue in issues:
            for item in issue.checklist:
                 # Check if we should validate this item
                 # If it's already passed, we might skip, but for "revalidate" we usually check again 
                 # or at least include it in the manifest as "passed".
                 # For now, let's re-validate everything to be safe or only pending ones.
                 # Let's re-validate pending/failed ones.
                 checklist_map[item.id] = item
                 input_items.append({
                     "id": item.id,
                     "text": item.text,
                     "issue_id": str(issue.id)
                 })

        if not input_items:
            return "validated", []

        if not diff:
            return "needs_work", []

        # Call AI specific validation with the PR diff
        results = await ai_service.validate_checklist(diff, input_items)
        
        # Construct updated checklist items for the PR Manifest
        # The schema uses app.models.pr.ChecklistItem
        manifest_items = []
        
        all_passed = True
        
        # Create a map of results for easy lookup
        result_map = {r["id"]: r for r in results}
        
        for item_data in input_items:
            original_item = checklist_map[item_data["id"]]
            result = result_map.get(item_data["id"])
            
            status = "pending"
            if result:
                status = result.get("status", "pending")
            
            # If AI says failed, mark failed
            if status == "failed":
                all_passed = False
            
            # Creating a dict that matches ChecklistItem model roughly
            # We don't have linked tests yet, so empty list
            manifest_items.append({
                "id": original_item.id,
                "text": original_item.text,
                "required": original_item.required,
                "status": status,
                "linked_tests": []
            })
        
        final_status = "validated" if all_passed else "needs_work"
        return final_status, manifest_items

validation_service = ValidationService()
