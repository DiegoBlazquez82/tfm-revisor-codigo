# ruff: noqa: E501
"""Ejecuta la evaluación y genera el informe.

    uv run --group eval python -m revisor.evaluation.run models --model qwen2.5:7b-instruct
    uv run --group eval python -m revisor.evaluation.run baselines
    uv run --group eval python -m revisor.evaluation.run report
    uv run python -m revisor.evaluation.run export-dataset
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path

from .dataset import BuiltCase, Expected, build_all
from .scoring import Counts, Predicted, summarize

RESULTS_DIR = Path("eval/results")
DATASET_DIR = Path("eval/dataset")


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _expected_to_json(items: list[Expected]) -> list[dict]:
    return [e.__dict__ for e in items]


def _predicted_to_json(items: list[Predicted]) -> list[dict]:
    return [p.__dict__ for p in items]


def run_models(args: argparse.Namespace) -> int:
    from ..cli import build_llm
    from ..graph import review_state

    os.environ["OLLAMA_MODEL"] = args.model
    llm = build_llm()
    cases = _select(build_all(), args.cases)
    records = []
    for index, built in enumerate(cases, start=1):
        started = time.perf_counter()
        state = review_state(built.diff, llm)
        seconds = time.perf_counter() - started
        predicted = [
            Predicted(f.agent, f.file, f.line, f.title) for f in state.get("findings", [])
        ]
        records.append(
            {
                "id": built.id,
                "category": built.category,
                "seconds": round(seconds, 2),
                "errors": state.get("errors", []),
                "dropped": state.get("dropped", []),
                "expected": _expected_to_json(built.expected),
                "predicted": _predicted_to_json(predicted),
            }
        )
        print(f"[{index}/{len(cases)}] {built.id}: {seconds:5.1f}s, {len(predicted)} hallazgos")
    out = Path(args.out) if args.out else RESULTS_DIR / f"{slug(args.model)}.json"
    _save(out, {"name": args.model, "kind": "model", "date": str(date.today()), "cases": records})
    return 0


def run_baselines(args: argparse.Namespace) -> int:
    from .baselines import run_bandit, run_ruff

    cases = _select(build_all(), args.cases)
    for name, runner in (("bandit", run_bandit), ("ruff", run_ruff)):
        records = []
        for built in cases:
            started = time.perf_counter()
            predicted = runner(built)
            records.append(
                {
                    "id": built.id,
                    "category": built.category,
                    "seconds": round(time.perf_counter() - started, 2),
                    "errors": [],
                    "expected": _expected_to_json(built.expected),
                    "predicted": _predicted_to_json(predicted),
                }
            )
        _save(
            RESULTS_DIR / f"{name}.json",
            {"name": name, "kind": "baseline", "date": str(date.today()), "cases": records},
        )
        print(f"{name}: {sum(len(r['predicted']) for r in records)} hallazgos")
    return 0


def export_dataset(_: argparse.Namespace) -> int:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    labels = []
    for built in build_all():
        (DATASET_DIR / f"{built.id}.diff").write_text(built.diff, encoding="utf-8", newline="\n")
        labels.extend(_expected_to_json(built.expected))
    (DATASET_DIR / "labels.json").write_text(
        json.dumps(labels, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{len(build_all())} casos exportados a {DATASET_DIR}")
    return 0


def _select(cases: list[BuiltCase], wanted: str | None) -> list[BuiltCase]:
    if not wanted:
        return cases
    ids = {item.strip() for item in wanted.split(",")}
    return [c for c in cases if c.id in ids or any(c.id.startswith(i) for i in ids)]


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"guardado en {path}")


# ----------------------------------------------------------------------------- informe --


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


def _fmt(counts: Counts, key: str) -> str:
    value = getattr(counts, key)
    return "—" if value is None else f"{value:.2f}"


def _row(label: str, counts: Counts) -> str:
    return (
        f"| {label} | {counts.tp} | {counts.fp} | {counts.fn} | "
        f"{_fmt(counts, 'precision')} | {_fmt(counts, 'recall')} | {_fmt(counts, 'f1')} |"
    )


def _times(data: dict) -> str:
    seconds = [rec["seconds"] for rec in data["cases"]]
    if not seconds:
        return "—"
    ordered = sorted(seconds)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    return f"{statistics.mean(seconds):.1f} s (mediana {statistics.median(seconds):.1f}, p95 {p95:.1f})"


def build_report(files: list[Path]) -> str:
    lines = ["# Resultados de la evaluación", "", "_Generado por `revisor.evaluation.run report`._", ""]
    loaded = [_load(path) for path in files]
    models = [(d, r) for d, r in loaded if d["kind"] == "model"]
    baselines = [(d, r) for d, r in loaded if d["kind"] == "baseline"]
    cases = loaded[0][0]["cases"] if loaded else []
    lines.append(f"Casos: **{len(cases)}** · etiquetas esperadas: "
                 f"**{sum(len(c['expected']) for c in cases)}**\n")

    lines += ["## Resumen (línea exacta)", "",
              "| Sistema | Agente | TP | FP | FN | Precisión | Exhaustividad | F1 |",
              "|---|---|---|---|---|---|---|---|"]
    for data, results in models + baselines:
        summary = summarize(results)
        agents = ["security", "smells", "tests"] if data["kind"] == "model" else (
            ["security"] if data["name"] == "bandit" else ["smells"])
        for agent in agents:
            lines.append(_row(f"{data['name']} | {agent}", summary.per_agent[agent]["strict"]))
        if data["kind"] == "model":
            lines.append(_row(f"{data['name']} | **informe final**", summary.final["strict"]))
    lines += ["", "«Línea exacta»: el hallazgo debe caer en la línea etiquetada (±1).", ""]

    lines += ["## Solo el fichero (se perdona la línea)", "",
              "| Sistema | Agente | TP | FP | FN | Precisión | Exhaustividad | F1 |",
              "|---|---|---|---|---|---|---|---|"]
    for data, results in models + baselines:
        summary = summarize(results)
        agents = ["security", "smells", "tests"] if data["kind"] == "model" else (
            ["security"] if data["name"] == "bandit" else ["smells"])
        for agent in agents:
            lines.append(_row(f"{data['name']} | {agent}", summary.per_agent[agent]["lenient"]))
    lines.append("")

    lines += ["## Falsos positivos en casos sin problemas y tiempo", "",
              "| Sistema | Casos sin problemas con falso positivo | Tiempo por caso | Agentes caídos |",
              "|---|---|---|---|"]
    for data, results in models + baselines:
        summary = summarize(results)
        down = sum(1 for rec in data["cases"] if rec["errors"])
        lines.append(
            f"| {data['name']} | {summary.clean_cases_with_false_positive} de {summary.clean_cases}"
            f" | {_times(data)} | {down} |"
        )
    lines.append("")

    lines += ["## Por tipo de caso (informe final, línea exacta)", "",
              "| Sistema | Categoría | Casos | TP | FP | FN |", "|---|---|---|---|---|---|"]
    for data, results in models:
        for category in ("security", "smells", "tests", "clean", "adversarial"):
            subset = [r for r in results if r[2] == category]
            summary = summarize(subset)
            c = summary.final["strict"]
            lines.append(f"| {data['name']} | {category} | {len(subset)} | {c.tp} | {c.fp} | {c.fn} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def report(args: argparse.Namespace) -> int:
    files = sorted(Path(args.results).glob("*.json"))
    if not files:
        print("No hay resultados en", args.results)
        return 1
    text = build_report(files)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"informe en {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="revisor-eval")
    sub = parser.add_subparsers(dest="command", required=True)
    models = sub.add_parser("models", help="Evalúa un modelo de Ollama")
    models.add_argument("--model", required=True)
    models.add_argument("--cases", help="Ids o prefijos separados por comas (por defecto, todos)")
    models.add_argument("--out")
    models.set_defaults(func=run_models)
    base = sub.add_parser("baselines", help="Ejecuta Bandit y Ruff")
    base.add_argument("--cases")
    base.set_defaults(func=run_baselines)
    export = sub.add_parser("export-dataset", help="Escribe los diffs y las etiquetas")
    export.set_defaults(func=export_dataset)
    rep = sub.add_parser("report", help="Genera el informe en Markdown")
    rep.add_argument("--results", default=str(RESULTS_DIR))
    rep.add_argument("--out", default="docs/evaluacion-resultados.md")
    rep.set_defaults(func=report)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
