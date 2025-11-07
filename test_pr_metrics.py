import requests
import re
from typing import Optional, Dict, List, Tuple
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

# ============================================================
# Helper: Total reviews (not inline) for a PR
# ============================================================
def get_review_count(owner: str, repo: str, pr_number: int, headers: Dict) -> int:
    """Retrieves the total count of formal reviews submitted for a Pull Request using the dedicated /reviews endpoint."""
    reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    
    try:
        # We use a HEAD request with per_page=1 and pagination trick to get the total count
        response = requests.head(reviews_url, headers=headers, params={"per_page": 1}, timeout=10)
        response.raise_for_status()
        
        # Check the 'Link' header for the last page
        link_header = response.headers.get('Link')
        if link_header:
            last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if last_page_match:
                return int(last_page_match.group(1))
        
    except requests.exceptions.RequestException:
        return 0

# ============================================================
# Helper: Path files of a repo
# ============================================================
def get_file_path_metrics(owner: str, repo: str, pr_number: int, headers: Dict) -> Tuple[int, float, int]:
    """
    Retrieves the count of changed files and calculates file path length statistics.
    Returns: (total_files, avg_path_length, max_path_length)
    """
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    all_file_paths = []
    page = 1
    
    # 
    while True:
        try:
            response = requests.get(
                files_url, 
                headers=headers, 
                params={"per_page": 100, "page": page}, 
                timeout=10
            )
            response.raise_for_status()
            files_data = response.json()
            
            if not files_data:
                break
                
            # Extract the 'filename' (which includes the full path)
            for file in files_data:
                # Store the length of the full file path string
                all_file_paths.append(len(file.get('filename', ''))) 
            
            # Check for the next page
            if 'link' not in response.headers or 'rel="next"' not in response.headers['link']:
                break
            page += 1
            
        except requests.exceptions.RequestException:
            break
            
    num_paths = len(all_file_paths)
    
    if num_paths == 0:
        return 0, 0.0, 0
    
    # Calculate average and max path length
    avg_path_length = sum(all_file_paths) / num_paths
    max_path_length = max(all_file_paths)
    
    return num_paths, avg_path_length, max_path_length

# ============================================================
# Helper: Commit Count
# ============================================================
def get_commit_count(owner, repo, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": 1}

    try:
        response = requests.head(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        link_header = response.headers.get('Link')

        if link_header:
            match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if match:
                return int(match.group(1))

        # fallback for repos with few commits
        response = requests.get(url, headers=headers, params={"per_page": 100}, timeout=10)
        return len(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching commits for {owner}/{repo}: {e}")
        return 0


# ============================================================
# Helper: Developer commits metrics
# ============================================================
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
    
    
# ============================================================
# Main Function: Pull Request Metrics
# ============================================================
def get_pull_request_metrics(owner: str, repo: str, pr_number: int, github_token: Optional[str] = None) -> Optional[Dict]:
    """
    Retrieves the lines added, lines deleted, and the number of files changed
    for a specific GitHub Pull Request.
    """
    
    # 1. API URL for a specific Pull Request
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {
        # Standard Accept header for the V3 API
        "Accept": "application/vnd.github.v3+json"
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        # Fetch the Pull Request object
        response = requests.get(pr_url, headers=headers, timeout=10)
        response.raise_for_status()
        pr_data = response.json()

        # 1. Line/File Change Metrics (from previous step)
        num_additions = pr_data.get('additions', 0)
        num_deletions = pr_data.get('deletions', 0)
        num_files_changed = pr_data.get('changed_files', 0)
        
        # 2. NumCommits, NumComments (exclude review) 
        num_commits = pr_data.get('commits', 0)
        num_comments = pr_data.get('comments', 0)
        num_formal_reviews = get_review_count(owner, repo, pr_number, headers)
        num_inline_comments = pr_data.get('review_comments', 0)
        
        #3
        num_paths, avg_path_len, max_path_len = get_file_path_metrics(
            owner, repo, pr_number, headers
        )
        
        return {
            "PR_ID": pr_number,
            "Additions": num_additions,
            "Deletions": num_deletions,
            "Files_Changed": num_files_changed,
            "NumCommits": num_commits,
            "NumComments": num_comments,
            "NumFormalReviews": num_formal_reviews, 
            "NumInlineComments": num_inline_comments, 
            "NumPathsInFile": num_paths,          # The number of paths (or files changed)
            "AvgPathCharLength": avg_path_len,    # Average characters in file paths
            "MaxPathCharLength": max_path_len,    # Max characters in file paths
        }
        
    except requests.exceptions.RequestException as e:
            print(f"Error fetching data for PR #{pr_number} in {owner}/{repo}: {e}")
            return None
    

# ============================================================
# MAIN PROGRAM
# ============================================================
PR_OWNER = "kubernetes-sigs"
PR_REPO = "cloud-provider-azure"
PR_NUMBERS = [
    9250 # A relatively recent feature PR
]

pr_results = []
print(f"Starting data retrieval for {PR_OWNER}/{PR_REPO} Pull Requests...")

for pr_num in PR_NUMBERS:
    metrics = get_pull_request_metrics(PR_OWNER, PR_REPO, pr_num, GITHUB_TOKEN)
    if metrics:
        pr_results.append(metrics)

print("\n Pull Request Metrics Summary:")
print("-" * 180) 

# Header
header = (
    f"{'PR ID':<8} | {'Adds':>6} | {'Dels':>6} | {'Files':>6} | "
    f"{'Commits':>8} | {'PR Comments':>12} | {'Formal Reviews':>15} | {'Code Comments':>13} | "
    f"{'Paths Changed':>13} | {'Avg Path Chars':>14} | {'Max Path Chars':>14}"
)
print(header)
print("-" * 180) 

# Printing out
for r in pr_results:
    # Note: AvgPathCharLength is a float, so we use .1f for one decimal place
    print(
        f"#{r['PR_ID']:<7} | "
        f"{r['Additions']:>6,} | "
        f"{r['Deletions']:>6,} | "
        f"{r['Files_Changed']:>6,} | "
        f"{r['NumCommits']:>8,} | "
        f"{r['NumComments']:>12,} | "
        f"{r['NumFormalReviews']:>15,} | "
        f"{r['NumInlineComments']:>13,} | "
        f"{r['NumPathsInFile']:>13,} | "
        f"{r['AvgPathCharLength']:>14.1f} | " 
        f"{r['MaxPathCharLength']:>14,}"
    )