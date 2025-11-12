import requests
import json
import os
from typing import List, Dict, Optional
import readability
import syntok.segmenter as segmenter
from dotenv import load_dotenv
import os

# ============================================================
# Initializing
# ============================================================
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

# ============================================================
# 1. Core Fetch Function for a Single Issue
# ============================================================
def fetch_single_issue(owner: str, repo: str, issue_number: int, github_token: Optional[str]) -> Optional[Dict]:
    """
    Fetches the title, body, and labels for a single issue number.
    Returns None if the issue is a PR, deleted, or if an error occurs.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        issue_data = response.json()

        # Check if the object is actually a Pull Request (PR)
        if 'pull_request' in issue_data:
            print(f"   [SKIP] #{issue_number} is a Pull Request, skipping.")
            return None
        
        # Extract the body fields for readability
        issue_body = issue_data.get('body') or "No body content provided."

        # Calculate Readability Score
        flesch_score = get_readability_score(issue_body)
        
        # Extract the required fields
        return {
            "issue_number": issue_number,
            "title": issue_data.get('title'),
            "body": issue_body,
            "labels": [label['name'] for label in issue_data.get('labels', [])],
            "url": issue_data.get('html_url'),
            "flesch_reading_ease": flesch_score
        }

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"   [FAIL] #{issue_number} not found (Error 404).")
        else:
            print(f"   [FAIL] HTTP Error for #{issue_number}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"   [FAIL] Connection Error for #{issue_number}: {e}")
        return None

# ----------------------------------------------------
# 2. Main Batch Processing Function
# ----------------------------------------------------
def batch_fetch_issue_details(issue_numbers: List[int], owner: str, repo: str, github_token: Optional[str]) -> List[Dict]:
    """
    Iterates over a list of issue numbers and fetches details for each.
    """
    all_issue_details = []
    total_issues = len(issue_numbers)
    
    print(f"Starting batch fetch for {total_issues} items in {owner}/{repo}...")

    for i, number in enumerate(issue_numbers):
        print(f"Processing {i+1}/{total_issues}: Issue #{number}...")
        
        detail = fetch_single_issue(owner, repo, number, github_token)
        
        if detail:
            all_issue_details.append(detail)
            
    print("\nBatch fetch complete.")
    return all_issue_details

# ----------------------------------------------------
# 3. Save to Markdown Function (Integrated)
# ----------------------------------------------------
def save_issues_to_markdown(issues: List[Dict], output_filename: str):
    """
    Formats the issue data into a structured Markdown file.
    """
    if not issues:
        print("No issues to save to Markdown.")
        return
    
    # Using 'issue_number' for the key consistency across files
    markdown_content = f"# Issue Report\n\n"
    markdown_content += f"Total Issues Found: {len(issues)}\n\n"
    markdown_content += "---\n"
    
    for issue in issues:
        markdown_content += f"## Issue #{issue['issue_number']}: {issue['title']}\n"
        markdown_content += f"* **URL:** {issue['url']}\n"
        markdown_content += f"* **Labels:** {', '.join(issue['labels'])}\n"
        
        # Display the new score
        score = issue.get('flesch_reading_ease')
        if score is not None:
            # Score is usually between 0 (hard) and 100 (easy)
            markdown_content += f"* **Flesch Reading Ease Score:** {score:.2f}\n" 
        else:
             markdown_content += f"* **Flesch Reading Ease Score:** N/A (Empty body or error)\n"
             
        markdown_content += "\n### Description\n"
        markdown_content += f"{issue['body']}\n" 
        markdown_content += "---\n"
        
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"\nSuccessfully saved issue details to: **{os.path.abspath(output_filename)}**")
    except Exception as e:
        print(f"Error writing Markdown file: {e}")

# ----------------------------------------------------
# Helper: Function for Preprocessing and Scoring
# ----------------------------------------------------
def get_readability_score(text: str) -> Optional[float]:
    """
    Tokenizes text using syntok and returns the Flesch Reading Ease score.
    Returns None if the text is empty or analysis fails.
    Based on: https://pypi.org/project/readability/
    """
    if not text or text == "No body content provided.":
        return None
    
    # 1. Use syntok to tokenize and segment the text
    # This complex join statement transforms the raw string into the required format:
    # 'word1 word2 .\nword3 word4 .\n\nnew_paragraph_word1 .'
    try:
        tokenized = '\n\n'.join(
            '\n'.join(' '.join(token.value for token in sentence) 
                      for sentence in paragraph)
            for paragraph in segmenter.analyze(text)
        )
    except Exception as e:
        print(f"Error during syntok analysis: {e}")
        return None

    # 2. Calculate the readability scores
    try:
        # Check if the tokenized text is not empty before scoring
        if not tokenized.strip():
            return None
            
        results = readability.getmeasures(tokenized, lang='en')
        
        # We will return the Flesch Reading Ease score as an example
        return results['readability grades']['FleschReadingEase']
        
    except Exception as e:
        print(f"Error calculating readability score: {e}")
        return None

# ============================================================
# MAIN PROGRAM
# ============================================================
TARGET_ISSUE_NUMBERS = [
    27,  
]

# --- REPOSITORY CONTEXT ---
OWNER = "fireship-io"
REPO = "flamethrower"

if __name__ == "__main__":
    
    # Run the batch process
    final_data = batch_fetch_issue_details(
        TARGET_ISSUE_NUMBERS, 
        OWNER, 
        REPO, 
        GITHUB_TOKEN
    )
    
    # Save the aggregated results to a JSON file
    output_filename = f"{REPO}_batch_issue_details.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4)
        print(f"\nSuccessfully saved detailed issue data to: **{os.path.abspath(output_filename)}**")
        print(f"Total Issues successfully collected: {len(final_data)}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        
    # 3. Save the aggregated results to a Markdown file
    markdown_output_filename = f"{REPO}_issue_report.md"
    save_issues_to_markdown(final_data, markdown_output_filename)        