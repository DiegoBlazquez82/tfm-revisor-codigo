"""Cliente mínimo de la API de GitHub para leer el diff y comentar en el PR."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import httpx

from .report import MARKER

API = "https://api.github.com"
# Autor de los comentarios que publica GITHUB_TOKEN dentro de Actions.
DEFAULT_AUTHORS = frozenset({"github-actions[bot]"})


class GitHubClient:
    def __init__(
        self,
        token: str,
        repo: str,
        client: httpx.Client | None = None,
        authors: Iterable[str] = DEFAULT_AUTHORS,
    ) -> None:
        self.repo = repo
        self.authors = frozenset(authors)
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

    def _iter_comments(self, pr: int) -> Iterator[dict]:
        """Recorre todas las páginas de comentarios del PR."""
        headers = {**self._headers, "Accept": "application/vnd.github+json"}
        url: str | None = f"{API}/repos/{self.repo}/issues/{pr}/comments"
        params: dict[str, int] | None = {"per_page": 100}
        while url:
            response = self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            yield from response.json()
            next_link = response.links.get("next")
            url = next_link["url"] if next_link else None
            params = None  # la URL de «next» ya lleva sus parámetros

    def find_own_comment(self, pr: int) -> dict | None:
        """Busca el comentario del revisor: lleva la marca Y lo escribió un autor de confianza.

        Comprobar solo la marca permitiría que cualquiera pegara la marca en su comentario y
        provocara un intento de editar un comentario ajeno.
        """
        for comment in self._iter_comments(pr):
            author = (comment.get("user") or {}).get("login")
            if MARKER in comment.get("body", "") and author in self.authors:
                return comment
        return None

    def upsert_comment(self, pr: int, body: str) -> None:
        """Crea el comentario del revisor o lo actualiza si ya existe (no spamea el PR)."""
        headers = {**self._headers, "Accept": "application/vnd.github+json"}
        existing = self.find_own_comment(pr)
        if existing:
            patch = self._client.patch(
                f"{API}/repos/{self.repo}/issues/comments/{existing['id']}",
                headers=headers,
                json={"body": body},
            )
            patch.raise_for_status()
        else:
            post = self._client.post(
                f"{API}/repos/{self.repo}/issues/{pr}/comments",
                headers=headers,
                json={"body": body},
            )
            post.raise_for_status()
