import pytest

from revisor import cli
from revisor.models import LLMFinding, LLMFindings
from tests.test_diff import SAMPLE


class FakeStructured:
    def invoke(self, messages):
        return LLMFindings(
            findings=[
                LLMFinding(file="app/db.py", line=11, severity="high", title="SQLi", detail="d")
            ]
        )


def test_main_reviews_a_diff_file(tmp_path, monkeypatch, capsys):
    diff = tmp_path / "cambio.diff"
    diff.write_text(SAMPLE, encoding="utf-8")
    monkeypatch.setattr(cli, "build_llm", lambda: FakeStructured())
    assert cli.main(["review", "--diff-file", str(diff)]) == 0
    out = capsys.readouterr().out
    assert "SQLi" in out
    assert "`app/db.py`:11" in out


def test_main_requires_a_source_for_the_diff(monkeypatch):
    monkeypatch.setattr(cli, "build_llm", lambda: FakeStructured())
    with pytest.raises(SystemExit):
        cli.main(["review"])


def test_main_needs_a_token_for_a_remote_pr(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        cli.main(["review", "--repo", "o/r", "--pr", "1"])


def test_post_with_a_local_diff_is_rejected(tmp_path, monkeypatch):
    diff = tmp_path / "c.diff"
    diff.write_text(SAMPLE, encoding="utf-8")
    monkeypatch.setattr(cli, "build_llm", lambda: FakeStructured())
    with pytest.raises(SystemExit):
        cli.main(["review", "--diff-file", str(diff), "--post"])
