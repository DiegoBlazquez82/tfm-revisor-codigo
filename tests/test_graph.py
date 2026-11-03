from revisor.agents import sanitize, summarize_test_coverage
from revisor.diff import parse_diff
from revisor.graph import review_diff
from revisor.models import LLMFinding, LLMFindings
from revisor.report import MARKER, aggregate, render_markdown
from tests.test_diff import SAMPLE


class FakeLLM:
    """Devuelve siempre los mismos hallazgos, sin llamar a ningún modelo."""

    def __init__(self, findings: list[LLMFinding]) -> None:
        self._findings = findings
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return LLMFindings(findings=self._findings)


SQLI = LLMFinding(
    file="app/db.py",
    line=11,
    severity="high",
    title="Inyección SQL",
    detail="La consulta se construye concatenando entrada del usuario.",
    suggestion="Usa parámetros enlazados.",
)


def test_sanitize_drops_hallucinated_files_and_bad_lines():
    files = parse_diff(SAMPLE)
    raw = LLMFindings(
        findings=[
            SQLI,
            LLMFinding(file="no/existe.py", title="x", detail="y"),
            LLMFinding(file="app/db.py", line=999, title="z", detail="w"),
        ]
    )
    result = sanitize(raw, "security", files)
    assert [f.file for f in result] == ["app/db.py", "app/db.py"]
    assert result[0].line == 11
    assert result[1].line is None


def test_summarize_test_coverage_flags_code_without_tests():
    assert "SIN ningún test" in summarize_test_coverage(parse_diff(SAMPLE))


def test_aggregate_removes_duplicates_and_sorts_by_severity():
    files = parse_diff(SAMPLE)
    low = LLMFinding(file="app/db.py", line=12, severity="low", title="Nombre", detail="d")
    findings = sanitize(LLMFindings(findings=[low, SQLI]), "smells", files)
    findings += sanitize(LLMFindings(findings=[SQLI]), "security", files)
    merged = aggregate(findings)
    assert [f.severity for f in merged] == ["high", "low"]


def test_review_diff_runs_all_three_agents_and_builds_report():
    llm = FakeLLM([SQLI])
    report = review_diff(SAMPLE, llm)
    assert llm.calls == 3
    assert report.startswith(MARKER)
    assert "Inyección SQL" in report
    assert "`app/db.py`:11" in report


def test_review_of_empty_diff_does_not_call_the_model():
    llm = FakeLLM([SQLI])
    report = review_diff("", llm)
    assert llm.calls == 0
    assert "No se han encontrado problemas" in report


def test_render_markdown_without_findings():
    assert "No se han encontrado problemas" in render_markdown([], 2)


def test_untested_code_finding_comes_from_a_rule():
    from revisor.agents import untested_code_findings

    findings = untested_code_findings(parse_diff(SAMPLE))
    assert [f.title for f in findings] == ["Código modificado sin tests"]
    assert findings[0].agent == "tests"
    assert findings[0].severity == "medium"


def test_no_untested_warning_when_a_test_is_touched():
    from revisor.agents import untested_code_findings
    from revisor.diff import ChangedFile

    files = [ChangedFile(path="app/db.py"), ChangedFile(path="tests/test_db.py")]
    assert untested_code_findings(files) == []
