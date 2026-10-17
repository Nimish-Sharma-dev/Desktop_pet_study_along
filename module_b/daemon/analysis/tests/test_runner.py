"""End-to-end run_tests() through the real sandbox (python adapter; go/java/js run in verify_lessons.py)."""
import json
from pathlib import Path

import pytest
from analysis import run_tests, test_results_to_findings
from analysis.runners import RunnerError, get_adapter, ADAPTERS

ROOT = Path(__file__).resolve().parents[3] / "lessons"
REF = (ROOT / "binary-search" / "reference" / "solution.py").read_text()
CONTRACT2 = {"lesson_id", "language", "duration_ms", "results"}


@pytest.fixture
def ws(tmp_path):
    return tmp_path


def run(ws, code, lesson="binary-search"):
    (ws / "solution.py").write_text(code)
    return run_tests(lesson, "python", ws)


def by_name(r):
    return {x["name"]: x for x in r["results"]}


def test_reference_passes_everything_and_matches_contract_2(ws):
    r = run(ws, REF)
    assert set(r) == CONTRACT2 and r["lesson_id"] == "binary-search" and r["language"] == "python"
    assert len(r["results"]) == 11 and all(x["passed"] for x in r["results"])
    assert {"name", "passed", "expected", "actual", "error_type", "message"} <= set(r["results"][0])
    assert r["results"][0]["name"] == "test_found_middle" and r["duration_ms"] > 0


def test_wrong_answer_reports_expected_actual_for_visible_tests(ws):
    r = by_name(run(ws, REF.replace("return mid", "return mid + 1")))
    t = r["test_found_middle"]
    assert not t["passed"] and (t["expected"], t["actual"], t["error_type"]) == ("2", "3", "WrongAnswer")


def test_hidden_tests_run_but_never_reveal_expected_values(ws):
    r = by_name(run(ws, REF.replace("lo <= hi", "lo < hi")))
    h = r["test_hidden_single_found"]
    assert h["hidden"] and not h["passed"] and h["expected"] is None and h["actual"] is None
    assert "hidden edge-case test failed" in h["message"] and "0" not in h["message"].replace("hidden", "")
    assert not by_name(r and run(ws, REF))["test_found_middle"]["hidden"]


def test_index_error_is_classified_and_has_a_line_number(ws):
    r = by_name(run(ws, REF.replace("hi = len(nums) - 1", "hi = len(nums)")))
    t = r["test_not_found_above"]
    assert t["error_type"] == "IndexError" and "solution.py:6" in t["message"]


def test_infinite_loop_in_one_case_times_out_only_that_case(ws):
    code = REF.replace("    lo = 0\n", "    if not nums:\n        while True:\n            pass\n    lo = 0\n")
    r = by_name(run(ws, code))
    assert r["test_hidden_empty"]["error_type"] == "Timeout"
    assert sum(1 for x in r.values() if x["passed"]) == 10


def test_infinite_loop_in_every_case_does_not_hang_the_runner(ws):
    import time
    t0 = time.time()
    r = run(ws, "def binary_search(nums, target):\n    while True:\n        pass\n", )
    assert time.time() - t0 < 120
    assert len(r["results"]) == 11 and all(x["error_type"] == "Timeout" for x in r["results"])


def test_unbounded_recursion_is_reported_as_recursion_error(ws):
    r = run(ws, "def fib(n):\n    return fib(n - 1)\n\ndef sum_digits(n):\n    return sum_digits(n // 10)\n", "recursion-basics")
    assert {x["error_type"] for x in r["results"]} == {"RecursionError"}


def test_syntax_error_is_a_compile_error_for_every_test(ws):
    r = run(ws, "def binary_search(nums, target:\n    return 1\n")
    assert all(x["error_type"] == "CompileError" and not x["passed"] for x in r["results"])


def test_missing_function_is_reported_not_crashed(ws):
    r = run(ws, "x = 1\n")
    assert len(r["results"]) == 11 and not any(x["passed"] for x in r["results"])


