"""Quick test call to football-data.org (reads token from .env)."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

token = os.getenv("FOOTBALL_DATA_TOKEN", "").strip()
if not token:
    raise SystemExit("Set FOOTBALL_DATA_TOKEN in .env")

url = "https://api.football-data.org/v4/matches"
headers = {"X-Auth-Token": token}

response = requests.get(url, headers=headers, timeout=30)
print(response.status_code)
print(response.json())
