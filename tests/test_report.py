import re

from revisor.models import Finding
from revisor.report import MARKER, escape_md, render_markdown

# Un enlace Markdown activo necesita «](» con el corchete sin escapar.
LIVE_LINK = re.compile(r"(?<!\\)\]\(")


def finding(**overrides) -> Finding:
    base = {
        "agent": "security",
        "file": "app/x.py",
        "line": 3,
        "severity": "high",
        "title": "Título",
        "detail": "Detalle",
        "suggestion": "Arreglo",
    }
    return Finding(**{**base, **overrides})


# --- D1: la salida del modelo se publica inerte --------------------------------------------


def test_mentions_are_neutralized():
    assert "@mallory" not in escape_md("avisa a @mallory")


def test_issue_references_are_neutralized():
    assert "#123" not in escape_md("ver #123")


def test_hidden_marker_cannot_be_forged_by_the_model():
    assert MARKER not in escape_md(f"{MARKER} hola")


def test_html_is_escaped():
    out = escape_md("<script>alert(1)</script><img src=x>")
    assert "<" not in out and ">" not in out


def test_links_and_images_are_defanged():
    out = escape_md("[pincha](http://evil.example) ![x](http://evil.example/p.png)")
    assert not LIVE_LINK.search(out)


def test_text_is_truncated():
    assert len(escape_md("a" * 5_000, limit=100)) <= 101


def test_single_line_collapses_newlines():
    assert "\n" not in escape_md("a\n\n# Encabezado falso", single_line=True)


def test_malicious_finding_does_not_inject_markdown_into_the_report():
    evil = finding(
        title="x\n# Gran titular",
        detail="Cc @admin, mira [aquí](http://evil.example) y #7",
        suggestion=f"{MARKER}",
        file="a`b.py",
    )
    report = render_markdown([evil], 1)
    assert report.count(MARKER) == 1  # solo la marca legítima de la cabecera
    assert "@admin" not in report
    assert not LIVE_LINK.search(report)
    assert "\n# Gran titular" not in report


# --- E3 / D3: el informe no miente ----------------------------------------------------------


def test_report_lists_omitted_files():
    report = render_markdown([], 3, omitted=["big.py (recortado)"])
    assert "no se revisó entero" in report
    assert "big.py" in report
    assert "No se han encontrado problemas" not in report


def test_report_warns_when_an_agent_failed_and_never_claims_all_clear():
    report = render_markdown([], 1, errors=["security: ConnectionError"])
    assert "incompleta" in report
    assert "security: ConnectionError" in report
    assert "No se han encontrado problemas" not in report


def test_clean_report_when_nothing_went_wrong():
    assert "No se han encontrado problemas" in render_markdown([], 1)


def test_identifiers_inside_code_spans_stay_readable():
    assert "`find_user`" in escape_md("la función `find_user` es vulnerable")


def test_mentions_inside_code_spans_are_left_alone_but_outside_are_not():
    out = escape_md("`@decorador` y @mallory")
    assert "`@decorador`" in out
    assert "@mallory" not in out
