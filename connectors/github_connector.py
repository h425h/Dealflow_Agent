import os
import re
from typing import Optional

import requests
from dotenv import load_dotenv

from connectors.base import Connector, ConnectorResult

load_dotenv()

_API = "https://api.github.com"


class GitHubConnector(Connector):
    @property
    def name(self) -> str:
        return "github"

    def _headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _get(self, url: str, params: Optional[dict] = None):
        """GET url; returns parsed JSON on 200, None otherwise (incl. 202 Accepted)."""
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            return r.json() if r.status_code == 200 else None
        except requests.RequestException:
            return None

    def _recent_commits(self, full_name: str) -> Optional[int]:
        """Commits in last 4 weeks from stats/commit_activity (52-week array)."""
        data = self._get(f"{_API}/repos/{full_name}/stats/commit_activity")
        if not isinstance(data, list) or not data:
            return None
        return sum(w.get("total", 0) for w in data[-4:])

    def _contributor_count(self, full_name: str) -> Optional[int]:
        """Total contributor count; reads pagination Link header for accuracy."""
        try:
            r = requests.get(
                f"{_API}/repos/{full_name}/contributors",
                headers=self._headers(),
                params={"per_page": 1, "anon": "false"},
                timeout=10,
            )
        except requests.RequestException:
            return None
        if r.status_code != 200:
            return None
        link = r.headers.get("Link", "")
        m = re.search(r'page=(\d+)>; rel="last"', link)
        return int(m.group(1)) if m else len(r.json())

    def search(self, query: str, max_results: int = 5) -> ConnectorResult:
        # sort=updated (last push date), not stars — recency is harder to fake than star count
        search_data = self._get(
            f"{_API}/search/repositories",
            params={"q": query, "sort": "updated", "order": "desc", "per_page": max_results},
        )
        if search_data is None:
            return ConnectorResult(
                source=self.name,
                query=query,
                items=[],
                confidence=0.0,
                error="GitHub API returned no data (rate limit or network error; set GITHUB_TOKEN to increase limits)",
            )

        repos = search_data.get("items", [])
        if not repos:
            return ConnectorResult(source=self.name, query=query, items=[], confidence=0.0)

        items = []
        for repo in repos:
            full_name = repo["full_name"]
            items.append({
                "name": full_name,
                "url": repo["html_url"],
                "description": (repo.get("description") or "")[:200],
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "recent_commits_4w": self._recent_commits(full_name),
                "contributor_count": self._contributor_count(full_name),
                "pushed_at": repo.get("pushed_at"),
                "is_fork": repo.get("fork", False),
            })

        has_activity = any(it["recent_commits_4w"] is not None for it in items)
        has_contributors = any(it["contributor_count"] is not None for it in items)
        if has_activity and has_contributors:
            confidence = 0.75
        elif has_activity or has_contributors:
            confidence = 0.5
        else:
            confidence = 0.3

        return ConnectorResult(
            source=self.name,
            query=query,
            items=items,
            confidence=confidence,
        )
