import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

# ============================================================
# Helper: Get the files name, patch code, addition, deletion, status,...
# ============================================================
def get_pr_files_and_patches(owner: str, repo: str, pr_number: int, github_token: Optional[str] = None) -> List[Dict]:
    """
    Fetches the filename and individual patch content for all files changed 
    in a Pull Request, handling pagination.

    Args:
        owner: The repository owner.
        repo: The repository name.
        pr_number: The Pull Request number.
        github_token: Optional GitHub Personal Access Token for authentication/rate limits.

    Returns:
        A list of dictionaries, each containing the filename and patch string.
    """
    
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    all_file_details = []
    page = 1
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    print(f"Fetching file details for PR #{pr_number} (Paginating 100 files/page)...")

    while True:
        params = {"per_page": 100, "page": page}
        
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            files_data = response.json()

            if not files_data:
                # No more files or end of data
                break

            for file in files_data:
                # Extract filename
                filename = file.get('filename')
                
                # Extract patch, and handle the "patch too long/missing" scenario
                # The 'patch' field is sometimes missing or null if the diff is massive.
                patch_content = file.get('patch')
                
                final_patch = patch_content if patch_content else "NULL"
                
                all_file_details.append({
                    "filename": filename,
                    "patch": final_patch,
                    "status": file.get('status'), # Status (added, modified, deleted)
                    "additions": file.get('additions', 0),
                    "deletions": file.get('deletions', 0),
                })
            
            # Check for the next page header
            if 'link' not in response.headers or 'rel="next"' not in response.headers['link']:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error during API call on page {page}: {e}")
            break
            
    print(f"✅ Finished fetching. Total files processed: {len(all_file_details)}")
    return all_file_details

# ============================================================
# Helper: save patch code to a patch file
# ============================================================
def save_patches_to_files(file_patches: List[Dict], pr_number: int):
    """
    Saves the individual patch content into separate .patch files 
    inside a new directory.
    """
    if not file_patches:
        print("No patches to save.")
        return
        
    # Create a safe directory for the patches
    output_dir = f"PR_{pr_number}_Patches"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nPatches will be saved in the directory: {output_dir}")

    saved_count = 0
    null_count = 0

    for item in file_patches:
        filename = item['filename']
        patch = item['patch']

        if patch == "NULL":
            print(f"   [Skipped] {filename}: Patch content was too large or missing.")
            null_count += 1
            continue

        # Sanitize the filename to make it safe for a file path (replace slashes with underscores)
        safe_filename = filename.replace(os.path.sep, '_').replace('/', '_')
        output_filepath = os.path.join(output_dir, f"{safe_filename}.patch")

        try:
            # The patch content already contains the filename in its headers (--- / +++ lines)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(patch)
            saved_count += 1
        except Exception as e:
            print(f"Error writing file {output_filepath}: {e}")
    
    print(f"\nSummary: {saved_count} patches saved successfully. ({null_count} patches marked NULL and skipped.)")

# ============================================================
# MAIN PROGRAM
# ============================================================
# Using the URL you provided: 
OWNER = "AgentOps-AI"
REPO = "agentops"
PR_NUMBER = 1179

# 1. Fetch the data from the GitHub API
file_patches = get_pr_files_and_patches(OWNER, REPO, PR_NUMBER, GITHUB_TOKEN)

# Display Results
if file_patches:
    print("\n--- Final File Patch Summary ---")
    for item in file_patches:
        patch_snippet = item['patch']
        if patch_snippet != "NULL":
            # snippet of the patch content
            patch_snippet = patch_snippet.splitlines()[0] + "..."
        
        print(f"\n[File: {item['filename']}]")
        print(f"  Status: {item['status'].upper()}")
        print(f"  Changes: +{item['additions']}, -{item['deletions']}")
        print(f"  Patch Snippet: {patch_snippet}")
else:
    print("No file patches were retrieved.")
    
# 2. Save the data to individual .patch files
save_patches_to_files(file_patches, PR_NUMBER)