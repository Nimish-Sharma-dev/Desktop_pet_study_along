"""analysis.analyze(event_batch, lesson) -> list[Finding]   (Contract 3)

Policy
------
* Static rules run on the LATEST buffer per file in the batch, and only when it parses
  cleanly (a half-typed line is not a bug).
* With a lesson: a rule only fires if some `common_mistakes[].signals` contains
  "rule:<rule_id>"; the finding then carries that mistake's id and concepts. This keeps
  nested loops from being reported in a BFS lesson where they are correct, and it is why the
  same logical bug gets the same mistake_id in Python, Java and Go.
* Without a lesson: every rule runs and uses its default mistake_id / concepts.
* Findings are de-duplicated per (student, file, mistake, line, flagged-code); a changed
  line is reported again, an unchanged one is not.
"""
from __future__ import annotations
import fnmatch
import os
import re
from pathlib import Path

import yaml

from . import rules as R
from .guess_spam import GuessSpamDetector
from .model import Finding
from .parser import detect_language, diagnostic_classes, parse

_LESSON_CACHE: dict = {}


def lessons_root() -> Path:
    return Path(os.environ.get("LESSONS_DIR") or Path(__file__).resolve().parents[2] / "lessons")


def load_lesson(lesson) -> dict | None:
    """Accepts a parsed dict, a path to lesson.yaml / lesson dir, or a lesson id."""
    if lesson is None or isinstance(lesson, dict):
        return lesson
    path = Path(str(lesson))
    if not path.exists():
        path = lessons_root() / str(lesson)
    if path.is_dir():
        path = path / "lesson.yaml"
    if not path.exists():
        return None
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _LESSON_CACHE:
        _LESSON_CACHE[key] = yaml.safe_load(path.read_text())
    return _LESSON_CACHE[key]


def _mistakes(lesson: dict | None) -> list:
    return (lesson or {}).get("common_mistakes", []) or []


def _mistake_for_signal(lesson: dict | None, signal: str):
    for cm in _mistakes(lesson):
        for s in cm.get("signals", []) or []:
            if s == signal or fnmatch.fnmatch(signal, s):
                return cm
    return None


class Analyzer:
    def __init__(self, dedupe: bool = True, guess_threshold: int = 3):
        self.dedupe = dedupe
        self.guess = GuessSpamDetector(threshold=guess_threshold)
        self._seen: set = set()

    def reset(self):
        self._seen.clear()
        self.guess.reset()

    # ------------------------------------------------------------------ main entry
    def analyze(self, event_batch: list, lesson=None) -> list:
        lesson = load_lesson(lesson)
        lesson_id = (lesson or {}).get("id")
        findings: list = []
        latest: dict = {}
        events = sorted(event_batch or [], key=lambda e: e.get("ts") or 0)
        for ev in events:
            typ = ev.get("type")
            student = ev.get("student_id", "local-user")
            file = ev.get("file") or ""
            if typ in ("edit", "focus", "file_open") and ev.get("content") is not None:
                lang = detect_language(file, ev.get("language"))
                if lang is None:
                    continue
                key = (student, file)
                latest[key] = (ev["content"], lang, ev)
                if typ == "edit":
                    sig = self.guess.observe(key, ev["content"], lang, (ev.get("cursor") or {}).get("line"))
                    if sig:
                        findings.append(Finding("guess_spam", "guess_and_check", ["debugging_by_tracing"],
                                                file, sig.line, sig.evidence, sig.confidence, lesson_id))
            elif typ == "diagnostics":
                findings += self._from_diagnostics(ev, lesson)
            elif typ == "test_run" and isinstance(ev.get("test_result"), dict):
                findings += test_results_to_findings(ev["test_result"], lesson, file or None)

        for (student, file), (content, lang, ev) in latest.items():
            findings += self._static(student, file, content, lang, lesson)
        findings = self._dedupe(findings, events)
        findings.sort(key=lambda f: -f.confidence)
        return findings

    # ------------------------------------------------------------------ static rules
    def _static(self, student, file, content, lang, lesson) -> list:
        p = parse(content, lang)
        if p.has_errors:
            return []
        out = []
        if lesson:
            allowed = {}
            for cm in _mistakes(lesson):
                for s in cm.get("signals", []) or []:
                    if s.startswith("rule:"):
                        allowed.setdefault(s[5:], cm)
            hits = R.run_rules(p, only=set(allowed))
        else:
            allowed = {}
            hits = R.run_rules(p)
        for h in hits:
            r = R.RULES[h.rule]
            cm = allowed.get(h.rule)
            mistake = cm["id"] if cm else r.default_mistake
            concepts = list(cm.get("concepts") or r.concepts) if cm else list(r.concepts)
            f = Finding("pattern", mistake, concepts, file, h.line, h.evidence, h.confidence,
                        (lesson or {}).get("id"))
            f._key = (student, file, mistake, h.line, h.key)       # type: ignore[attr-defined]
            out.append(f)
        return out

    # ------------------------------------------------------------------ diagnostics
    def _from_diagnostics(self, ev: dict, lesson) -> list:
        out, seen = [], set()
        classes = diagnostic_classes()
        for d in ev.get("diagnostics") or []:
            if (d.get("severity") or "error").lower() != "error":
                continue
            msg = (d.get("message") or "")
            low = msg.lower()
            cls = next((c for c, pats in classes.items() if any(x in low for x in pats)), "compiler_error")
            if cls in seen:
                continue
            seen.add(cls)
            cm = _mistake_for_signal(lesson, f"diag:{cls}")
            out.append(Finding("diagnostic", cm["id"] if cm else cls,
                               list(cm.get("concepts") or []) if cm else ["reading_error_messages"],
                               ev.get("file") or "", d.get("line") or 0, f"{cls}: {msg[:160]}", 0.9,
                               (lesson or {}).get("id")))
        return out

    # ------------------------------------------------------------------ misc
    def _dedupe(self, findings: list, events: list) -> list:
        if not self.dedupe:
            return findings
        out = []
        for f in findings:
            key = getattr(f, "_key", None)
            if key is None:
                out.append(f)
                continue
            if key in self._seen:
                continue
            self._seen.add(key)
            out.append(f)
        return out


