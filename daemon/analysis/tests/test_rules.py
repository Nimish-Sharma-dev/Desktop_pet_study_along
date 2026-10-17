import pytest
from analysis.parser import parse, supported_languages
from analysis.rules import RULES, run_rules
from analysis.analyzer import Analyzer
from .fixtures import BUGGY, GOOD


def _lang(key):
    return key.split("_")[0] if key.startswith("python_") else key


def cases(table):
    return [(r, l, c) for r, d in table.items() for l, c in d.items()]


@pytest.mark.parametrize("rule,lang,code", cases(BUGGY))
def test_rule_fires_in_every_grammar(rule, lang, code):
    p = parse(code, lang)
    assert not p.has_errors, "fixture must parse cleanly"
    assert rule in [h.rule for h in run_rules(p)]


@pytest.mark.parametrize("rule,lang,code", cases(GOOD))
def test_rule_has_no_false_positive_on_correct_code(rule, lang, code):
    p = parse(code, _lang(lang))
    assert not p.has_errors
    assert rule not in [h.rule for h in run_rules(p)]


def test_all_ten_grammars_load_and_every_rule_is_covered():
    assert len(supported_languages()) >= 10
    for want in ("python", "java", "c", "cpp", "c_sharp", "go", "rust", "javascript", "typescript", "kotlin"):
        assert want in supported_languages()
    assert set(BUGGY) == set(RULES)


def test_same_logical_bug_same_mistake_id_across_languages():
    """Acceptance: same logical bug in different languages -> identical mistake_id (via lesson signals)."""
    lesson = {"id": "t", "common_mistakes": [
        {"id": "boundary_off_by_one", "concepts": ["array_indexing"], "signals": ["rule:loop_bound_off_by_one"], "seed_questions": []}]}
    ids = {}
    for lang, code in BUGGY["loop_bound_off_by_one"].items():
        ev = [{"type": "edit", "ts": 1, "file": "x", "language": lang, "content": code, "student_id": "s"}]
        ids[lang] = {f.mistake_id for f in Analyzer(dedupe=False).analyze(ev, lesson)}
    assert all(v == {"boundary_off_by_one"} for v in ids.values()), ids


def test_comments_and_strings_do_not_trigger_rules():
    code = 'def f(xs):\n    # for i in range(len(xs) + 1): xs.remove(1)\n    s = "for i in range(len(xs)+1)"\n    return s\n'
    assert run_rules(parse(code, "python")) == []


def test_unparseable_buffer_yields_no_static_findings():
    ev = [{"type": "edit", "ts": 1, "file": "a.py", "language": "python", "content": "def f(n:\n    for i in range(len(", "student_id": "s"}]
    assert Analyzer(dedupe=False).analyze(ev) == []
