import requests
import re
from typing import Optional, Dict
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

# ============================================================
# Helper: Total Commit Counts
# ============================================================
def get_commit_count(owner, repo, headers):
    """Retrieves the total number of commits for the entire repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": 1}
    
    try:
        # Use HEAD request and pagination trick for total count
        response = requests.head(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        link_header = response.headers.get('Link')

        if link_header:
            last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if last_page_match:
                return int(last_page_match.group(1))
        
        # Fallback for very small repos
        return 0 
        
    except requests.exceptions.RequestException:
        return 0


def get_developer_commit_metrics(owner: str, repo: str, developer_login: str, github_token: Optional[str] = None) -> Optional[Dict]:
    """
    Retrieves a developer's total commits and their percentage contribution to the repo.
    """
    
    # Setup headers with token
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        # 1. Get the total commits for the developer (filtered by author)
        # We use the pagination trick again, but this time with the 'author' parameter
        
        developer_commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {"per_page": 1, "author": developer_login}
        
        dev_response = requests.head(developer_commit_url, headers=headers, params=params, timeout=10)
        dev_response.raise_for_status()
        
        developer_commits = 0
        dev_link_header = dev_response.headers.get('Link')
        
        if dev_link_header:
            dev_last_page_match = re.search(r'page=(\d+)>; rel="last"', dev_link_header)
            if dev_last_page_match:
                developer_commits = int(dev_last_page_match.group(1))
        
        # 2. Get the total commits for the entire repository
        total_commits = get_commit_count(owner, repo, headers)
        
        # 3. Calculate the percentage contribution
        commit_percentage = 0.0
        if total_commits > 0:
            commit_percentage = (developer_commits / total_commits) * 100
        
        return {
            "Developer_Login": developer_login,
            "Total_Repo_Commits": total_commits,
            "Developer_Commits": developer_commits,
            "Developer_Commit_Percentage": commit_percentage,
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {developer_login} in {owner}/{repo}: {e}")
        return None
    
    # --- (The get_total_commit_count function goes here) ---
# --- (The get_developer_commit_metrics function goes here) ---

REPO_OWNER = "kubernetes-sigs"
REPO_NAME = "cloud-provider-azure"

# Example Developer (Replace with the developer you are interested in)
DEVELOPER_LOGIN = "nilo19" 

print(f"Starting commit metric retrieval for {DEVELOPER_LOGIN} in {REPO_OWNER}/{REPO_NAME}...")

metrics = get_developer_commit_metrics(REPO_OWNER, REPO_NAME, DEVELOPER_LOGIN, GITHUB_TOKEN)

print("\n📊 Developer Commit Metrics Summary:")
print("-" * 70)

if metrics:
    # Print Header
    header = f"{'Developer':<20} | {'Repo Commits':>15} | {'Dev Commits':>15} | {'Contribution %':>15}"
    print(header)
    print("-" * 70)

    # Print Data
    print(
        f"{metrics['Developer_Login']:<20} | "
        f"{metrics['Total_Repo_Commits']:>15,} | "
        f"{metrics['Developer_Commits']:>15,} | "
        f"{metrics['Developer_Commit_Percentage']:>15.2f}%"
    )