def test_tests_are_never_written_to_the_student_workspace(ws):
    code = REF + "\nimport glob, os\nLEAK = glob.glob('test_hidden*')\n" \
                 "def binary_search(nums, target, _o=binary_search):\n    return -7 if os.path.exists('/root') else _o(nums, target)\n"
    r = run(ws, code)                   # hidden tests ARE in the sandbox cwd, but the student file never ships them out
    assert (ws / "solution.py").exists() and not list(ws.glob("test_*")), "tests must never be written to the student workspace"


def test_missing_solution_and_unknown_lesson_raise_runner_error(ws):
    with pytest.raises(RunnerError):
        run_tests("binary-search", "python", ws)
    with pytest.raises(RunnerError):
        run_tests("no-such-lesson", "python", ws)
    with pytest.raises(RunnerError):
        get_adapter("brainfuck")


def test_solution_is_found_in_nested_workspace_folder(ws):
    (ws / "src" / "binary-search").mkdir(parents=True)
    (ws / "src" / "binary-search" / "solution.py").write_text(REF)
    assert all(x["passed"] for x in run_tests("binary-search", "python", ws)["results"])


def test_results_feed_findings_and_the_tutor_gets_a_mapped_mistake(ws):
    r = run(ws, REF.replace("hi = len(nums) - 1", "hi = len(nums)"))
    fs = test_results_to_findings(r, "binary-search", "solution.py")
    assert fs[0].kind == "test_failure" and fs[0].mistake_id == "boundary_off_by_one" and fs[0].line == 6
    json.dumps([f.to_dict() for f in fs])


def test_every_adapter_declares_a_solution_file_and_all_nine_languages_are_registered():
    assert {"python", "javascript", "typescript", "go", "java", "cpp", "rust", "c_sharp", "kotlin"} <= set(ADAPTERS)
    for lang, cls in ADAPTERS.items():
        a = cls()
        assert a.solution_files and a.framework


def test_cpp_adapter_end_to_end_with_googletest(tmp_path):
    a = get_adapter("cpp")
    if a.available():
        pytest.skip(a.available())
    import shutil, subprocess
    if subprocess.run(["bash", "-c", "echo '#include <gtest/gtest.h>' | g++ -x c++ -fsyntax-only -"], capture_output=True).returncode:
        pytest.skip("GoogleTest headers not installed")
    lroot = tmp_path / "lessons"
    (lroot / "demo" / "tests" / "cpp" / "visible").mkdir(parents=True)
    (lroot / "demo" / "tests" / "cpp" / "hidden").mkdir(parents=True)
    (lroot / "demo" / "lesson.yaml").write_text("id: demo\n")
    (lroot / "demo" / "cases.yaml").write_text("functions:\n - name: add\n   cases:\n   - {name: adds}\n   - {name: hidden_big, hidden: true}\n")
    (lroot / "demo" / "tests" / "cpp" / "visible" / "a_test.cpp").write_text(
        'TEST(V, adds) { EXPECT_EQ(add(2, 3), 5); }\n')
    (lroot / "demo" / "tests" / "cpp" / "hidden" / "h_test.cpp").write_text(
        'TEST(H, hidden_big) { EXPECT_EQ(add(1000000, 1), 1000001); }\n')
    ws = tmp_path / "ws"; ws.mkdir()
    import os
    os.environ["LESSONS_DIR"] = str(lroot)
    try:
        (ws / "solution.cpp").write_text("int add(int a, int b) { return a + b; }\n")
        good = run_tests("demo", "cpp", ws)
        assert [x["passed"] for x in good["results"]] == [True, True]
        (ws / "solution.cpp").write_text("int add(int a, int b) { return a - b; }\n")
        assert not any(x["passed"] for x in run_tests("demo", "cpp", ws)["results"])
        (ws / "solution.cpp").write_text("int add(int a, int b) { return a +; }\n")
        assert all(x["error_type"] == "CompileError" for x in run_tests("demo", "cpp", ws)["results"])
    finally:
        os.environ.pop("LESSONS_DIR")
