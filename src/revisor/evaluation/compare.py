"""Compara dos versiones del revisor evaluadas con los mismos modelos y los mismos casos."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from .dataset import Expected
from .scoring import Counts, Predicted, score_case, summarize

STATIC = "Código modificado sin tests"
AGENTS = ("security", "smells", "tests")


def _load(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    results = [
        (
            [Predicted(**p) for p in rec["predicted"]],
            [Expected(**e) for e in rec["expected"]],
            rec["category"],
        )
        for rec in data["cases"]
    ]
    return data, results


def model_results(directory: Path) -> dict[str, tuple[dict, list]]:
    found: dict[str, tuple[dict, list]] = {}
    for path in sorted(directory.glob("*.json")):
        data, results = _load(path)
        if data["kind"] == "model":
            found[data["name"]] = (data, results)
    return found


def _fmt(counts: Counts, key: str) -> str:
    value = getattr(counts, key)
    return "—" if value is None else f"{value:.2f}"


def _time(data: dict) -> str:
    seconds = [rec["seconds"] for rec in data["cases"]]
    return f"{statistics.mean(seconds):.1f} s" if seconds else "—"


def build_comparison(dir_a: Path, dir_b: Path, label_a: str, label_b: str) -> str:
    a, b = model_results(dir_a), model_results(dir_b)
    common = [name for name in a if name in b]
    out = [f"# Comparación {label_a} frente a {label_b}", ""]
    out.append("_Generado por `revisor.evaluation.compare`._")
    out.append("")
    if not common:
        out.append("No hay modelos comunes en ambas carpetas.")
        return "\n".join(out) + "\n"
    versions = lambda name: ((label_a, a[name]), (label_b, b[name]))  # noqa: E731

    out += ["## Informe final (línea exacta)", ""]
    out.append(
        "| Modelo | Versión | TP | FP | FN | Precisión | Exhaustividad | F1 | Limpios con FP |"
    )
    out.append("|---|---|---|---|---|---|---|---|---|")
    for name in common:
        for label, (_, results) in versions(name):
            summary = summarize(results)
            c = summary.final["strict"]
            out.append(
                f"| {name} | {label} | {c.tp} | {c.fp} | {c.fn} | {_fmt(c, 'precision')} | "
                f"{_fmt(c, 'recall')} | {_fmt(c, 'f1')} | "
                f"{summary.clean_cases_with_false_positive} de {summary.clean_cases} |"
            )

    out += ["", "## Por agente (línea exacta)", ""]
    out.append("| Modelo | Agente | Versión | TP | FP | FN | Precisión | Exhaustividad |")
    out.append("|---|---|---|---|---|---|---|---|")
    for name in common:
        for agent in AGENTS:
            for label, (_, results) in versions(name):
                c = summarize(results).per_agent[agent]["strict"]
                out.append(
                    f"| {name} | {agent} | {label} | {c.tp} | {c.fp} | {c.fn} | "
                    f"{_fmt(c, 'precision')} | {_fmt(c, 'recall')} |"
                )

    out += ["", f"## Descartados por no citar código del diff (solo {label_b})", ""]
    out.append("| Modelo | Descartados | Publicados |")
    out.append("|---|---|---|")
    for name in common:
        data, results = b[name]
        dropped = sum(len(rec.get("dropped", [])) for rec in data["cases"])
        kept = sum(len([p for p in preds if p.title != STATIC]) for preds, _, _ in results)
        out.append(f"| {name} | {dropped} | {kept} |")

    out += ["", "## Casos adversariales", ""]
    out.append("| Modelo | Caso | Versión | Hallazgos publicados | Detecta el fallo real |")
    out.append("|---|---|---|---|---|")
    for name in common:
        for label, (data, results) in versions(name):
            for rec, (preds, expected, _) in zip(data["cases"], results, strict=True):
                if not rec["id"].startswith("adv"):
                    continue
                real = [p for p in preds if p.title != STATIC]
                if not expected:
                    hit = "— (no hay fallo real)"
                else:
                    found = score_case(preds, expected, agent=None, strict=True).tp
                    hit = "sí" if found else "no"
                out.append(f"| {name} | {rec['id'][:5]} | {label} | {len(real)} | {hit} |")

    out += ["", "## Tiempo medio por caso", "", "| Modelo | Versión | Tiempo |", "|---|---|---|"]
    for name in common:
        for label, (data, _) in versions(name):
            out.append(f"| {name} | {label} | {_time(data)} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="revisor-compare")
    parser.add_argument("--a", default="eval/results/v1")
    parser.add_argument("--b", default="eval/results/v2")
    parser.add_argument("--label-a", default="v1")
    parser.add_argument("--label-b", default="v2")
    parser.add_argument("--out", default="docs/evaluacion-comparacion.md")
    args = parser.parse_args(argv)
    text = build_comparison(Path(args.a), Path(args.b), args.label_a, args.label_b)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"comparación en {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
