"""Fast, no-execution checks over every lesson pack: structure (Contract 6), concept graph, and the
acceptance rule 'same logical bug -> same mistake_id in every language'."""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3] / "lessons"
sys.path.insert(0, str(ROOT / "_tools"))
import verify_lessons as V          # noqa: E402

LESSONS = sorted(d.name for d in ROOT.iterdir() if (d / "lesson.yaml").exists() and not d.name.startswith("micro-"))
CODE = [l for l in LESSONS if (ROOT / l / "cases.yaml").exists()]
DESIGN = [l for l in LESSONS if (ROOT / l / "rubric.yaml").exists()]
CONCEPTS = yaml.safe_load((ROOT / "concepts.yaml").read_text())["concepts"]
SOL = V.SOL


def load(l):
    return yaml.safe_load((ROOT / l / "lesson.yaml").read_text())


def test_at_least_ten_lessons_including_two_system_design():
    assert len(LESSONS) >= 10 and len(DESIGN) >= 2 and len(CODE) >= 9
    for need in ("binary-search", "two-pointers", "sliding-window", "recursion-basics", "linked-list-reversal",
                 "graph-bfs-dfs", "dp-intro", "hash-maps", "stacks-queues", "url-shortener", "rate-limiter"):
        assert need in LESSONS


@pytest.mark.parametrize("lid", LESSONS)
def test_lesson_yaml_matches_contract_6(lid):
    l = load(lid)
    assert set(l) == {"id", "title", "track", "difficulty", "concepts", "prerequisites", "estimated_minutes",
                      "common_mistakes", "languages"}
    assert l["id"] == lid and l["track"] in ("dsa", "system_design") and isinstance(l["difficulty"], int)
    assert l["concepts"] and set(l["concepts"]) <= set(CONCEPTS)
    assert set(l["prerequisites"]) <= set(LESSONS)
    ids = [m["id"] for m in l["common_mistakes"]]
    assert len(ids) == len(set(ids)) and ids
    for m in l["common_mistakes"]:
        assert set(m) == {"id", "concepts", "signals", "seed_questions"}
        assert m["seed_questions"] and m["signals"] and set(m["concepts"]) <= set(CONCEPTS)
        assert all(s.split(":", 1)[0] in ("rule", "test", "error", "diag", "rubric") for s in m["signals"])
    assert (ROOT / lid / "README.md").read_text().strip()


@pytest.mark.parametrize("lid", CODE)
def test_code_lesson_files(lid):
    l, d = load(lid), ROOT / lid
    cases = yaml.safe_load((d / "cases.yaml").read_text())
    names = [c["name"] for f in cases["functions"] for c in f["cases"]]
    assert len(names) == len(set(names))
    assert any(c.get("hidden") for f in cases["functions"] for c in f["cases"]), "needs hidden edge-case tests"
    assert any(not c.get("hidden") for f in cases["functions"] for c in f["cases"])
    for lang in l["languages"]:
        assert "TODO" in (d / "starter" / SOL[lang]).read_text()
        assert (d / "reference" / SOL[lang]).exists()
        assert any((d / "tests" / lang / "visible").iterdir()) and any((d / "tests" / lang / "hidden").iterdir())
    for m in l["common_mistakes"]:                       # every test: signal must point at a real test
        for s in m["signals"]:
            if s.startswith("test:"):
                import fnmatch
                assert any(fnmatch.fnmatch("test_" + n, s[5:]) for n in names), (lid, s)


def test_concept_graph_is_a_dag_with_the_required_chains():
    def reach(n, seen=None):
        seen = seen if seen is not None else set()
        for r in CONCEPTS[n]["requires"]:
            assert r in CONCEPTS
            if r not in seen:
                seen.add(r); reach(r, seen)
        return seen
    for n in CONCEPTS:
        assert n not in reach(n), f"cycle through {n}"
    assert {"recursion", "base_cases"} <= reach("dp") and "arrays" in reach("array_indexing")
    assert "base_cases" in reach("recursion")


@pytest.mark.parametrize("lid", CODE)
def test_references_have_no_static_false_positives(lid):
    l = load(lid)
    for lang in l["languages"]:
        assert V.static_ids(l, lang, (ROOT / lid / "reference" / SOL[lang]).read_text()) == [], (lid, lang)


@pytest.mark.parametrize("lid", CODE)
def test_seeded_bug_patches_apply_and_static_bugs_give_identical_mistake_id_in_every_language(lid):
    d = ROOT / lid
    l = load(lid)
    bugs = (yaml.safe_load((d / "seeded_bugs.yaml").read_text()) or {}).get("bugs", [])
    assert bugs, "every lesson needs seeded bugs"
    for b in bugs:
        seen = {}
        for lang in l["languages"]:
            text = V.apply_bug((d / "reference" / SOL[lang]).read_text(), b, lang)
            if text is None:
                continue
            if b.get("static"):
                ids = {m for m, _ in V.static_ids(l, lang, text)}
                assert b["static"] in ids, (lid, b["id"], lang, ids)
                seen[lang] = b["static"] if b["static"] in ids else None
        if b.get("static"):
            assert len(set(seen.values())) == 1 and len(seen) == len(l["languages"])


def test_three_languages_same_bug_same_id_python_java_go():
    l = load("binary-search")
    b = yaml.safe_load((ROOT / "binary-search" / "seeded_bugs.yaml").read_text())["bugs"][0]
    got = {lang: {m for m, _ in V.static_ids(l, lang, V.apply_bug((ROOT / "binary-search" / "reference" / SOL[lang]).read_text(), b, lang))}
           for lang in ("python", "java", "go")}
    assert all(v == {"boundary_off_by_one"} for v in got.values()), got
