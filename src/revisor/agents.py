"""Agentes revisores. Cada uno es un nodo del grafo con su propio criterio."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from .diff import ChangedFile, annotate_patch, is_source_file, is_test_file
from .models import Finding, LLMFindings

MAX_DIFF_CHARS = 12_000


class StructuredLLM(Protocol):
    """Lo mínimo que necesitan los agentes; permite sustituir el modelo en los tests."""

    def invoke(self, messages: Any) -> LLMFindings: ...


SECURITY_INSTRUCTIONS = """Eres un revisor de seguridad de aplicaciones. Analiza SOLO las líneas
añadidas del diff y busca problemas del OWASP Top 10: control de acceso roto, fallos criptográficos,
inyección (SQL, comandos, XSS), diseño inseguro, mala configuración, componentes vulnerables,
fallos de autenticación, integridad de datos, falta de logging y SSRF. Señala también secretos o
claves escritos en el código. No inventes problemas: si no hay ninguno, devuelve una lista vacía.
Gravedad: "high" = explotable o con impacto directo (inyección, secretos, autenticación rota);
"medium" = riesgo real pero acotado; "low" = mejora menor. En "line" pon el número que aparece
como L<n> en la línea añadida donde está el problema."""

SMELLS_INSTRUCTIONS = """Eres un revisor de calidad de código. Ignora la seguridad (otro agente
la revisa). Analiza SOLO las líneas añadidas del diff y detecta code smells: funciones largas o con demasiadas responsabilidades, duplicación,
nombres poco claros, números mágicos, anidamiento excesivo, manejo de errores deficiente, código
muerto y acoplamiento innecesario. Prioriza lo que de verdad perjudica el mantenimiento. No
inventes problemas: si no hay ninguno, devuelve una lista vacía.
Gravedad: "high" = explotable o con impacto directo (inyección, secretos, autenticación rota);
"medium" = riesgo real pero acotado; "low" = mejora menor. En "line" pon el número que aparece
como L<n> en la línea añadida donde está el problema."""

TESTS_INSTRUCTIONS = """Eres un revisor de pruebas. Ignora seguridad y estilo (otros
agentes los revisan). Evalúa si el cambio está bien cubierto: casos límite sin probar, tests que no comprueban nada, dependencias externas sin aislar y
comportamiento nuevo sin ningún test. Usa también el resumen de cobertura que se te da. No inventes
problemas: si no hay ninguno, devuelve una lista vacía.
Gravedad: "high" = explotable o con impacto directo (inyección, secretos, autenticación rota);
"medium" = riesgo real pero acotado; "low" = mejora menor. En "line" pon el número que aparece
como L<n> en la línea añadida donde está el problema."""


def render_diff(files: list[ChangedFile], limit: int = MAX_DIFF_CHARS) -> tuple[str, bool]:
    """Devuelve el diff como texto para el prompt y si se tuvo que recortar."""
    parts: list[str] = []
    used = 0
    for changed in files:
        block = f"### {changed.path}\n{annotate_patch(changed.patch)}"
        if used + len(block) > limit:
            return "\n".join(parts), True
        parts.append(block)
        used += len(block)
    return "\n".join(parts), False


def summarize_test_coverage(files: list[ChangedFile]) -> str:
    sources = [f.path for f in files if is_source_file(f.path)]
    tests = [f.path for f in files if is_test_file(f.path)]
    if sources and not tests:
        return "Ficheros de código modificados SIN ningún test tocado: " + ", ".join(sources)
    if sources:
        return f"Código modificado: {', '.join(sources)}. Tests tocados: {', '.join(tests)}."
    return "El cambio no toca código de producción."


def untested_code_findings(files: list[ChangedFile]) -> list[Finding]:
    """Aviso determinista (sin modelo): hay código de producción nuevo y ningún test tocado."""
    if any(is_test_file(f.path) for f in files):
        return []
    return [
        Finding(
            agent="tests",
            file=f.path,
            severity="medium",
            title="Código modificado sin tests",
            detail="Este PR cambia código de producción pero no añade ni modifica ningún test.",
            suggestion="Añade pruebas que cubran el comportamiento nuevo y sus casos límite.",
        )
        for f in files
        if is_source_file(f.path)
    ]


def sanitize(raw: LLMFindings, agent: str, files: list[ChangedFile]) -> list[Finding]:
    """Descarta hallazgos sobre ficheros que no están en el diff y ajusta las líneas."""
    by_path = {f.path: f for f in files}
    findings: list[Finding] = []
    for item in raw.findings:
        changed = by_path.get(item.file)
        if changed is None:
            continue
        line = item.line if item.line in changed.added_lines else None
        findings.append(Finding(**{**item.model_dump(), "line": line, "agent": agent}))
    return findings


def make_agent(
    name: str,
    instructions: str,
    llm: StructuredLLM,
    context: Callable[[list[ChangedFile]], str] | None = None,
    static: Callable[[list[ChangedFile]], list[Finding]] | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def run(state: dict[str, Any]) -> dict[str, Any]:
        files: list[ChangedFile] = state["files"]
        diff_text, _ = render_diff(files)
        extra = f"\n\nContexto adicional:\n{context(files)}" if context else ""
        messages = [
            ("system", instructions),
            ("human", f"Diff a revisar:\n{diff_text}{extra}"),
        ]
        raw = llm.invoke(messages)
        found = sanitize(raw, name, files)
        if static:
            found = static(files) + found
        return {"findings": found}

    return run


def build_agents(llm: StructuredLLM) -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    return {
        "security": make_agent("security", SECURITY_INSTRUCTIONS, llm),
        "smells": make_agent("smells", SMELLS_INSTRUCTIONS, llm),
        "tests": make_agent(
            "tests",
            TESTS_INSTRUCTIONS,
            llm,
            context=summarize_test_coverage,
            static=untested_code_findings,
        ),
    }
