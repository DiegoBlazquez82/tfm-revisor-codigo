"""Casos límite del parseo del diff (errores E1 y E2 de la revisión)."""

from revisor.diff import annotate_patch, parse_diff

# --- E1: la marca «\ No newline at end of file» no desplaza los números de línea ---------------

NO_NEWLINE = (
    "diff --git a/a.txt b/a.txt\n"
    "--- a/a.txt\n"
    "+++ b/a.txt\n"
    "@@ -1,2 +1,3 @@\n"
    "-viejo\n"
    "\\ No newline at end of file\n"
    "+nuevo\n"
    "\\ No newline at end of file\n"
    "+extra\n"
)


def test_no_newline_marker_does_not_shift_line_numbers():
    files = parse_diff(NO_NEWLINE)
    assert set(files[0].added_lines) == {1, 2}
    assert files[0].added_lines[2] == "extra"


def test_annotate_patch_ignores_the_no_newline_marker():
    annotated = annotate_patch(parse_diff(NO_NEWLINE)[0].patch)
    assert "L1: +nuevo" in annotated
    assert "L2: +extra" in annotated


# --- E2: una línea añadida que empieza por «++ » no es un fichero nuevo ------------------------

PLUS_PLUS = (
    "diff --git a/a.c b/a.c\n"
    "--- a/a.c\n"
    "+++ b/a.c\n"
    "@@ -1,1 +1,2 @@\n"
    " int x;\n"
    "+++ counter;\n"
)


def test_added_line_starting_with_plus_plus_is_not_a_new_file():
    files = parse_diff(PLUS_PLUS)
    assert [f.path for f in files] == ["a.c"]
    assert files[0].added_lines == {2: "++ counter;"}


def test_removed_line_looking_like_a_header_is_not_a_header():
    text = (
        "diff --git a/m.c b/m.c\n"
        "--- a/m.c\n"
        "+++ b/m.c\n"
        "@@ -1,2 +1,2 @@\n"
        "--- viejo\n"
        "+++ nuevo\n"
        " fin\n"
    )
    files = parse_diff(text)
    assert [f.path for f in files] == ["m.c"]
    assert files[0].added_lines == {1: "++ nuevo"}


def test_two_files_without_diff_git_lines_are_still_separated():
    text = (
        "--- a/x.py\n+++ b/x.py\n@@ -1,1 +1,2 @@\n a\n+b\n"
        "--- a/y.py\n+++ b/y.py\n@@ -1,1 +1,2 @@\n a\n+c\n"
    )
    assert [f.path for f in parse_diff(text)] == ["x.py", "y.py"]


def test_hunk_header_without_counts_means_one_line():
    text = "diff --git a/z b/z\n--- a/z\n+++ b/z\n@@ -1 +1 @@\n-a\n+b\n"
    assert parse_diff(text)[0].added_lines == {1: "b"}


def test_inconsistent_hunk_counts_do_not_swallow_the_next_file():
    text = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1,9 +1,9 @@\n+uno\n"
        "diff --git a/b.py b/b.py\n--- a/b.py\n+++ b/b.py\n@@ -1,1 +1,1 @@\n+dos\n"
    )
    assert [f.path for f in parse_diff(text)] == ["a.py", "b.py"]
