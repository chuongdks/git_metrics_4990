from github import Github
from github import Auth
from dotenv import load_dotenv
import os

# Load the API key from config file
load_dotenv("./api_key.env")
# Fetch the API key from the environment
TOKEN = os.getenv("OPENAI_API_KEY")

# using an access token
auth = Auth.Token(TOKEN)

# github instance
g = Github(auth=auth)

# The query (https://api.github.com/repos/jellydn/vscode-hurl-runner 
# query = 'is:pr repo:jellydn/vscode-hurl-runner ' \
#         'in:body:"Co-Authored-By: Claude"' 

# The string concatenation might introduce issues, or the underlying library/tool is mis-encoding it.
query = 'is:pr head:codex
                    
print(f"Executing search query: {query}")
print("-" * 50)

# Execute the search
try:
    results = g.search_issues(query=query)
except Exception as e:
    print(f"An error occurred during search: {e}")

# Process the results
print(f"\nFound {results.totalCount} matching Pull Requests.")

for pr_issue in results:
    # PyGithub returns an Issue object (search_issue duh), but if 'is:pr' was in the query, treat it as a PR url
    # get meta data based on REST API Response schema (https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28)
    print("---")
    print(f"PR #:   {pr_issue.number}")
    print(f"Title:  {pr_issue.title}")
    print(f"Author: {pr_issue.user.login}")
    
    # Get the PR object to inspect head branch. TRIGGER ADDITIONAL API CALL
    pr = pr_issue.as_pull_request()
    print(f"Head Branch: {pr.head.ref}")
    
    # Message in Body
    if pr_issue.body:
        print(f"Body snippet (first 100 chars): {pr_issue.body[:100].replace('\n', ' ')}...")