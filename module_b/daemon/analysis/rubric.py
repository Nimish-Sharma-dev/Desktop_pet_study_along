"""System-design rubric scorer.

    score_design(design, lesson) -> {
        "lesson_id", "axes": {axis: 0-5, ...8}, "radar": {8 axes + scalability, fault_tolerance, cost},
        "total", "max", "passed", "diagram": bool, "gaps": [...], "findings": [Finding dict]}

Findings here are RUBRIC GAPS, not code bugs: kind="pattern", mistake_id="rubric_gap_<axis>" (mapped through the
lesson's `rubric:<axis>` signals), line = the section heading's line (1 if the section is missing).
Deterministic regex coverage checks - see README "Limits of the rubric scorer".
"""
from __future__ import annotations
import re
from pathlib import Path

import yaml

from .analyzer import _mistake_for_signal, lessons_root, load_lesson
from .model import Finding

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def load_rubric(lesson: dict | None, lesson_dir: Path | None = None) -> dict:
    lid = (lesson or {}).get("id")
    lesson_dir = lesson_dir or (lessons_root() / lid if lid else None)
    rpath = (lesson_dir / "rubric.yaml") if lesson_dir else None
    if not rpath or not rpath.exists():
        rpath = lessons_root() / "_templates" / "system-design-rubric.yaml"
    return _load(rpath)


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    base_ref = data.pop("extends", None)
    if not base_ref:
        return data
    base = _load((path.parent / base_ref).resolve())
    for k, v in data.items():
        if k == "axes":
            base["axes"].update(v)
        else:
            base[k] = v
    return base


def parse_sections(text: str) -> list:
    """[(level, title, line_no(1-based), body_text)] - body runs to the next heading of same or higher level."""
    lines = text.splitlines()
    heads = [(i, len(m.group(1)), m.group(2)) for i, l in enumerate(lines) if (m := _HEADING.match(l))]
    out = []
    for idx, (i, lvl, title) in enumerate(heads):
        end = len(lines)
        for j, l2, _ in heads[idx + 1:]:
            if l2 <= lvl:
                end = j
                break
        out.append((lvl, title, i + 1, "\n".join(lines[i + 1:end])))
    return out


def _find_section(sections: list, keywords: list):
    best = None
    for lvl, title, line, body in sections:
        if any(k.lower() in title.lower() for k in keywords):
            if best is None or len(body) > len(best[3]):
                best = (lvl, title, line, body)
    return best


def _hit(patterns: list, text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _real_diagram(f: Path) -> bool:
    """A diagram file counts only if it is not the untouched starter placeholder (has a TODO) and has some content."""
    if not f.exists():
        return False
    if f.suffix in (".png", ".drawio"):
        return f.stat().st_size > 0
    txt = f.read_text(errors="replace")
    body = [l for l in txt.splitlines() if l.strip() and not l.strip().startswith("%%")]
    return "TODO" not in txt and len(body) >= 3


def score_design(design, lesson=None, rubric: dict | None = None, file: str | None = None) -> dict:
    lesson = load_lesson(lesson)
    rubric = rubric or load_rubric(lesson)
    path = None
    if isinstance(design, Path) or (isinstance(design, str) and "\n" not in design and len(design) < 500 and Path(design).exists()):
        path = Path(design)
        text = path.read_text()
    else:
        text = str(design)
    sections = parse_sections(text)
    min_words = rubric.get("min_words", 25)
    axes, details = {}, {}
    for aid, ax in rubric["axes"].items():
        sec = _find_section(sections, ax["section"])
        body = sec[3] if sec else text
        words = len(re.findall(r"\w+", body))
        hits = [c["id"] for c in ax["checks"] if _hit(c["any"], body)]
        score = len(hits)
        if sec is None:
            score = min(score, 2)
        elif words < min_words:
            score = min(score, 1)
        axes[aid] = score
        details[aid] = {"section_found": sec is not None, "line": sec[2] if sec else 1,
                        "missing": [c["hint"] for c in ax["checks"] if c["id"] not in hits]}
    radar = dict(axes)
    for rid, spec in rubric.get("radar", {}).items():
        base = sum(axes.get(a, 0) * w for a, w in spec["from"].items())
        extra = sum(1 for pats in spec["checks"] if _hit(pats, text))
        radar[rid] = round(0.5 * base + 0.5 * extra, 1)

    d = rubric.get("diagram", {})
    has_diagram = _hit(d.get("inline", []), text)
    if path is not None and not has_diagram:
        has_diagram = any(_real_diagram(path.parent / f) for f in d.get("files", []))
    total, mx = sum(axes.values()), 5 * len(axes)
    thr = rubric.get("pass", {"axis_min": 3, "total_min": 28})
    passed = all(v >= thr["axis_min"] for v in axes.values()) and total >= thr["total_min"] and has_diagram

    findings, gaps = [], []
    lid = (lesson or {}).get("id")
    fpath = file or (str(path) if path else "design.md")
    for aid, sc in sorted(axes.items(), key=lambda kv: kv[1]):
        if sc >= thr["axis_min"]:
            continue
        det = details[aid]
        cm = _mistake_for_signal(lesson, f"rubric:{aid}")
        ev = (f"{rubric['axes'][aid]['title']}: {sc}/5" + ("" if det["section_found"] else ", no section found")
              + (f"; not covered: {', '.join(det['missing'][:3])}" if det["missing"] else ""))
        gaps.append({"axis": aid, "score": sc, "missing": det["missing"]})
        findings.append(Finding("pattern", cm["id"] if cm else f"rubric_gap_{aid}",
                                list(cm.get("concepts") or rubric["axes"][aid].get("concepts", [])) if cm else rubric["axes"][aid].get("concepts", []),
                                fpath, det["line"], ev, 0.6 + 0.1 * (thr["axis_min"] - sc), lid))
    if not has_diagram:
        cm = _mistake_for_signal(lesson, "rubric:diagram")
        findings.append(Finding("pattern", cm["id"] if cm else "rubric_gap_diagram", ["scaling"], fpath, 1,
                                "no architecture diagram found (mermaid block, image link or diagram file)", 0.7, lid))
    return {"lesson_id": lid, "axes": axes, "radar": radar, "total": total, "max": mx, "passed": passed,
            "diagram": has_diagram, "gaps": gaps, "findings": [f.to_dict() for f in findings]}
