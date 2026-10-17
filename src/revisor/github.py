"""Cliente mínimo de la API de GitHub para leer el diff y comentar en el PR."""

from __future__ import annotations

import httpx

from .report import MARKER

API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, repo: str, client: httpx.Client | None = None) -> None:
        self.repo = repo
        self._client = client or httpx.Client(timeout=30)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_pr_diff(self, pr: int) -> str:
        response = self._client.get(
            f"{API}/repos/{self.repo}/pulls/{pr}",
            headers={**self._headers, "Accept": "application/vnd.github.v3.diff"},
        )
        response.raise_for_status()
        return response.text

    def upsert_comment(self, pr: int, body: str) -> None:
        """Crea el comentario del revisor o lo actualiza si ya existe (no spamea el PR)."""
        url = f"{API}/repos/{self.repo}/issues/{pr}/comments"
        headers = {**self._headers, "Accept": "application/vnd.github+json"}
        response = self._client.get(url, headers=headers, params={"per_page": 100})
        response.raise_for_status()
        existing = next((c for c in response.json() if MARKER in c.get("body", "")), None)
        if existing:
            patch = self._client.patch(
                f"{API}/repos/{self.repo}/issues/comments/{existing['id']}",
                headers=headers,
                json={"body": body},
            )
            patch.raise_for_status()
        else:
            post = self._client.post(url, headers=headers, json={"body": body})
            post.raise_for_status()
