"""Formato del comentario que se publica en el pull request."""

from __future__ import annotations

import re

from .models import Finding

MARKER = "<!-- revisor-agents -->"

_ORDER = {"high": 0, "medium": 1, "low": 2}
_AGENT_PRIORITY = {"security": 0, "smells": 1, "tests": 2}
_LABEL = {"security": "Seguridad", "smells": "Calidad", "tests": "Tests"}
_ICON = {"high": "🔴", "medium": "🟠", "low": "🟡"}

MAX_TITLE = 120
MAX_DETAIL = 600
MAX_SUGGESTION = 400
_ZWSP = "​"  # espacio de ancho cero: rompe menciones y referencias sin cambiar el aspecto
# Solo lo necesario para que no se formen enlaces, imágenes ni énfasis. Los backticks se dejan
# (un código entre `comillas` es útil y no permite inyectar nada) y los paréntesis también:
# sin `[` ni `]` activos no hay enlace posible.
_MD_SPECIAL = re.compile(r"([\\*_\[\]])")
_ISSUE_REF = re.compile(r"#(?=\d)")
# split() con un grupo de captura deja los fragmentos de código en las posiciones impares.
_CODE_SPAN = re.compile(r"(`[^`\n]*`)")


def escape_md(text: str, limit: int | None = None, single_line: bool = False) -> str:
    """Deja el texto del modelo inerte al publicarlo en Markdown de GitHub.

    El texto procede de un modelo que ha leído datos de un tercero, así que no se confía en él:
    se neutralizan HTML (incluida la marca oculta del revisor), menciones `@usuario`, referencias
    `#123`, enlaces e imágenes, y se limita la longitud.
    """
    if single_line:
        text = " ".join(text.split())
    if limit is not None and len(text) > limit:
        text = text[: limit - 1] + "…"
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Dentro de `código` GitHub no interpreta Markdown, ni menciones, ni referencias: se deja tal
    # cual para que nombres como `find_user` se lean bien. Fuera sí se neutraliza.
    parts = _CODE_SPAN.split(text)
    for i in range(0, len(parts), 2):
        piece = parts[i].replace("@", "@" + _ZWSP)
        piece = _ISSUE_REF.sub("#" + _ZWSP, piece)
        parts[i] = _MD_SPECIAL.sub(r"\\\1", piece)
    return "".join(parts)


def aggregate(findings: list[Finding]) -> list[Finding]:
    """Una sola entrada por (fichero, línea): gana la más grave y, a igualdad, la de seguridad."""
    ranked = sorted(
        findings, key=lambda f: (_ORDER[f.severity], _AGENT_PRIORITY.get(f.agent, 9))
    )
    seen: set[tuple[str, int | None, str]] = set()
    unique: list[Finding] = []
    for item in ranked:
        # Sin línea no se puede afirmar que sea el mismo problema: se distingue por título.
        key = (item.file, item.line, "" if item.line else item.title.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return sorted(unique, key=lambda f: (_ORDER[f.severity], f.file, f.line or 0))


def _location(item: Finding) -> str:
    path = item.file.replace("`", "'")
    if len(path) > 200:
        path = path[:199] + "…"
    where = f"`{path}`"
    return where + (f":{item.line}" if item.line else "")


def render_markdown(
    findings: list[Finding],
    files_reviewed: int,
    omitted: list[str] | None = None,
    errors: list[str] | None = None,
) -> str:
    omitted = omitted or []
    errors = errors or []
    lines = [MARKER, "## Revisión automática del PR", ""]
    lines.append(f"Ficheros revisados: **{files_reviewed}** · Hallazgos: **{len(findings)}**")
    if omitted:
        names = ", ".join(f"`{escape_md(n, 120, single_line=True)}`" for n in omitted[:10])
        extra = f" y {len(omitted) - 10} más" if len(omitted) > 10 else ""
        lines.append(f"\n> ⚠️ El diff era grande: no se revisó entero. Afectados: {names}{extra}.")
    if errors:
        failed = ", ".join(escape_md(e, 80, single_line=True) for e in errors)
        lines.append(
            f"\n> ⚠️ Parte de la revisión falló y está incompleta ({failed}). "
            "Que no aparezcan hallazgos de esa categoría no significa que no los haya."
        )
    if not findings:
        if errors or omitted:
            lines.append("\nNo hay hallazgos en lo que se pudo revisar.")
        else:
            lines.append("\nNo se han encontrado problemas. ✅")
        return "\n".join(lines) + "\n"
    for item in findings:
        title = escape_md(item.title, MAX_TITLE, single_line=True)
        lines.append(
            f"\n{_ICON[item.severity]} **[{_LABEL.get(item.agent, item.agent)}] {title}**"
            f" — {_location(item)}\n{escape_md(item.detail, MAX_DETAIL)}"
        )
        if item.suggestion:
            lines.append(f"\n_Sugerencia:_ {escape_md(item.suggestion, MAX_SUGGESTION)}")
    lines.append("\n---\n_Generado por agentes de IA: revísalo antes de actuar._")
    return "\n".join(lines) + "\n"
