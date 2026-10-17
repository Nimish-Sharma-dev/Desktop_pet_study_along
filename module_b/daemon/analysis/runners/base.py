"""analysis.run_tests(lesson_id, language, workspace) -> TestResult   (Contract 2)

Flow
 1. Locate the student's solution file in `workspace` (never modified, never given the tests).
 2. Assemble a throw-away work dir: student file + lesson tests (visible AND hidden) + support kit.
 3. Run build steps then the test step inside the sandbox.
 4. Parse the framework's native output -> common result format.
 5. Anything that did not report (infinite loop, crash, stack overflow in a compiled language) is
    re-run in isolation (one process per case) so one hanging case cannot hide the others;
    cases that still do not finish are reported as Timeout / Crash.

Infrastructure problems (unknown lesson, missing toolchain, missing solution file) raise
RunnerError - they are not the student's fault and must not become "mistakes".
"""
from __future__ import annotations
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..analyzer import lessons_root
from ..sandbox import Limits, Sandbox, cleanup, make_workdir


class RunnerError(RuntimeError):
    pass


@dataclass
class Step:
    cmd: list
    kind: str = "test"                 # "build" | "test"
    env: dict = field(default_factory=dict)
    data_mb: int | None = None
    wall_s: float = 30.0


class Adapter:
    language = ""
    framework = ""
    solution_files: list = []
    isolate = False                    # re-run unreported cases one process at a time
    rerun_timeouts = False             # also re-run cases that reported Timeout (needed where hung cases leak spinning threads: go/java)
    data_mb = 768

    # -- environment ----------------------------------------------------------------
    def available(self) -> str | None:
        """Return a human message if a required tool is missing, else None."""
        return None

    # -- workdir ----------------------------------------------------------------------
    def prepare(self, lesson_dir: Path, solution: Path, workdir: Path):
        support = lessons_root() / "_support" / self.language
        if support.exists():
            for f in support.iterdir():
                if f.is_file():
                    shutil.copy2(f, workdir / f.name)
        for sub in ("visible", "hidden"):
            d = lesson_dir / "tests" / self.language / sub
            if d.exists():
                for f in d.iterdir():
                    if f.is_file():
                        shutil.copy2(f, workdir / f.name)
        shutil.copy2(solution, workdir / solution.name)       # last: tests can never be shadowed

    # -- commands ---------------------------------------------------------------------
    def build_steps(self, workdir: Path) -> list:
        return []

    def test_step(self, workdir: Path, only: str | None = None) -> Step:
        raise NotImplementedError

    def parse(self, workdir: Path, res) -> list:
        raise NotImplementedError

    def canonical(self, native: str) -> str:
        return canonical_name(native)


def canonical_name(native: str) -> str:
    n = re.split(r"::|\.", native.strip())[-1] if not native.startswith("test_") else native
    n = n.replace("()", "").strip()
    return re.sub(r"^(test_|Test_)", "", n)


_ERR_MAP = [
    (r"IndexError|ArrayIndexOutOfBounds|IndexOutOfBounds|index out of range|out of bounds|StringIndexOutOfBounds", "IndexError"),
    (r"NullPointer|NoneType|nil pointer|null reference|NullReference|Cannot read propert|undefined is not|is not a function|of null|of undefined", "NullReference"),
    (r"RecursionError|StackOverflow|Maximum call stack|stack overflow|goroutine stack exceeds", "RecursionError"),
    (r"Timeout|timed out|TimeoutException", "Timeout"),
    (r"MemoryError|OutOfMemory|out of memory", "MemoryError"),
]


def normalize_error(text: str | None) -> str:
    t = text or ""
    for rx, name in _ERR_MAP:
        if re.search(rx, t):
            return name
    return ""


def load_cases(lesson_dir: Path) -> dict:
    """canonical case name -> {'hidden': bool}   (from cases.yaml, the single source of truth)"""
    f = lesson_dir / "cases.yaml"
    out = {}
    if f.exists():
        data = yaml.safe_load(f.read_text())
        for fn in data.get("functions", []):
            for c in fn.get("cases", []):
                out[c["name"]] = {"hidden": bool(c.get("hidden"))}
    return out


def find_solution(workspace: Path, lesson_id: str, names: list) -> Path:
    workspace = Path(workspace)
    for n in names:
        for cand in (workspace / lesson_id / n, workspace / n):
            if cand.is_file():
                return cand
    for n in names:
        found = sorted((p for p in workspace.rglob(n) if p.is_file() and "node_modules" not in p.parts),
                       key=lambda p: len(p.parts))
        if found:
            return found[0]
    raise RunnerError(f"solution file {names[0]!r} not found in {workspace}")


_COMPILE_RX = re.compile(r"error:|error\[E|error TS|cannot find symbol|undefined:|syntax error|SyntaxError|"
                         r"\.go:\d+:\d+:|build failed|cannot be resolved|expected .* but found", re.I)


def _short(msg: str, n: int = 300) -> str:
    lines = [l for l in (msg or "").splitlines() if l.strip() and "LESSON_FAIL" not in l]
    return " | ".join(l.strip() for l in lines[:4])[:n]


