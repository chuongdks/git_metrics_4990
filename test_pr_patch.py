import requests
from typing import Optional
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

# ============================================================
# Helper: Get the code patch 
# ============================================================
def get_pr_patch(owner: str, repo: str, pr_number: int, github_token: Optional[str] = None) -> Optional[str]:
    """
    Fetches the final code patch (diff) for a Pull Request.
    """
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {
        # Request the patch media type instead of JSON
        "Accept": "application/vnd.github.v3.patch" 
    }
    
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(pr_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # The content is returned as a plain text string (the patch)
        return response.text 

    except requests.exceptions.RequestException as e:
        print(f"Error fetching patch for PR #{pr_number}: {e}")
        return None

# ============================================================
# MAIN PROGRAM
# ============================================================
PR_OWNER = "kubernetes-sigs"
PR_REPO = "cloud-provider-azure"
PR_NUMBERS = 9250 

patch_content = get_pr_patch(PR_OWNER, PR_REPO, PR_NUMBERS, GITHUB_TOKEN)

if patch_content:
    print(f"Successfully fetched patch for {PR_OWNER}/{PR_REPO} PR #{PR_NUMBERS}.")
    # Print the first 15 lines of the patch for brevity
    print("\n--- Start of Patch (First 15 Lines) ---")
    print('\n'.join(patch_content.splitlines()[:15]))
    print("--- End of Snippet ---")