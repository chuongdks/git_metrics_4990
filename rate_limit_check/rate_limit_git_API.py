import requests
from dotenv import load_dotenv
import os
import json
load_dotenv("./api_key.env")
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")

headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
}

response = requests.get('https://api.github.com/rate_limit', headers=headers)

data = response.json()

# Pretty-print and save to file
with open("./rate_limit_check/rate_limit.json", "w") as f:
    json.dump(data, f, indent=4)

print("Saved to rate_limit.json")
