#!/usr/bin/env python3
"""Acceptance check for lesson packs.
  * reference solution passes every visible+hidden test, with no static findings (no false positives)
  * starter fails every test
  * each seeded bug fails >=1 test; bugs marked `static:` yield that mistake_id from analyze() in EVERY language
Usage: verify_lessons.py [lesson-id ...] [--lang python,go]
"""
import sys, tempfile, shutil
from pathlib import Path
import yaml
HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "daemon"))
from analysis import run_tests
from analysis.analyzer import Analyzer
from analysis.parser import detect_language

ROOT = HERE.parents[1]
SOL = {"python": "solution.py", "javascript": "solution.js", "go": "solution.go", "java": "Solution.java"}


def apply_bug(ref_text: str, bug: dict, lang: str):
    if lang in (bug.get("full") or {}):
        return bug["full"][lang]
    patches = (bug.get("patches") or {}).get(lang)
    if patches is None:
        return None
    t = ref_text
    for p in patches:
        assert t.count(p["old"]) == 1, f"patch {p['old']!r} matches {t.count(p['old'])}x in {lang}"
        t = t.replace(p["old"], p["new"])
    return t


def run_variant(lesson_id, lang, text):
    ws = Path(tempfile.mkdtemp(prefix="ws-"))
    try:
        (ws / SOL[lang]).write_text(text)
        return run_tests(lesson_id, lang, ws)
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def static_ids(lesson, lang, text):
    a = Analyzer(dedupe=False)
    ev = [{"type": "edit", "ts": 1, "file": SOL[lang], "language": lang, "content": text, "student_id": "t"}]
    return [(f.mistake_id, f.line) for f in a.analyze(ev, lesson) if f.kind == "pattern"]


def verify(lesson_id, langs=None, log=print):
    d = ROOT / lesson_id
    lesson = yaml.safe_load((d / "lesson.yaml").read_text())
    bugs = (yaml.safe_load((d / "seeded_bugs.yaml").read_text()) or {}).get("bugs", []) if (d / "seeded_bugs.yaml").exists() else []
    problems, static_seen = [], {}
    for lang in langs or lesson["languages"]:
        ref = (d / "reference" / SOL[lang]).read_text()
        r = run_variant(lesson_id, lang, ref)
        bad = [x["name"] for x in r["results"] if not x["passed"]]
        n = len(r["results"])
        log(f"  [{lang:10}] reference: {n - len(bad)}/{n} pass ({r['duration_ms']} ms)")
        if bad: problems.append(f"{lesson_id}/{lang}: reference fails {bad}")
        fp = static_ids(lesson, lang, ref)
        if fp: problems.append(f"{lesson_id}/{lang}: static false positive on reference {fp}")
        st = (d / "starter" / SOL[lang]).read_text()
        r = run_variant(lesson_id, lang, st)
        ok = [x["name"] for x in r["results"] if x["passed"]]
        if ok: problems.append(f"{lesson_id}/{lang}: starter passes {ok}")
        for b in bugs:
            text = apply_bug(ref, b, lang)
            if text is None: continue
            r = run_variant(lesson_id, lang, text)
            failed = [x for x in r["results"] if not x["passed"]]
            tag = ""
            if not failed and lang not in b.get("static_only", []): problems.append(f"{lesson_id}/{lang}: seeded bug {b['id']} is NOT caught by tests")
            if b.get("static"):
                ids = [m for m, _ in static_ids(lesson, lang, text)]
                static_seen.setdefault(b["id"], {})[lang] = ids
                if b["static"] not in ids: problems.append(f"{lesson_id}/{lang}: bug {b['id']} expected static {b['static']}, got {ids}")
                tag = f" static={ids}"
            log(f"  [{lang:10}] bug {b['id']:28} fails {len(failed)}/{len(r['results'])} tests{tag}")
    return problems


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    langs = None
    for a in sys.argv[1:]:
        if a.startswith("--lang"): langs = a.split("=", 1)[1].split(",")
    allp = []
    for d in sorted(ROOT.iterdir()):
        if (d / "cases.yaml").exists() and (not args or d.name in args):
            print(d.name); allp += verify(d.name, langs)
    print("\nPROBLEMS:" if allp else "\nALL LESSONS OK")
    for p in allp: print(" -", p)
    sys.exit(1 if allp else 0)
