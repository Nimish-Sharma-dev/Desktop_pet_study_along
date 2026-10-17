"""Module B: code analysis, test runners, sandbox, lesson content tooling.

Public interface (see README):
    analyze(event_batch, lesson=None) -> list[Finding]     Contract 3
    run_tests(lesson_id, language, workspace) -> dict       Contract 2
    test_results_to_findings(result, lesson) -> list[Finding]
    score_design(design_md, lesson) -> dict                 rubric scorer (system design)
    generate_micro_lesson(...)                              micro-lesson generator
"""
from .analyzer import Analyzer, analyze, load_lesson, test_results_to_findings
from .model import Finding
from .parser import supported_languages, detect_language


def run_tests(lesson_id: str, language: str, workspace):
    from .runners import run_tests as _run
    return _run(lesson_id, language, workspace)


def __getattr__(name):                     # lazy: keep `import analysis` light
    if name == "score_design":
        from .rubric import score_design
        return score_design
    if name in ("generate_micro_lesson", "root_weak_concept"):
        from . import microlesson
        return getattr(microlesson, name)
    raise AttributeError(name)
