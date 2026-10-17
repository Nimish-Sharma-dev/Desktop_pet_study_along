"""Micro-lesson generation for a ROOT weak concept.

    root = root_weak_concept("dp", mastery)            # deepest prerequisite the student is weak at
    path = generate_micro_lesson(root)                  # lessons/micro-<root>/  (lesson.yaml, README, starter, tests)

`root_weak_concept` walks the REQUIRES graph from the concept the student keeps failing: a prerequisite is weak when
its mastery < threshold (concepts with no evidence get `default`, i.e. are NOT blamed). The answer is the weakest-ranked concept that has no weak
prerequisite of its own - fixing that unlocks the ones above it. If every prerequisite is fine, the concept itself.
"""
from __future__ import annotations
import importlib.util
import string
from pathlib import Path

import yaml

from .analyzer import lessons_root


def load_concepts(path: Path | None = None) -> dict:
    path = path or lessons_root() / "concepts.yaml"
    return yaml.safe_load(path.read_text())["concepts"]


def prerequisites(concept: str, concepts: dict | None = None) -> list:
    """All transitive prerequisites, nearest first."""
    c = concepts or load_concepts()
    out, queue = [], list(c[concept]["requires"])
    while queue:
        n = queue.pop(0)
        if n not in out:
            out.append(n)
            queue.extend(c[n]["requires"])
    return out


def root_weak_concept(concept: str, mastery: dict, threshold: float = 0.6, default: float = 0.75,
                      concepts: dict | None = None) -> str:
    c = concepts or load_concepts()
    if concept not in c:
        raise KeyError(f"unknown concept {concept!r}")
    weak = lambda n: mastery.get(n, default) < threshold
    candidates = [n for n in prerequisites(concept, c) if weak(n)]
    # the root = weak prerequisite none of whose own prerequisites are weak; prefer the one closest to `concept`
    roots = [n for n in candidates if not any(weak(m) for m in prerequisites(n, c))]
    if roots:
        return roots[0]
    return concept


def _gen_module():
    spec = importlib.util.spec_from_file_location("gen_lessons", lessons_root() / "_tools" / "gen_lessons.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def generate_micro_lesson(concept: str, out_dir: Path | None = None, needed_by: str | None = None) -> Path:
    c = load_concepts()
    info = c[concept]
    out = Path(out_dir) if out_dir else lessons_root() / f"micro-{concept}"
    out.mkdir(parents=True, exist_ok=True)
    tmpl_dir = lessons_root() / "_templates" / "micro-lesson"
    subs = {"concept": concept, "name": info["name"], "track": info["track"],
            "needed_by": needed_by or "the lesson you were working on"}
    lesson = yaml.safe_load(string.Template((tmpl_dir / "lesson.yaml.tmpl").read_text()).safe_substitute(subs))
    lesson["common_mistakes"][0]["seed_questions"] = list(info.get("questions") or
                                                          [f"In your own words, what is {info['name']}?"])
    drill = info.get("drill")
    if drill:
        task = f"**Task** - `{drill['function']}`: {drill['doc']}"
        cases = {"title": f"Micro-lesson: {info['name']}",
                 "functions": [{"name": drill["function"], "doc": drill["doc"], "params": drill["params"],
                                "returns": drill["returns"], "cases": drill["cases"]}]}
        (out / "cases.yaml").write_text(yaml.safe_dump(cases, sort_keys=False, width=200))
        (out / "reference").mkdir(exist_ok=True)
        (out / "reference" / "solution.py").write_text(drill["reference"])
        _gen_module().generate_lesson(out, langs=["python"])
    else:
        task = ("**Task** - no code drill exists for this concept yet. Talk it through with the pet: it will ask you "
                "the questions below and you answer in your own words.")
    (out / "lesson.yaml").write_text(yaml.safe_dump(lesson, sort_keys=False, width=200))
    subs["task"] = task
    (out / "README.md").write_text(string.Template((tmpl_dir / "README.md.tmpl").read_text()).safe_substitute(subs))
    return out
