"""Validación por cita literal: un hallazgo debe apuntar a código real del diff."""

from revisor.agents import make_agent, validate_evidence
from revisor.diff import ChangedFile
from revisor.models import Finding, LLMFinding, LLMFindings


def changed(lines: dict[int, str], path: str = "app/x.py") -> ChangedFile:
    return ChangedFile(path=path, patch="", added_lines=lines)


def finding(evidence: str, line: int | None = 3, title: str = "t", file: str = "app/x.py"):
    return Finding(
        agent="security", file=file, line=line, title=title, detail="d", evidence=evidence
    )


CODE = {
    1: "import os",
    2: "# nota: usa os.system con cuidado",
    3: 'os.system("ping " + host)',
    4: "return 0",
}


def test_quote_present_in_an_added_code_line_is_kept():
    kept, dropped = validate_evidence([finding('os.system("ping " + host)')], [changed(CODE)])
    assert len(kept) == 1 and dropped == []


def test_missing_evidence_is_dropped():
    kept, dropped = validate_evidence([finding("")], [changed(CODE)])
    assert kept == [] and len(dropped) == 1


def test_fabricated_quote_is_dropped():
    kept, dropped = validate_evidence([finding("API_KEY = 'sk_live_123'")], [changed(CODE)])
    assert kept == [] and len(dropped) == 1


def test_a_quote_that_only_appears_in_a_comment_is_dropped():
    """Un comentario puede contener una orden para el modelo: no vale como evidencia."""
    comment_only = finding("usa os.system con cuidado", line=2)
    kept, dropped = validate_evidence([comment_only], [changed(CODE)])
    assert kept == [] and len(dropped) == 1


def test_line_is_reanchored_to_where_the_quote_really_is():
    kept, _ = validate_evidence([finding('os.system("ping " + host)', line=99)], [changed(CODE)])
    assert kept[0].line == 3


def test_missing_line_is_filled_in_from_the_quote():
    kept, _ = validate_evidence([finding("return 0", line=None)], [changed(CODE)])
    assert kept[0].line == 4


def test_with_several_matches_the_closest_to_the_stated_line_wins():
    lines = {1: "x = eval(a)", 2: "pass", 10: "y = eval(b)"}
    kept, _ = validate_evidence([finding("eval(", line=9)], [changed(lines)])
    assert kept[0].line == 10


def test_whitespace_differences_are_ignored():
    kept, _ = validate_evidence([finding('os.system("ping "     +    host)')], [changed(CODE)])
    assert len(kept) == 1


def test_model_prefixes_and_quotes_around_the_quote_are_tolerated():
    for evidence in ('L3: +os.system("ping " + host)', '`os.system("ping " + host)`',
                     '+os.system("ping " + host)'):
        kept, _ = validate_evidence([finding(evidence)], [changed(CODE)])
        assert len(kept) == 1, evidence


def test_multiline_quote_uses_its_first_line():
    kept, _ = validate_evidence([finding('os.system("ping " + host)\nreturn 0')], [changed(CODE)])
    assert len(kept) == 1


def test_a_too_short_quote_is_not_accepted():
    kept, dropped = validate_evidence([finding("os")], [changed(CODE)])
    assert kept == [] and len(dropped) == 1


def test_finding_on_a_file_that_is_not_in_the_diff_is_dropped():
    kept, dropped = validate_evidence([finding("return 0", file="otro.py")], [changed(CODE)])
    assert kept == [] and len(dropped) == 1


# --- integrado en el agente ----------------------------------------------------------------


class Canned:
    def __init__(self, items: list[LLMFinding]) -> None:
        self.items = items

    def invoke(self, messages):
        return LLMFindings(findings=self.items)


def test_agent_keeps_real_findings_and_reports_the_dropped_ones():
    real = LLMFinding(file="app/x.py", line=3, title="real", detail="d",
                      evidence='os.system("ping " + host)')
    fake = LLMFinding(file="app/x.py", line=3, title="inventado", detail="d",
                      evidence="password = 'x'")
    result = make_agent("security", "I", Canned([real, fake]))({"files": [changed(CODE)]})
    assert [f.title for f in result["findings"]] == ["real"]
    assert result["dropped"] == ["security: inventado"]


def test_prompts_ask_for_a_literal_quote():
    from revisor.agents import SECURITY_INSTRUCTIONS, SMELLS_INSTRUCTIONS, TESTS_INSTRUCTIONS

    for prompt in (SECURITY_INSTRUCTIONS, SMELLS_INSTRUCTIONS, TESTS_INSTRUCTIONS):
        assert '"evidence"' in prompt and "LITERALMENTE" in prompt
