"""Scenario S9: Guard blocking leaked fixes and fallback to seed questions."""

from __future__ import annotations

from tutor.guard import guard_check
from adapters.tutor_adapter import sanitize_final_output


def test_s9_guard_blocks_code_leak_and_falls_back():
    """
    S9 Guard: force a model output that leaks the fix -> it is blocked and
    regenerated, or the seed question is used after 3 failures.
    """
    # 1. Candidate with fenced code
    cand_code_block = "You should change your loop to this:\n```python\nwhile lo <= hi:\n    mid = (lo + hi) // 2\n```"
    valid, violation = guard_check(cand_code_block)
    assert not valid
    assert "code block" in violation.lower() or "```" in violation

    # 2. Candidate with direct assignment fix
    cand_assignment = "Just write mid = (lo + hi) // 2 to fix the midpoint."
    valid, violation = guard_check(cand_assignment)
    assert not valid

    # 3. Candidate with return statement fix
    cand_return = "You need to return -1 at the bottom."
    valid, violation = guard_check(cand_return)
    assert not valid

    # 4. Daemon Independent Safeguard: blocks any leaked text and substitutes fallback
    safe_from_block = sanitize_final_output(cand_code_block, "boundary_off_by_one")
    assert "```" not in safe_from_block
    assert "Consider what happens" in safe_from_block

    safe_from_assign = sanitize_final_output(cand_assignment, "boundary_off_by_one")
    assert "=" not in safe_from_assign or "?" in safe_from_assign
    assert "Consider what happens" in safe_from_assign

    # 5. Clean Socratic question passes through
    clean_socratic = "What is the largest index you are allowed to read from this list?"
    valid, _ = guard_check(clean_socratic)
    assert valid
    assert sanitize_final_output(clean_socratic, "boundary_off_by_one") == clean_socratic
