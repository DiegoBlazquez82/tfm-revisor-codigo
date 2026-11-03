import httpx

from revisor.github import GitHubClient
from revisor.report import MARKER

BOT = {"login": "github-actions[bot]"}
HUMAN = {"login": "mallory"}


def make_client(pages: list[list[dict]]):
    """Servidor falso con comentarios paginados mediante la cabecera Link."""
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "GET":
            page = int(request.url.params.get("page", "1"))
            headers = {}
            if page < len(pages):
                headers["Link"] = (
                    f'<https://api.github.com{request.url.path}?page={page + 1}>; rel="next"'
                )
            return httpx.Response(200, json=pages[page - 1], headers=headers)
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    return GitHubClient("tok", "o/r", client=httpx.Client(transport=transport)), calls


def test_upsert_creates_comment_when_missing():
    gh, calls = make_client([[{"id": 1, "body": "otro comentario", "user": HUMAN}]])
    gh.upsert_comment(5, f"{MARKER}\nhola")
    assert calls[-1] == ("POST", "/repos/o/r/issues/5/comments")


def test_upsert_updates_existing_comment_from_the_bot():
    gh, calls = make_client([[{"id": 42, "body": f"{MARKER}\nviejo", "user": BOT}]])
    gh.upsert_comment(5, f"{MARKER}\nnuevo")
    assert calls[-1] == ("PATCH", "/repos/o/r/issues/comments/42")


def test_comment_with_the_marker_from_another_user_is_ignored():
    """Alguien pega la marca en su comentario: no se debe intentar editarlo."""
    gh, calls = make_client([[{"id": 7, "body": f"{MARKER} spoof", "user": HUMAN}]])
    gh.upsert_comment(5, f"{MARKER}\nnuevo")
    assert calls[-1] == ("POST", "/repos/o/r/issues/5/comments")
    assert all(method != "PATCH" for method, _ in calls)


def test_finds_the_comment_on_a_later_page():
    first = [{"id": i, "body": "x", "user": HUMAN} for i in range(100)]
    second = [{"id": 999, "body": f"{MARKER}\nviejo", "user": BOT}]
    gh, calls = make_client([first, second])
    gh.upsert_comment(5, f"{MARKER}\nnuevo")
    assert calls[-1] == ("PATCH", "/repos/o/r/issues/comments/999")
    assert sum(1 for method, _ in calls if method == "GET") == 2


def test_custom_author_can_be_trusted():
    pages = [[{"id": 3, "body": f"{MARKER}", "user": {"login": "diego"}}]]
    transport_calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        transport_calls.append((request.method, request.url.path))
        return httpx.Response(200, json=pages[0] if request.method == "GET" else {})

    gh = GitHubClient(
        "tok", "o/r", client=httpx.Client(transport=httpx.MockTransport(handler)), authors=["diego"]
    )
    gh.upsert_comment(1, f"{MARKER}\nnuevo")
    assert transport_calls[-1] == ("PATCH", "/repos/o/r/issues/comments/3")
