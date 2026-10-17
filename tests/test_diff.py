from revisor.diff import is_source_file, is_test_file, parse_diff

SAMPLE = """diff --git a/app/db.py b/app/db.py
index 111..222 100644
--- a/app/db.py
+++ b/app/db.py
@@ -10,3 +10,5 @@ def connect():
     conn = make()
+    query = "SELECT * FROM users WHERE id = " + user_id
+    return conn.execute(query)
     return conn
diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-x = 1
-y = 2
"""


def test_parse_diff_tracks_added_line_numbers():
    files = parse_diff(SAMPLE)
    assert [f.path for f in files] == ["app/db.py"]
    assert set(files[0].added_lines) == {11, 12}
    assert "SELECT" in files[0].added_lines[11]


def test_deleted_files_are_ignored():
    assert all(f.path != "old.py" for f in parse_diff(SAMPLE))


def test_empty_diff():
    assert parse_diff("") == []


def test_file_classification():
    assert is_test_file("tests/test_db.py")
    assert is_test_file("src/app.spec.ts")
    assert not is_test_file("src/db.py")
    assert is_source_file("src/db.py")
    assert not is_source_file("README.md")
    assert not is_source_file("tests/test_db.py")
