"""
github_contributions.py
Fetches GitHub contribution data for a given user and year
using the GitHub GraphQL API (requires a personal access token).
"""

import requests
from datetime import datetime, timezone

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

CONTRIBUTIONS_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    name
    login
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""


def fetch_github_contributions(username: str, year: int, token: str) -> dict:
    """
    Fetch GitHub contributions for a user in a given year.

    Args:
        username: GitHub username (e.g. 'nyandajr')
        year:     Year to fetch contributions for (e.g. 2026)
        token:    GitHub personal access token (needs read:user scope)

    Returns:
        dict with user contribution data on success,
        or dict with an 'error' key on failure.
    """
    from_date = f"{year}-01-01T00:00:00Z"
    now = datetime.now(timezone.utc)
    # Cap to current time when querying the current or a future year
    if year >= now.year:
        to_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        to_date = f"{year}-12-31T23:59:59Z"

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": CONTRIBUTIONS_QUERY,
        "variables": {
            "username": username,
            "from": from_date,
            "to": to_date,
        },
    }

    try:
        r = requests.post(
            GITHUB_GRAPHQL_URL, json=payload, headers=headers, timeout=15
        )
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            return {"error": data["errors"][0].get("message", "Unknown GraphQL error")}
        user = data.get("data", {}).get("user")
        if user is None:
            return {"error": f"GitHub user '{username}' not found"}
        return user
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