def _fmt(v) -> str | None:
    return None if v is None else json.dumps(v, separators=(",", ":"), sort_keys=True)


def run_tests(lesson_id: str, language: str, workspace, sandbox: Sandbox | None = None) -> dict:
    from . import get_adapter
    t_start = time.monotonic()
    lesson_dir = lessons_root() / lesson_id
    if not (lesson_dir / "lesson.yaml").exists():
        raise RunnerError(f"unknown lesson {lesson_id!r}")
    adapter = get_adapter(language)
    problem = adapter.available()
    if problem:
        raise RunnerError(problem)
    solution = find_solution(Path(workspace), lesson_id, adapter.solution_files)
    cases = load_cases(lesson_dir)
    if not (lesson_dir / "tests" / language).exists():
        raise RunnerError(f"lesson {lesson_id!r} has no tests for language {language!r}")
    sandbox = sandbox or Sandbox()
    workdir = make_workdir()
    results: dict = {}                       # canonical -> final result dict
    sol_name = adapter.solution_files[0]

    def finish(canon, passed, raw=None, error_type=None, message=""):
        hidden = cases.get(canon, {}).get("hidden", canon.startswith("hidden_"))
        info = (raw or {}).get("info") or {}
        et = None
        if not passed:
            exc = (raw or {}).get("exception")
            et = (error_type or info.get("error_type") or normalize_error((raw or {}).get("message"))
                  or (exc and (normalize_error(exc) or exc)) or "WrongAnswer")
        line = info.get("line")
        msg = ""
        if not passed:
            if hidden:
                msg = f"hidden edge-case test failed ({et})"
            else:
                msg = message or info.get("detail") or _short((raw or {}).get("message", "")) or et
            if line:
                msg += f" at {sol_name}:{line}"
        results[canon] = {"name": f"test_{canon}", "passed": passed,
                          "expected": None if (passed or hidden) else _fmt(info.get("expected")),
                          "actual": None if (passed or hidden) else _fmt(info.get("actual")),
                          "error_type": et, "message": msg[:400], "hidden": hidden}

    try:
        adapter.prepare(lesson_dir, solution, workdir)
        run = lambda step: sandbox.run(step.cmd, workdir, adapter.language, step.env,
                                       Limits(wall_s=step.wall_s), step.data_mb or adapter.data_mb)
        # ---- build ----
        for step in adapter.build_steps(workdir):
            r = run(step)
            if r.returncode != 0 or r.timed_out:
                out = (r.stderr + "\n" + r.stdout).strip()
                for c in cases:
                    finish(c, False, error_type="CompileError", message=_short(out, 400) or "build failed")
                return _assemble(lesson_id, language, results, cases, t_start)
        # ---- test ----
        tstep = adapter.test_step(workdir)
        r = run(tstep)
        try:
            raw = adapter.parse(workdir, r)
        except Exception as e:                                    # unparsable output = crash, not a student mistake we can name
            raw = []
        suite_err = [x for x in raw if x.get("suite_error")]
        raw = [x for x in raw if not x.get("skipped") and not x.get("suite_error")]
        for x in raw:
            c = adapter.canonical(x["name"])
            finish(c, x["passed"], x)
        if not raw and (suite_err or _COMPILE_RX.search(r.stderr + r.stdout)) and not r.timed_out:
            out = (suite_err[0]["message"] if suite_err else (r.stderr + "\n" + r.stdout)).strip()
            for c in cases:
                finish(c, False, error_type="CompileError", message=_short(out, 400))
            return _assemble(lesson_id, language, results, cases, t_start)
        # ---- isolate hangs / crashes ----
        redo = [c for c in cases if c not in results or (adapter.rerun_timeouts and results[c]["error_type"] == "Timeout")]
        if redo and adapter.isolate:
            for c in redo:
                step = adapter.test_step(workdir, only=c)
                step.wall_s = min(step.wall_s, 8.0)
                ri = run(step)
                try:
                    rawi = [x for x in adapter.parse(workdir, ri) if adapter.canonical(x["name"]) == c]
                except Exception:
                    rawi = []
                if rawi:
                    finish(c, rawi[0]["passed"], rawi[0])
                elif ri.timed_out:
                    finish(c, False, error_type="Timeout", message="did not finish in time (possible infinite loop)")
                else:
                    finish(c, False, error_type="Crash", message=_short(ri.stderr or ri.stdout) or ri.reason or "crashed")
        for c in cases:
            if c not in results:
                if r.timed_out:
                    finish(c, False, error_type="Timeout", message="did not finish in time (possible infinite loop)")
                else:
                    finish(c, False, error_type="Crash", message=_short(r.stderr or r.stdout) or r.reason or "crashed")
    finally:
        cleanup(workdir)
    return _assemble(lesson_id, language, results, cases, t_start)


def _assemble(lesson_id, language, results: dict, cases: dict, t_start: float) -> dict:
    order = list(cases) + [c for c in results if c not in cases]
    return {"lesson_id": lesson_id, "language": language,
            "duration_ms": int((time.monotonic() - t_start) * 1000),
            "results": [results[c] for c in order if c in results]}
