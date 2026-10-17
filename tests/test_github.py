import httpx

from revisor.github import GitHubClient
from revisor.report import MARKER


def make_client(existing: list[dict]):
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "GET":
            return httpx.Response(200, json=existing)
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    return GitHubClient("tok", "o/r", client=httpx.Client(transport=transport)), calls


def test_upsert_creates_comment_when_missing():
    gh, calls = make_client([{"id": 1, "body": "otro comentario"}])
    gh.upsert_comment(5, f"{MARKER}\nhola")
    assert calls[-1] == ("POST", "/repos/o/r/issues/5/comments")


def test_upsert_updates_existing_comment():
    gh, calls = make_client([{"id": 42, "body": f"{MARKER}\nviejo"}])
    gh.upsert_comment(5, f"{MARKER}\nnuevo")
    assert calls[-1] == ("PATCH", "/repos/o/r/issues/comments/42")
