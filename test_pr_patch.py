import requests
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

# --- 1. SET YOUR VARIABLES ---
PR_OWNER = "AgentOps-AI"
PR_REPO = "agentops"
PR_NUMBERS = 1179 

# --- 2. CONSTRUCT THE URL AND HEADERS ---
API_URL = f"https://api.github.com/repos/{PR_OWNER}/{PR_REPO}/pulls/{PR_NUMBERS}"

HEADERS = {
    # *** KEY CHANGE: Requesting the output in unified patch format ***
    "Accept": "application/vnd.github.v3.patch", 
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

# --- 3. MAKE THE REQUEST ---
response = requests.get(API_URL, headers=HEADERS)

# --- 4. CHECK THE RESPONSE ---
if response.status_code == 200:
    # The response content is the single text string containing all patches
    full_patch_text = response.text
    
    print("Successfully retrieved the full unified patch.")
    
    # You can now save this text to a file or process it:
    with open('./pr_final_patch.patch', 'w', encoding='utf-8') as f:
        f.write(full_patch_text)
    
    # Display the first 20 lines of the patch
    print("\n--- Start of Unified Patch (First 20 Lines) ---")
    print('\n'.join(full_patch_text.splitlines()[:20])) # 
    print("---------------------------------------------")

else:
    print(f"Error. Status Code: {response.status_code}")
    # Print the error message if it's JSON
    try:
        print(response.json()) 
    except requests.exceptions.JSONDecodeError:
        print(response.text)