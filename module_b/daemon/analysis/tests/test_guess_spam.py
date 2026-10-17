import pytest
from analysis.guess_spam import GuessSpamDetector
from . import spam_fixtures as F


def run(seq, lang="python"):
    d, hits = GuessSpamDetector(), []
    for i, s in enumerate(seq, 1):
        r = d.observe("k", s, lang)
        if r:
            hits.append((i, r))
    return hits


def test_rename_streak_detected_within_four_edits():
    hits = run(F.RENAMES)
    assert hits and hits[0][0] <= 4
    assert set(hits[0][1].kinds) == {"rename"}


def test_line_reshuffle_detected_within_four_edits():
    hits = run(F.SHUFFLES)
    assert hits and hits[0][0] <= 4 and set(hits[0][1].kinds) == {"reshuffle"}


def test_flip_flopping_an_operator_is_detected():
    hits = run(F.FLIPFLOP)
    assert hits and "revert" in hits[0][1].kinds


@pytest.mark.parametrize("name", ["REWRITE", "REAL_STEPS", "DEPENDENT"])
def test_genuine_work_is_not_flagged(name):
    assert run(getattr(F, name)) == []


def test_typing_a_comment_or_half_typed_lines_is_not_flagged():
    b = F.BASE
    assert run([b + "# " + "x" * k + "\n" for k in range(1, 8)]) == []
    assert run([b, b.replace("return mid", "retu"), b.replace("return mid", "ret"), b, b]) == []


def test_character_by_character_rewrite_is_not_flagged():
    target = F.REWRITE[-1]
    snaps = [target[:i] for i in range(0, len(target) + 1, 3)]
    assert run([F.BASE] + snaps) == []


def test_finding_points_at_changed_line():
    hit = run(F.RENAMES)[0][1]
    assert hit.line >= 1 and 0.5 <= hit.confidence <= 0.9 and "control flow" in hit.evidence


def test_works_in_other_languages():
    java = "class S { static int f(int[] a) { int total = 0; for (int i = 0; i < a.length; i++) { total += a[i]; } return total; } }"
    seq = [java, java.replace("total", "sum"), java.replace("total", "acc"), java.replace("total", "t"), java.replace("total", "x")]
    assert run(seq, "java")
