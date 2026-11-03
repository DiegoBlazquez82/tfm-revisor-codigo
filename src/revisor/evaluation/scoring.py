"""Puntuación: compara los hallazgos de un revisor con las etiquetas esperadas."""

from __future__ import annotations

from dataclasses import dataclass, field

from .dataset import Expected

LINE_TOLERANCE = 1
# Aviso determinista (regla, no modelo): se prueba aparte y no entra en la puntuación del modelo.
STATIC_TITLES = {"Código modificado sin tests"}


@dataclass(frozen=True)
class Predicted:
    agent: str
    file: str
    line: int | None
    title: str = ""


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def add(self, other: Counts) -> None:
        self.tp += other.tp
        self.fp += other.fp
        self.fn += other.fn

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)


def line_matches(predicted: Predicted, expected: Expected) -> bool:
    if predicted.line is None:
        return False
    return expected.start - LINE_TOLERANCE <= predicted.line <= expected.end + LINE_TOLERANCE


def score_case(
    predicted: list[Predicted],
    expected: list[Expected],
    *,
    agent: str | None,
    strict: bool,
) -> Counts:
    """Cuenta aciertos, falsos positivos y omisiones de un caso.

    `agent` limita la comparación a un agente; con `None` se ignora quién lo dijo (informe final).
    Cada etiqueta se empareja como mucho con un hallazgo. `strict` exige acertar la línea; si no,
    basta con acertar el fichero.
    """
    predicted = [p for p in predicted if p.title not in STATIC_TITLES]
    if agent is not None:
        predicted = [p for p in predicted if p.agent == agent]
        expected = [e for e in expected if e.agent == agent]
    free = list(predicted)
    counts = Counts()
    for exp in expected:
        hit = next(
            (p for p in free if p.file == exp.file and (not strict or line_matches(p, exp))),
            None,
        )
        if hit is None:
            counts.fn += 1
        else:
            counts.tp += 1
            free.remove(hit)
    counts.fp = len(free)
    return counts


@dataclass
class Summary:
    """Resultados agregados de un revisor sobre todos los casos."""

    per_agent: dict[str, dict[str, Counts]] = field(default_factory=dict)  # agente -> modo
    final: dict[str, Counts] = field(default_factory=dict)  # modo -> counts
    clean_cases: int = 0
    clean_cases_with_false_positive: int = 0


def summarize(
    results: list[tuple[list[Predicted], list[Expected], str]],
    agents: tuple[str, ...] = ("security", "smells", "tests"),
) -> Summary:
    """`results` es una lista de (predicho, esperado, categoría) por caso."""
    summary = Summary()
    for agent in agents:
        summary.per_agent[agent] = {"strict": Counts(), "lenient": Counts()}
    summary.final = {"strict": Counts(), "lenient": Counts()}
    for predicted, expected, _category in results:
        for agent in agents:
            for mode in ("strict", "lenient"):
                summary.per_agent[agent][mode].add(
                    score_case(predicted, expected, agent=agent, strict=mode == "strict")
                )
        for mode in ("strict", "lenient"):
            summary.final[mode].add(
                score_case(predicted, expected, agent=None, strict=mode == "strict")
            )
        if not expected:
            summary.clean_cases += 1
            real = [p for p in predicted if p.title not in STATIC_TITLES]
            if real:
                summary.clean_cases_with_false_positive += 1
    return summary
