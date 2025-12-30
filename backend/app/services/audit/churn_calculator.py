"""
Churn Calculator
Calculates file change frequency from GitHub API
"""
import logging
from typing import Dict
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class ChurnCalculator:
    """Calculates file-level churn from GitHub commit history"""
    
    async def calculate_churn(
        self,
        repo_url: str,
        github_token: str,
        file_paths: list,
        days: int = 90
    ) -> Dict[str, int]:
        """
        Calculate churn for files using GitHub API.
        
        Args:
            repo_url: GitHub repo URL (https://github.com/owner/repo)
            github_token: GitHub access token
            file_paths: List of file paths to check
            days: Look back period (default 90 days)
            
        Returns:
            Dict mapping file_path -> commit_count
        """
        churn_map = {}
        
        # Extract owner/repo from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            logger.error(f"Invalid repo URL: {repo_url}")
            return churn_map
        
        owner, repo = parts[-2], parts[-1]
        
        # Calculate since timestamp
        since = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            # Limit to top 20 files to avoid rate limits
            files_to_check = file_paths[:20] if len(file_paths) > 20 else file_paths
            
            async with aiohttp.ClientSession() as session:
                # Get commits since date
                params = {
                    'since': since,
                    'per_page': 100
                }
                
                async with session.get(api_url, headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"GitHub API error: {response.status}")
                        return churn_map
                    
                    commits = await response.json()
                    logger.info(f"Found {len(commits)} commits in last {days} days")
                    
                    # For each file, count how many commits touched it
                    for file_path in files_to_check:
                        count = 0
                        
                        for commit in commits:
                            commit_sha = commit['sha']
                            
                            # Get commit details to see which files changed
                            commit_url = f"{api_url}/{commit_sha}"
                            async with session.get(commit_url, headers=headers) as commit_response:
                                if commit_response.status == 200:
                                    commit_data = await commit_response.json()
                                    
                                    # Check if this file was modified
                                    if 'files' in commit_data:
                                        for file in commit_data['files']:
                                            if file['filename'] == file_path:
                                                count += 1
                                                break
                        
                        churn_map[file_path] = count
                    
                    logger.info(f"Calculated churn for {len(churn_map)} files")
                    
        except Exception as e:
            logger.error(f"Failed to calculate churn: {e}")
        
        return churn_map
