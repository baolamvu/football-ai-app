import requests

url = "https://api.football-data.org/v4/matches"

headers = {
    "X-Auth-Token": "14ecba9640e845229a9eece33202f795"
}

response = requests.get(url, headers=headers)

print(response.json())