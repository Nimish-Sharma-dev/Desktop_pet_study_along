#!/usr/bin/env python3
"""Module B demo: python -m analysis.demo   (run from /daemon)   [--write-mocks]

Walks the whole pipeline on the binary-search and url-shortener lessons:
  1 static analysis of a buggy buffer  -> Contract 3 finding
  2 guess-spam detection               -> Contract 3 finding (kind=guess_spam)
  3 sandboxed tests (visible+hidden)   -> Contract 2 result -> findings
  4 an infinite loop is contained
  5 system-design rubric               -> radar scores + rubric-gap findings
  6 root weak concept -> micro-lesson
"""
import json
import sys
import tempfile
from pathlib import Path

from analysis import Analyzer, run_tests, test_results_to_findings, score_design
from analysis.microlesson import root_weak_concept, generate_micro_lesson
from analysis.analyzer import lessons_root

L = lessons_root()
REF = (L / "binary-search" / "reference" / "solution.py").read_text()
BUG = REF.replace("hi = len(nums) - 1", "hi = len(nums)")
MOCKS = Path(__file__).resolve().parents[2] / "docs" / "mocks"
WRITE = "--write-mocks" in sys.argv
out = {}


def show(title, obj):
    print(f"\n=== {title}")
    print(json.dumps(obj, indent=2, default=str)[:1800])


def edit(code, ts, cursor=None):
    return {"type": "edit", "ts": ts, "file": "solution.py", "language": "python", "content": code,
            "cursor": cursor or {"line": 3, "col": 1}, "selection": None, "student_id": "local-user"}


# 1 -------------------------------------------------------------------------------------------
a = Analyzer()
f = [x.to_dict() for x in a.analyze([edit(BUG, 1)], "binary-search")]
show("1. static analysis (Contract 3)", f)
out["findings_static.json"] = f

# 2 -------------------------------------------------------------------------------------------
a = Analyzer()
names = [("hi", "high"), ("lo", "low"), ("mid", "m")]
code, spam = REF, []
import re
for i, (old, new) in enumerate([(None, None)] + names, 1):
    if old:
        code = re.sub(rf"\b{old}\b", new, code)
    spam += [x.to_dict() for x in a.analyze([edit(code, i)], "binary-search") if x.kind == "guess_spam"]
show("2. guess-spam after 3 rename-only edits (Contract 3)", spam)
out["findings_guess_spam.json"] = spam

# 3 -------------------------------------------------------------------------------------------
ws = Path(tempfile.mkdtemp())
(ws / "solution.py").write_text(BUG)
res = run_tests("binary-search", "python", ws)
show("3. test result (Contract 2) - hidden tests redacted", {**res, "results": res["results"][:5]})
fs = [x.to_dict() for x in test_results_to_findings(res, "binary-search", "solution.py")]
show("3b. -> findings", fs)
out["test_result.json"] = res
out["findings_test_failure.json"] = fs

# 4 -------------------------------------------------------------------------------------------
(ws / "solution.py").write_text("def binary_search(nums, target):\n    while True:\n        pass\n")
r = run_tests("binary-search", "python", ws)
print("\n=== 4. while True contained:", {x["error_type"] for x in r["results"]}, f"in {r['duration_ms']} ms")

# 5 -------------------------------------------------------------------------------------------
sd = score_design(L / "url-shortener" / "starter" / "design.md", "url-shortener")
show("5. rubric score of an empty design (radar + gaps)", {k: sd[k] for k in ("axes", "radar", "total", "passed", "diagram")})
good = score_design(L / "url-shortener" / "reference" / "design.md", "url-shortener")
print("   reference design:", good["total"], "/", good["max"], "passed =", good["passed"])
out["rubric_score_starter.json"], out["rubric_score_reference.json"] = sd, good

# 6 -------------------------------------------------------------------------------------------
root = root_weak_concept("dp", {"recursion": 0.2, "base_cases": 0.3, "memoization": 0.4})
d = generate_micro_lesson(root, Path(tempfile.mkdtemp()) / f"micro-{root}")
print(f"\n=== 6. root weak concept of dp = {root!r}; micro-lesson generated: {sorted(p.name for p in d.rglob('*') if p.is_file())}")

if WRITE:
    MOCKS.mkdir(parents=True, exist_ok=True)
    for name, obj in out.items():
        (MOCKS / ("b_" + name)).write_text(json.dumps(obj, indent=2) + "\n")
    print("\nwrote", len(out), "mock files to", MOCKS)
