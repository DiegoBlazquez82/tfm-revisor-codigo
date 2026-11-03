"""Líneas base sin IA: Bandit (seguridad) y Ruff (calidad) sobre el mismo código de los casos.

Sirven para responder a «¿qué aporta el modelo frente a un analizador estático que ya existe y es
gratis?». Semgrep no se incluye: no tiene soporte oficial en Windows, donde se ha hecho el trabajo.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .dataset import BuiltCase
from .scoring import Predicted

# Reglas de Ruff que se acercan a lo que busca el agente de calidad.
RUFF_SELECT = "C901,PLR0913,PLR2004,E722,PLR1702"
RUFF_CONFIG = "lint.mccabe.max-complexity = 4"


def _write(case: BuiltCase, root: Path) -> None:
    for path, source in case.sources.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")


def _relative(filename: str, root: Path) -> str:
    return Path(filename).resolve().relative_to(root.resolve()).as_posix()


def run_bandit(case: BuiltCase) -> list[Predicted]:
    """Bandit sobre el código del caso (se omite B101, el `assert` de los tests)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(case, root)
        proc = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", str(root), "-f", "json", "-q", "-s", "B101"],
            capture_output=True,
            text=True,
            check=False,
        )
        data = json.loads(proc.stdout or "{}")
        return [
            Predicted(
                agent="security",
                file=_relative(item["filename"], root),
                line=item["line_number"],
                title=f"{item['test_id']} {item['issue_text']}",
            )
            for item in data.get("results", [])
        ]


def run_ruff(case: BuiltCase) -> list[Predicted]:
    """Ruff con reglas de complejidad, anidamiento, valores mágicos y `except` desnudo."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(case, root)
        proc = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check", "--isolated", "--preview",
                "--select", RUFF_SELECT, "--config", RUFF_CONFIG,
                "--output-format", "json", str(root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )  # fmt: skip
        data = json.loads(proc.stdout or "[]")
        return [
            Predicted(
                agent="smells",
                file=_relative(item["filename"], root),
                line=item["location"]["row"],
                title=f"{item['code']} {item['message']}",
            )
            for item in data
            if not _relative(item["filename"], root).startswith("tests/")
        ]
