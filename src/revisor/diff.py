"""Parseo mínimo de un diff unificado de git."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class ChangedFile:
    path: str
    patch: str = ""
    added_lines: dict[int, str] = field(default_factory=dict)


def parse_diff(text: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    current: ChangedFile | None = None
    new_line = 0
    in_hunk = False
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            current = None
            in_hunk = False
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
        if current is None:
            continue
        match = _HUNK.match(raw)
        if match:
            new_line = int(match.group(1))
            in_hunk = True
            current.patch += raw + "\n"
            continue
        if not in_hunk:
            continue
        current.patch += raw + "\n"
        if raw.startswith("+"):
            current.added_lines[new_line] = raw[1:]
            new_line += 1
        elif raw.startswith("-"):
            continue
        else:
            new_line += 1
    return files


def annotate_patch(patch: str) -> str:
    """Antepone `L<n>:` a las líneas añadidas para que el modelo pueda citar la línea exacta."""
    out: list[str] = []
    new_line = 0
    for raw in patch.splitlines():
        match = _HUNK.match(raw)
        if match:
            new_line = int(match.group(1))
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