# ---------------------------------------------------------------------- test results -> findings
_LINE_RX = re.compile(r"(?i)\bsolution\.(?:py|js|ts|go|rs|cpp|cc|c|cs|kt|java):(\d+)")


def test_results_to_findings(result: dict, lesson=None, file: str | None = None) -> list:
    """Contract 2 TestResult -> Contract 3 Findings (one per distinct mistake_id)."""
    lesson = load_lesson(lesson) or load_lesson(result.get("lesson_id"))
    lesson_id = (lesson or {}).get("id") or result.get("lesson_id")
    groups: dict = {}
    for r in result.get("results", []):
        if r.get("passed"):
            continue
        name = r.get("name", "")
        et0 = r.get("error_type") or "WrongAnswer"
        by_test, by_error = (_mistake_for_signal(lesson, f"test:{name}"), _mistake_for_signal(lesson, f"error:{et0}"))
        # a crash/timeout names its cause more precisely than the test that happened to trigger it;
        # for plain wrong answers the test name is the better evidence.
        cm = (by_error or by_test) if et0 != "WrongAnswer" else (by_test or by_error)
        mid = cm["id"] if cm else "failing_test"
        if cm:
            concepts = list(cm.get("concepts") or [])
        else:
            concepts = list((lesson or {}).get("concepts", []))[:2]
        et = r.get("error_type") or "WrongAnswer"
        if r.get("hidden"):
            ev = f"hidden edge-case test `{name}` failed ({et})"
        elif r.get("expected") is not None and r.get("actual") is not None and et == "WrongAnswer":
            ev = f"{name}: expected {r['expected']}, got {r['actual']}"
        else:
            detail = re.sub(rf"^{re.escape(et)}:?\s*", "", str(r.get("message") or "")).strip()
            ev = f"{name} raised {et}" + (f" ({detail[:100]})" if detail else "")
        m = _LINE_RX.search(r.get("message") or "")
        line = int(m.group(1)) if m else 0
        g = groups.setdefault(mid, {"concepts": concepts, "first": (ev, line), "n": 0})
        g["n"] += 1
    out = []
    for mid, g in groups.items():
        ev, line = g["first"]
        if g["n"] > 1:
            ev += f" (+{g['n'] - 1} more failing test{'s' if g['n'] > 2 else ''} with the same cause)"
        out.append(Finding("test_failure", mid, g["concepts"], file or "", line, ev,
                           0.95 if mid != "failing_test" else 0.9, lesson_id))
    return out


test_results_to_findings.__test__ = False      # name starts with test_: keep pytest from collecting it

_DEFAULT = Analyzer()


def analyze(event_batch: list, lesson=None) -> list:
    """Module-level convenience: shares one stateful Analyzer (guess-spam history, de-dupe)."""
    return _DEFAULT.analyze(event_batch, lesson)
