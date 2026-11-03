"""Convierte los casos en diffs que ve el revisor y en las etiquetas que se esperan."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .cases import CASES, Case

_MARKER = re.compile(r"\s*#@ (?P<agent>\w+):(?P<kind>\w+)(?: \+(?P<span>\d+))?\s*$")


@dataclass(frozen=True)
class Expected:
    """Un problema que el revisor debería encontrar."""

    case: str
    agent: str
    kind: str
    file: str
    start: int
    end: int


@dataclass(frozen=True)
class BuiltCase:
    id: str
    category: str
    diff: str
    expected: list[Expected]
    sources: dict[str, str]  # ficheros sin marcas, tal y como los vería el revisor


def strip_markers(case_id: str, path: str, source: str) -> tuple[str, list[Expected]]:
    """Quita las marcas `#@` y devuelve las etiquetas con sus números de línea."""
    clean: list[str] = []
    expected: list[Expected] = []
    for number, line in enumerate(source.splitlines(), start=1):
        match = _MARKER.search(line)
        if match:
            span = int(match.group("span") or 0)
            expected.append(
                Expected(
                    case=case_id,
                    agent=match.group("agent"),
                    kind=match.group("kind"),
                    file=path,
                    start=number,
                    end=number + span,
                )
            )
            line = line[: match.start()]
        clean.append(line)
    return "\n".join(clean) + "\n", expected


def new_file_diff(path: str, source: str) -> str:
    """Diff unificado de un fichero nuevo: los números de línea coinciden con los del fichero."""
    lines = source.splitlines()
    body = "\n".join(f"+{line}" for line in lines)
    return (
        f"diff --git a/{path} b/{path}\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        f"+++ b/{path}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}\n"
    )


def build_case(case: Case) -> BuiltCase:
    diffs: list[str] = []
    expected: list[Expected] = []
    sources: dict[str, str] = {}
    for path, raw in case.files.items():
        clean, found = strip_markers(case.id, path, raw)
        sources[path] = clean
        expected.extend(found)
        diffs.append(new_file_diff(path, clean))
    return BuiltCase(case.id, case.category, "".join(diffs), expected, sources)


def build_all() -> list[BuiltCase]:
    return [build_case(case) for case in CASES]
