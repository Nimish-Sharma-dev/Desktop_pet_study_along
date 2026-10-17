from analysis.analyzer import Analyzer, test_results_to_findings, load_lesson
from analysis.model import Finding

LESSON = {"id": "demo", "concepts": ["array_indexing"], "common_mistakes": [
    {"id": "boundary_off_by_one", "concepts": ["array_indexing", "loop_invariants"], "signals": ["rule:loop_bound_off_by_one", "error:IndexError"], "seed_questions": []},
    {"id": "loops_forever", "concepts": ["loop_invariants"], "signals": ["error:Timeout"], "seed_questions": []},
    {"id": "empty_input", "concepts": ["edge_cases"], "signals": ["test:test_hidden_empty*", "diag:undefined_name"], "seed_questions": []}]}
BUG = "def f(nums):\n    t = 0\n    for i in range(len(nums) + 1):\n        t += nums[i]\n    return t\n"
NESTED = "def f(a):\n    for i in a:\n        for j in a:\n            pass\n"


def ev(code, ts=1, typ="edit", file="solution.py"):
    return {"type": typ, "ts": ts, "file": file, "language": "python", "content": code, "student_id": "s"}


def test_contract3_shape_and_lesson_mapping():
    (f,) = Analyzer().analyze([ev(BUG)], LESSON)
    d = f.to_dict()
    assert set(d) == {"kind", "mistake_id", "concept_ids", "file", "line", "evidence", "confidence", "lesson_id"}
    assert (d["kind"], d["mistake_id"], d["line"], d["lesson_id"]) == ("pattern", "boundary_off_by_one", 3, "demo")
    assert d["concept_ids"] == ["array_indexing", "loop_invariants"] and 0 <= d["confidence"] <= 1


def test_lesson_gates_rules_so_correct_nested_loops_are_not_reported():
    assert Analyzer().analyze([ev(NESTED)], LESSON) == []                 # lesson does not list nested_loop_quadratic
    assert [f.mistake_id for f in Analyzer().analyze([ev(NESTED)])] == ["avoidable_nested_loops"]   # no lesson: defaults


def test_dedupe_until_the_code_changes():
    a = Analyzer()
    assert len(a.analyze([ev(BUG)], LESSON)) == 1
    assert a.analyze([ev(BUG, ts=2)], LESSON) == []
    changed = BUG.replace("range(len(nums) + 1)", "range(0, len(nums) + 1)")      # the flagged loop itself changed
    assert len(a.analyze([ev(changed, ts=3)], LESSON)) == 1
    a2 = Analyzer(dedupe=False)
    assert len(a2.analyze([ev(BUG)], LESSON)) == 1 and len(a2.analyze([ev(BUG)], LESSON)) == 1


def test_only_latest_buffer_per_file_is_analyzed_and_events_are_sorted_by_ts():
    fixed = BUG.replace(" + 1", "")
    out = Analyzer().analyze([ev(fixed, ts=5), ev(BUG, ts=1)], LESSON)       # bug first, then the fix wins
    assert out == []


def test_unknown_language_is_ignored():
    assert Analyzer().analyze([{"type": "edit", "ts": 1, "file": "notes.txt", "content": "hello", "student_id": "s"}]) == []


def test_diagnostics_become_findings_with_lesson_override():
    batch = [{"type": "diagnostics", "ts": 1, "file": "a.py", "student_id": "s",
              "diagnostics": [{"line": 4, "severity": "error", "message": "NameError: name 'x' is not defined"},
                              {"line": 9, "severity": "warning", "message": "unused variable"}]}]
    (f,) = Analyzer().analyze(batch, LESSON)
    assert (f.kind, f.mistake_id, f.line) == ("diagnostic", "empty_input", 4)
    (g,) = Analyzer().analyze(batch)
    assert g.mistake_id == "undefined_name" and g.concept_ids == ["reading_error_messages"]


def test_test_results_to_findings_groups_by_mistake_and_never_leaks_hidden_expectations():
    result = {"lesson_id": "demo", "language": "python", "duration_ms": 5, "results": [
        {"name": "test_basic", "passed": True, "expected": None, "actual": None, "error_type": None, "message": ""},
        {"name": "test_hidden_empty", "passed": False, "expected": None, "actual": None, "error_type": "IndexError", "message": "x at solution.py:7", "hidden": True},
        {"name": "test_hidden_empty_two", "passed": False, "expected": None, "actual": None, "error_type": "WrongAnswer", "message": "", "hidden": True},
        {"name": "test_loop", "passed": False, "expected": None, "actual": None, "error_type": "Timeout", "message": "did not finish"},
        {"name": "test_visible", "passed": False, "expected": "3", "actual": "4", "error_type": "WrongAnswer", "message": ""}]}
    fs = {f.mistake_id: f for f in test_results_to_findings(result, LESSON, "solution.py")}
    # IndexError crash -> error:IndexError signal wins over the test-name glob; the plain wrong answer uses its test name
    assert set(fs) == {"boundary_off_by_one", "empty_input", "loops_forever", "failing_test"}
    assert fs["boundary_off_by_one"].evidence.startswith("hidden edge-case test") and fs["boundary_off_by_one"].line == 7
    assert fs["empty_input"].evidence == "hidden edge-case test `test_hidden_empty_two` failed (WrongAnswer)"
    assert fs["loops_forever"].line == 0
    assert fs["failing_test"].evidence == "test_visible: expected 3, got 4"
    assert all(f.kind == "test_failure" for f in fs.values())
    assert "expected" not in fs["boundary_off_by_one"].evidence.replace("edge-case", "")


def test_loads_real_lesson_by_id():
    assert load_lesson("binary-search")["track"] == "dsa"
