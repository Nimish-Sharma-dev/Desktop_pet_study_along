import os
import re
import shutil
from pathlib import Path

import pytest
import yaml

from analysis.rubric import score_design, parse_sections
from analysis.microlesson import root_weak_concept, generate_micro_lesson, prerequisites, load_concepts

ROOT = Path(__file__).resolve().parents[3] / "lessons"
DESIGNS = ["url-shortener", "rate-limiter"]
AXES = ["requirements", "estimation", "data_model", "api", "scaling", "bottlenecks", "failure_handling", "tradeoffs"]


def drop_section(text, title):
    lines = text.splitlines(keepends=True)
    secs = parse_sections(text)
    for lvl, t, line, body in secs:
        if t.lower() == title.lower():
            n = len(body.splitlines()) + 1
            return "".join(lines[:line - 1] + lines[line - 1 + n:])
    raise KeyError(title)


@pytest.mark.parametrize("lid", DESIGNS)
def test_reference_design_passes_and_starter_fails(lid):
    ref = score_design(ROOT / lid / "reference" / "design.md", lid)
    assert ref["passed"] and ref["diagram"] and ref["gaps"] == [] and all(ref["axes"][a] >= 4 for a in AXES)
    st = score_design(ROOT / lid / "starter" / "design.md", lid)
    assert not st["passed"] and st["total"] <= 8 and not st["diagram"]
    assert {f["mistake_id"] for f in st["findings"]} >= {f"rubric_gap_{a}" for a in AXES}


@pytest.mark.parametrize("lid", DESIGNS)
def test_radar_has_rubric_axes_plus_scalability_fault_tolerance_cost(lid):
    r = score_design(ROOT / lid / "reference" / "design.md", lid)["radar"]
    assert set(r) == set(AXES) | {"scalability", "fault_tolerance", "cost"}
    assert all(0 <= v <= 5 for v in r.values()) and r["scalability"] >= 3


@pytest.mark.parametrize("lid", DESIGNS)
def test_seeded_gaps_are_reported(lid):
    text = (ROOT / lid / "reference" / "design.md").read_text()
    bugs = yaml.safe_load((ROOT / lid / "seeded_bugs.yaml").read_text())["bugs"]
    assert bugs
    for b in bugs:
        res = score_design(drop_section(text, b["remove_section"]) , lid)
        assert res["axes"][b["expect_gap"]] <= 2 and not res["passed"]
        f = [x for x in res["findings"] if x["mistake_id"] == b["expect_mistake"]]
        assert f and f[0]["kind"] == "pattern" and f[0]["lesson_id"] == lid and f[0]["line"] >= 1
        others = [a for a in AXES if a != b["expect_gap"]]
        assert all(res["axes"][a] >= 4 for a in others), "removing one section must not hurt the others"


def test_thin_section_is_capped_and_missing_diagram_is_a_finding(tmp_path):
    text = (ROOT / "url-shortener" / "reference" / "design.md").read_text()
    thin = re.sub(r"(## Estimation\n\n).*?(\n## Data model)", r"\1QPS and GB.\n\2", text, flags=re.S)
    assert score_design(thin, "url-shortener")["axes"]["estimation"] <= 1
    nodiag = re.sub(r"```mermaid.*?```", "", text, flags=re.S)
    r = score_design(nodiag, "url-shortener")
    assert not r["diagram"] and any(f["mistake_id"] == "rubric_gap_diagram" for f in r["findings"])
    (tmp_path / "design.md").write_text(nodiag)
    assert not score_design(tmp_path / "design.md", "url-shortener")["diagram"]
    (tmp_path / "diagram.mmd").write_text("flowchart LR\n a-->b\n b-->c\n c-->d\n")
    assert score_design(tmp_path / "design.md", "url-shortener")["diagram"]


def test_keyword_stuffing_outside_the_section_does_not_score():
    text = (ROOT / "url-shortener" / "reference" / "design.md").read_text()
    stuffed = drop_section(text, "Failure handling") + "\n## Misc\n\nfailover replica backup retry timeout\n"
    assert score_design(stuffed, "url-shortener")["axes"]["failure_handling"] <= 2


# ------------------------------------------------------------------ micro lessons
def test_root_weak_concept_walks_to_deepest_weak_prerequisite():
    m = {"recursion": 0.2, "base_cases": 0.3, "memoization": 0.4}
    assert root_weak_concept("dp", m) == "base_cases"
    assert root_weak_concept("dp", {"recursion": 0.2}) == "recursion"
    assert root_weak_concept("dp", {}) == "dp"
    assert root_weak_concept("binary_search", {"array_indexing": 0.1, "arrays": 0.2}) == "arrays"
    assert prerequisites("dp")[:2] == ["memoization", "optimal_substructure"] and "base_cases" in prerequisites("dp")


def test_generated_micro_lesson_is_runnable_end_to_end(tmp_path, monkeypatch):
    root = tmp_path / "lessons"
    root.mkdir()
    for n in ("_support", "_templates", "_tools", "concepts.yaml"):
        src = ROOT / n
        dst = root / n
        try:
            os.symlink(src, dst)
        except (OSError, NotImplementedError):
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    monkeypatch.setenv("LESSONS_DIR", str(root))
    out = generate_micro_lesson("base_cases", root / "micro-base_cases")
    lesson = yaml.safe_load((out / "lesson.yaml").read_text())
    assert lesson["id"] == "micro-base_cases" and lesson["concepts"] == ["base_cases"] and lesson["estimated_minutes"] <= 15
    assert lesson["common_mistakes"][0]["seed_questions"]
    assert set(lesson) == {"id", "title", "track", "difficulty", "concepts", "prerequisites", "estimated_minutes", "common_mistakes", "languages"}
    from analysis import run_tests
    ws = tmp_path / "ws"; ws.mkdir()
    (ws / "solution.py").write_text((out / "reference" / "solution.py").read_text())
    r = run_tests("micro-base_cases", "python", ws)
    assert all(x["passed"] for x in r["results"]) and len(r["results"]) == 4
    (ws / "solution.py").write_text((out / "starter" / "solution.py").read_text())
    assert not any(x["passed"] for x in run_tests("micro-base_cases", "python", ws)["results"])


def test_concept_without_drill_still_generates_a_conversational_micro_lesson(tmp_path, monkeypatch):
    root = tmp_path / "lessons"; root.mkdir()
    for n in ("_support", "_templates", "_tools", "concepts.yaml"):
        src = ROOT / n
        dst = root / n
        try:
            os.symlink(src, dst)
        except (OSError, NotImplementedError):
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    monkeypatch.setenv("LESSONS_DIR", str(root))
    out = generate_micro_lesson("pointers", root / "micro-pointers")
    assert (out / "lesson.yaml").exists() and not (out / "cases.yaml").exists()
    assert "no code drill" in (out / "README.md").read_text()
