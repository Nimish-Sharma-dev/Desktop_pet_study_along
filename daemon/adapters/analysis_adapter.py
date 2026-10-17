"""Analysis adapter: validates events, runs AST/test/rubric analysis, and maps to canonical contracts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import analysis
from contracts import Finding, ReviewAxis, ReviewPayload, TestCaseResult, TestResult

log = logging.getLogger("tutor.adapters.analysis")


def adapt_analyze(event_batch: List[Dict[str, Any]], lesson: Optional[Dict[str, Any]] = None) -> List[Finding]:
    """Run analysis.analyze and normalize results to canonical Finding objects."""
    try:
        raw_findings = analysis.analyze(event_batch, lesson)
    except Exception:
        log.exception("analysis.analyze failed on batch")
        return []

    findings: List[Finding] = []
    for f in raw_findings or []:
        d = f.to_dict() if hasattr(f, "to_dict") else dict(f)
        try:
            findings.append(Finding(**d))
        except Exception:
            log.warning("Failed to parse finding into canonical model: %s", d)
    return findings


def adapt_run_tests(lesson_id: str, language: str, workspace_dir: str | Path) -> TestResult:
    """Run sandboxed tests and return canonical TestResult."""
    raw = analysis.run_tests(lesson_id, language, Path(workspace_dir))
    if not isinstance(raw, dict):
        raw = dict(raw)

    results_list: List[TestCaseResult] = []
    for r in raw.get("results") or []:
        rd = dict(r) if not isinstance(r, dict) else r
        results_list.append(TestCaseResult(**rd))

    all_passed = bool(results_list) and all(r.passed for r in results_list)
    return TestResult(
        lesson_id=raw.get("lesson_id", lesson_id),
        language=raw.get("language", language),
        duration_ms=raw.get("duration_ms", 0),
        results=results_list,
        all_passed=all_passed,
    )


def adapt_test_results_to_findings(
    test_result: TestResult | Dict[str, Any],
    lesson: Optional[Dict[str, Any]] = None,
    solution_file: str = "solution.py",
) -> List[Finding]:
    """Convert test failures to pedagogical findings."""
    res_dict = test_result.model_dump() if hasattr(test_result, "model_dump") else test_result
    raw_findings = analysis.test_results_to_findings(res_dict, lesson, solution_file)
    findings: List[Finding] = []
    for f in raw_findings or []:
        d = f.to_dict() if hasattr(f, "to_dict") else dict(f)
        try:
            findings.append(Finding(**d))
        except Exception:
            log.warning("Failed to normalize test failure finding: %s", d)
    return findings


def adapt_score_design(design_md_content: str, lesson: Optional[Dict[str, Any]] = None) -> Tuple[ReviewPayload, List[Finding]]:
    """Score system design markdown file, producing a UI ReviewPayload and tutor gap findings."""
    scored = analysis.score_design(design_md_content, lesson)
    lid = scored.get("lesson_id") or (lesson or {}).get("id") or "design"

    # Adapt axes for UI review channel
    axes_out: List[ReviewAxis] = []
    radar = scored.get("radar", {})
    axes_list = scored.get("axes", [])

    # If axes is a list of dicts: [{"axis": "data_model", "score": 0, "missing": [...]}, ...]
    if isinstance(axes_list, list):
        for ax in axes_list:
            if isinstance(ax, dict):
                ax_id = ax.get("axis", "")
                label = ax_id.replace("_", " ").title()
                score = float(ax.get("score", 0))
                axes_out.append(ReviewAxis(id=ax_id, label=label, score=score, max=5.0))
    elif isinstance(radar, dict):
        for k, v in radar.items():
            axes_out.append(ReviewAxis(id=k, label=k.replace("_", " ").title(), score=float(v) * 5.0, max=5.0))

    # Notes from missing rubric items
    notes: List[str] = []
    for ax in axes_list if isinstance(axes_list, list) else []:
        if isinstance(ax, dict):
            for m in ax.get("missing", [])[:2]:
                notes.append(f"{ax.get('axis', '').title()}: needs {m}")

    review = ReviewPayload(design_id=lid, axes=axes_out, notes=notes[:6])

    # Extract gap findings
    findings: List[Finding] = []
    for f in scored.get("findings", []):
        d = f.to_dict() if hasattr(f, "to_dict") else dict(f)
        try:
            findings.append(Finding(**d))
        except Exception:
            pass

    return review, findings
