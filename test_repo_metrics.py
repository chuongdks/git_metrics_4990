import requests
from datetime import datetime, timezone
from dateutil import parser # A helpful library for parsing date strings
import re
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")


# ============================================================
# Helper: Total Contributors
# ============================================================
def get_total_contributors(owner, repo, headers):
    """
    Retrieves the total number of contributors for a GitHub repository 
    using the Link header pagination trick.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    params = {"per_page": 1, "anon": "true"}  # include anonymous contributors

    try:
        response = requests.head(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        link_header = response.headers.get('Link')

        if link_header:
            match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if match:
                return int(match.group(1))
        # fallback for small repos
        return 1
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contributors for {owner}/{repo}: {e}")
        return 0

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
# Helper: Issues and Pull Requests
# ============================================================
def get_issue_and_pull_metrics(owner, repo, headers):
    base_search_url = "https://api.github.com/search/issues"

    queries = {
        'open_issues': f"repo:{owner}/{repo} is:issue is:open",
        'closed_issues': f"repo:{owner}/{repo} is:issue is:closed",
        'open_prs': f"repo:{owner}/{repo} is:pr is:open",
        'closed_prs': f"repo:{owner}/{repo} is:pr is:closed",
    }

    metrics = {'open_issues': 0, 'closed_issues': 0, 'total_pull_requests': 0}

    for key, query in queries.items():
        try:
            response = requests.get(base_search_url, headers=headers, params={'q': query, 'per_page': 1}, timeout=10)
            response.raise_for_status()
            total = response.json().get('total_count', 0)

            if key.startswith('open_issue'):
                metrics['open_issues'] = total
            elif key.startswith('closed_issue'):
                metrics['closed_issues'] = total
            else:
                metrics['total_pull_requests'] += total

        except requests.exceptions.RequestException:
            continue

    return metrics

# ============================================================
# Main Function: Repository Metrics
# ============================================================
def get_repo_metrics(owner, repo, github_token=None):
    """
    Retrieves metrics for a GitHub repository:
    Watchers, Duration, Commits, Issues, Pull Requests, Contributors
    """
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    try:
        response = requests.get(repo_url, headers=headers, timeout=10)
        response.raise_for_status()
        repo_data = response.json()

        # Basic metrics
        num_watchers = repo_data.get('stargazers_count', 0)
        num_commits = get_commit_count(owner, repo, headers)
        issue_pr_metrics = get_issue_and_pull_metrics(owner, repo, headers)
        num_closed_issues = issue_pr_metrics['closed_issues']
        num_open_issues = issue_pr_metrics['open_issues']
        num_pull_reqs = issue_pr_metrics['total_pull_requests']
        num_contributors = get_total_contributors(owner, repo, headers)

        # Duration (days since creation)
        created_at_str = repo_data.get('created_at')
        num_days = 0
        if created_at_str:
            created_at_aware = parser.parse(created_at_str)
            now_utc = datetime.now(timezone.utc)
            num_days = (now_utc - created_at_aware).days

        return {
            "Repo": f"{owner}/{repo}",
            "NumWatchers": num_watchers,
            "NumDays": num_days,
            "NumCommits": num_commits,
            "NumOpenIssues": num_open_issues,
            "NumClosedIssues": num_closed_issues,
            "NumPullReqs": num_pull_reqs,
            "NumContributors": num_contributors,
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {owner}/{repo}: {e}")
        return None

# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    REPOSITORIES = [
        ("milvus-io", "pymilvus"),
        ("badlogic", "lemmy"),
        ("firezone", "firezone"),
        # Add more repos here...
    ]

    results = []
    print("Starting data retrieval... (may take a moment due to multiple API calls)")

    for owner, repo in REPOSITORIES:
        metrics = get_repo_metrics(owner, repo, GITHUB_TOKEN)
        if metrics:
            results.append(metrics)

    # Display table
    print("\n Repository Metrics Summary:")
    print("-" * 160)
    header = (
        f"{'Repo':<25} | {'Watchers':>10} | {'Duration (Days)':>15} | {'Commits':>10} | "
        f"{'Open Issues':>12} | {'Closed Issues':>13} | {'Pull Requests':>14} | {'Contributors':>14}"
    )
    print(header)
    print("-" * 160)

    for r in results:
        print(
            f"{r['Repo']:<25} | "
            f"{r['NumWatchers']:>10,} | "
            f"{r['NumDays']:>15,} | "
            f"{r['NumCommits']:>10,} | "
            f"{r['NumOpenIssues']:>12,} | "
            f"{r['NumClosedIssues']:>13,} | "
            f"{r['NumPullReqs']:>14,} | "
            f"{r['NumContributors']:>14,}"
        )
