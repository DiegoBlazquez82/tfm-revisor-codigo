"""Formato del comentario que se publica en el pull request."""

from __future__ import annotations

from .models import Finding

MARKER = "<!-- revisor-agents -->"

_ORDER = {"high": 0, "medium": 1, "low": 2}
_LABEL = {"security": "Seguridad", "smells": "Calidad", "tests": "Tests"}
_ICON = {"high": "🔴", "medium": "🟠", "low": "🟡"}


def aggregate(findings: list[Finding]) -> list[Finding]:
    """Quita duplicados y ordena por gravedad."""
    seen: set[tuple[str, int | None, str]] = set()
    unique: list[Finding] = []
    for item in findings:
        key = (item.file, item.line, item.title.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return sorted(unique, key=lambda f: (_ORDER[f.severity], f.file, f.line or 0))


def render_markdown(findings: list[Finding], files_reviewed: int, truncated: bool) -> str:
    lines = [MARKER, "## Revisión automática del PR", ""]
    lines.append(f"Ficheros revisados: **{files_reviewed}** · Hallazgos: **{len(findings)}**")
    if truncated:
        lines.append("\n> El diff era muy grande y se revisó solo una parte.")
    if not findings:
        lines.append("\nNo se han encontrado problemas. ✅")
        return "\n".join(lines) + "\n"
    for item in findings:
        where = f"`{item.file}`" + (f":{item.line}" if item.line else "")
        lines.append(
            f"\n{_ICON[item.severity]} **[{_LABEL.get(item.agent, item.agent)}] {item.title}**"
            f" — {where}\n{item.detail}"
        )
        if item.suggestion:
            lines.append(f"\n_Sugerencia:_ {item.suggestion}")
    lines.append("\n---\n_Generado por agentes de IA: revísalo antes de actuar._")
    return "\n".join(lines) + "\n"
