"""Parseo mínimo de un diff unificado de git."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_NO_NEWLINE = "\\"


@dataclass
class ChangedFile:
    path: str
    patch: str = ""
    added_lines: dict[int, str] = field(default_factory=dict)


def _count(value: str | None) -> int:
    """En la cabecera de un hunk, un recuento ausente significa 1."""
    return 1 if value is None else int(value)


def parse_diff(text: str) -> list[ChangedFile]:
    """Parsea un diff unificado.

    Dentro de un hunk se usan los recuentos de la cabecera `@@` para saber cuándo termina, de modo
    que una línea añadida que empiece por `++ ` no se confunde con la cabecera `+++ ` de un fichero.
    Las marcas «\\ No newline at end of file» no cuentan como líneas del fichero.
    """
    files: list[ChangedFile] = []
    current: ChangedFile | None = None
    new_line = 0
    old_left = new_left = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            # Una línea de hunk nunca empieza así: cierra el hunk aunque los recuentos fallen.
            current = None
            old_left = new_left = 0
            continue
        if (old_left > 0 or new_left > 0) and current is not None:
            if raw.startswith(_NO_NEWLINE):
                continue
            current.patch += raw + "\n"
            if raw.startswith("+"):
                current.added_lines[new_line] = raw[1:]
                new_line += 1
                new_left -= 1
            elif raw.startswith("-"):
                old_left -= 1
            else:
                new_line += 1
                old_left -= 1
                new_left -= 1
            continue
        if raw.startswith("+++ "):
            target = raw[4:].strip()
            if target == "/dev/null":
                current = None
                continue
            path = target[2:] if target.startswith("b/") else target
            current = ChangedFile(path=path)
            files.append(current)
            continue
        match = _HUNK.match(raw)
        if match and current is not None:
            old_left = _count(match.group(1))
            new_line = int(match.group(2))
            new_left = _count(match.group(3))
            current.patch += raw + "\n"
    return files


def annotate_patch(patch: str) -> str:
    """Antepone `L<n>:` a las líneas añadidas para que el modelo pueda citar la línea exacta."""
    out: list[str] = []
    new_line = 0
    for raw in patch.splitlines():
        match = _HUNK.match(raw)
        if match:
            new_line = int(match.group(2))
            out.append(raw)
        elif raw.startswith(_NO_NEWLINE):
            out.append(raw)
        elif raw.startswith("+"):
            out.append(f"L{new_line}: {raw}")
            new_line += 1
        elif raw.startswith("-"):
            out.append(raw)
        else:
            out.append(raw)
            new_line += 1
    return "\n".join(out) + "\n"


def is_test_file(path: str) -> bool:
    lowered = path.lower().replace("\\", "/")
    name = lowered.rsplit("/", 1)[-1]
    return (
        "/tests/" in f"/{lowered}"
        or "/test/" in f"/{lowered}"
        or name.startswith("test_")
        or name.endswith(("_test.py", ".test.ts", ".test.js", ".spec.ts", ".spec.js"))
    )


_SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".cs", ".rb", ".php")


def is_source_file(path: str) -> bool:
    return path.lower().endswith(_SOURCE_SUFFIXES) and not is_test_file(path)
