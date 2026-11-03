"""Tests del arnés de evaluación (no usan red ni modelos)."""

from revisor.diff import parse_diff
from revisor.evaluation.cases import CASES
from revisor.evaluation.dataset import Expected, build_all, new_file_diff, strip_markers
from revisor.evaluation.scoring import (
    Counts,
    Predicted,
    score_case,
    summarize,
)

VALID_AGENTS = {"security", "smells", "tests"}
VALID_CATEGORIES = {"security", "smells", "tests", "clean", "adversarial"}


# --- el conjunto de casos es coherente ---------------------------------------------------------


def test_case_ids_are_unique():
    ids = [c.id for c in CASES]
    assert len(ids) == len(set(ids))


def test_categories_and_agents_are_valid():
    for built in build_all():
        assert built.category in VALID_CATEGORIES
        assert {e.agent for e in built.expected} <= VALID_AGENTS


def test_every_label_points_to_a_real_added_line():
    for built in build_all():
        files = {f.path: f for f in parse_diff(built.diff)}
        for exp in built.expected:
            assert exp.file in files, built.id
            assert exp.start in files[exp.file].added_lines, (built.id, exp)
            assert exp.end >= exp.start


def test_markers_never_reach_the_reviewer():
    for built in build_all():
        assert "#@" not in built.diff, built.id


def test_dataset_has_positive_clean_and_adversarial_cases():
    cats = {c.category for c in CASES}
    assert {"security", "smells", "tests", "clean", "adversarial"} <= cats
    assert sum(len(c.expected) for c in build_all()) >= 20


def test_clean_cases_have_no_labels():
    for built in build_all():
        if built.category == "clean":
            assert built.expected == [], built.id


# --- construcción de diffs y etiquetas --------------------------------------------------------


def test_strip_markers_removes_marker_and_records_line_and_span():
    source = "a = 1\nb = eval(x)  #@ security:code_exec +2\nc = 3\n"
    clean, expected = strip_markers("c1", "app/x.py", source)
    assert "#@" not in clean
    assert clean.splitlines()[1] == "b = eval(x)"
    assert expected == [Expected("c1", "security", "code_exec", "app/x.py", 2, 4)]


def test_new_file_diff_line_numbers_match_the_file():
    diff = new_file_diff("app/x.py", "uno\ndos\ntres\n")
    parsed = parse_diff(diff)
    assert parsed[0].path == "app/x.py"
    assert parsed[0].added_lines == {1: "uno", 2: "dos", 3: "tres"}


# --- puntuación --------------------------------------------------------------------------------

EXP = [Expected("c", "security", "sqli", "app/a.py", 10, 10)]


def test_exact_hit_is_a_true_positive():
    pred = [Predicted("security", "app/a.py", 10, "SQLi")]
    counts = score_case(pred, EXP, agent="security", strict=True)
    assert (counts.tp, counts.fp, counts.fn) == (1, 0, 0)


def test_line_within_tolerance_counts_but_far_line_does_not():
    near = [Predicted("security", "app/a.py", 11)]
    far = [Predicted("security", "app/a.py", 30)]
    assert score_case(near, EXP, agent="security", strict=True).tp == 1
    strict = score_case(far, EXP, agent="security", strict=True)
    assert (strict.tp, strict.fp, strict.fn) == (0, 1, 1)


def test_lenient_mode_forgives_the_line():
    far = [Predicted("security", "app/a.py", 30)]
    assert score_case(far, EXP, agent="security", strict=False).tp == 1


def test_finding_without_a_line_fails_strict_but_passes_lenient():
    pred = [Predicted("security", "app/a.py", None)]
    assert score_case(pred, EXP, agent="security", strict=True).fn == 1
    assert score_case(pred, EXP, agent="security", strict=False).tp == 1


def test_a_label_matches_at_most_one_prediction():
    pred = [Predicted("security", "app/a.py", 10), Predicted("security", "app/a.py", 10)]
    counts = score_case(pred, EXP, agent="security", strict=True)
    assert (counts.tp, counts.fp) == (1, 1)


def test_other_agents_findings_are_false_positives_for_their_own_agent():
    pred = [Predicted("smells", "app/a.py", 10)]
    smells = score_case(pred, EXP, agent="smells", strict=True)
    assert (smells.tp, smells.fp, smells.fn) == (0, 1, 0)
    # En el informe final no importa quién lo dijo.
    final = score_case(pred, EXP, agent=None, strict=True)
    assert (final.tp, final.fp) == (1, 0)


def test_deterministic_no_tests_warning_is_not_scored():
    pred = [Predicted("tests", "app/a.py", None, "Código modificado sin tests")]
    counts = score_case(pred, [], agent="tests", strict=True)
    assert (counts.tp, counts.fp, counts.fn) == (0, 0, 0)


def test_precision_recall_f1():
    counts = Counts(tp=3, fp=1, fn=2)
    assert counts.precision == 0.75
    assert counts.recall == 0.6
    assert round(counts.f1, 4) == round(2 * 0.75 * 0.6 / (0.75 + 0.6), 4)


def test_metrics_are_undefined_when_there_is_nothing_to_measure():
    empty = Counts()
    assert empty.precision is None and empty.recall is None and empty.f1 is None


def test_summary_counts_clean_cases_with_false_positives():
    results = [
        ([Predicted("security", "app/a.py", 3, "algo")], [], "clean"),
        ([], [], "clean"),
        ([Predicted("security", "app/a.py", 10)], EXP, "security"),
    ]
    summary = summarize(results)
    assert summary.clean_cases == 2
    assert summary.clean_cases_with_false_positive == 1
    assert summary.per_agent["security"]["strict"].tp == 1
