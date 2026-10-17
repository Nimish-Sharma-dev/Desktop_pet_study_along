"""STUB for B's analysis module. Same interface; language-agnostic heuristics only.
Switch to the real one with `mock.analysis: false` in config.yaml."""
import itertools
import re

ALWAYS_EMIT = True  # emit a canned finding on every batch so the UI always gets a bubble
_CANNED = [
    ("loop_invariants", ["loop_invariants"], "stub: no real analysis yet"),
    ("boundary_off_by_one", ["array_indexing"], "stub: checking boundaries"),
    ("complexity_blindspot", ["time_complexity"], "stub: nested loops noticed"),
    ("missing_base_case", ["recursion"], "stub: no base case seen"),
]
_n = itertools.count()
_OFF_BY_ONE = re.compile(r"<=\s*(len\s*\(|\w+\.length|\w+\.size\s*\(|\bn\b|\bsize\b)")


def _f(kind, mid, concepts, file, line, evidence, conf, lesson):
    return {"kind": kind, "mistake_id": mid, "concept_ids": concepts, "file": file, "line": line,
            "evidence": evidence, "confidence": conf, "lesson_id": (lesson or {}).get("id", "demo")}


def analyze(event_batch, lesson):
    file = next((e["file"] for e in reversed(event_batch) if e.get("file")), "")
    test_ev = next((e for e in reversed(event_batch) if e["type"] == "test_run" and e.get("test_result")), None)
    if test_ev:
        out = []
        for r in test_ev["test_result"].get("results", []):
            if not r.get("passed"):
                boundary = any(k in r["name"] for k in ("single", "empty", "boundary"))
                out.append(_f("test_failure", "boundary_off_by_one" if boundary else "wrong_output",
                              ["array_indexing"] if boundary else ["correctness"], file, 1,
                              f"{r['name']}: expected {r.get('expected')}, got {r.get('actual')}", 0.9, lesson))
        return out
    diag_ev = next((e for e in reversed(event_batch) if e["type"] == "diagnostics"), None)
    errors = [d for d in (diag_ev or {}).get("diagnostics", []) if d.get("severity") == "error"]
    if errors:
        return [_f("diagnostic", "syntax_error", ["syntax"], file, errors[0].get("line", 1), errors[0]["message"], 0.8, lesson)]
    edit = next((e for e in reversed(event_batch) if e.get("content")), None)
    if edit:
        for i, line in enumerate(edit["content"].splitlines(), 1):
            if _OFF_BY_ONE.search(line):
                return [_f("pattern", "boundary_off_by_one", ["array_indexing"], file, i,
                           "loop bound uses <= with a length", 0.6, lesson)]
    if ALWAYS_EMIT and edit:
        mid, concepts, ev = _CANNED[next(_n) % len(_CANNED)]
        return [_f("pattern", mid, concepts, file, 1, ev, 0.3, lesson)]
    return []


_runs = itertools.count(1)


def run_tests(lesson_id, language, workspace):
    """Fails the single-element test on runs 1-2, passes everything on every 3rd run (to demo confetti)."""
    ok = next(_runs) % 3 == 0
    return {"lesson_id": lesson_id, "language": language, "duration_ms": 120, "results": [
        {"name": "test_empty_list", "passed": True, "expected": "-1", "actual": "-1", "error_type": None, "message": ""},
        {"name": "test_found_middle", "passed": True, "expected": "2", "actual": "2", "error_type": None, "message": ""},
        {"name": "test_single_element", "passed": ok, "expected": "0",
         "actual": "0" if ok else "IndexError", "error_type": None if ok else "IndexError",
         "message": "" if ok else "list index out of range"},
    ]}
