import requests
from typing import Dict, Optional
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
def get_primary_language(owner: str, repo: str, github_token: Optional[str] = None) -> Optional[str]:
    """
    Fetches language statistics from GitHub and determines the primary language 
    based on the largest byte count.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        language_data: Dict[str, int] = response.json()
        
        if not language_data:
            print(f"No language data found for {owner}/{repo}.")
            return None
        
        # find the max key (language name) 
        primary_language = max(language_data, key=language_data.get)
        
        print(f"Success. Primary Language: {primary_language}")
        print(f"All Languages (bytes): {language_data}")
        
        return primary_language
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching language data: {e}")
        return None

# ============================================================
# MAIN PROGRAM
# ============================================================
REPO_OWNER = "kubernetes-sigs"
REPO_NAME = "cloud-provider-azure"

# Run the function
primary_lang = get_primary_language(REPO_OWNER, REPO_NAME, GITHUB_TOKEN)