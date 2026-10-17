"""Scenario S3: Repeat the same mistake 3 times -> stressed/escalate, drops after pass."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tests.e2e.conftest import stack_context


def test_s3_recurrence_escalation_and_reset(lessons_path):
    """
    S3 Repeat the same mistake 3 times -> pet shows stressed/detective,
    hint level escalates, then drops after a pass.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            lesson_file = lessons_path / "binary-search" / "starter" / "solution.py"

            buggy_code_1 = """
def binary_search(nums: list[int], target: int) -> int:
    t = 0
    for i in range(len(nums) + 1):
        t += nums[i]
    return t
"""
            # Student tweaks the range call
            buggy_code_2 = """
def binary_search(nums: list[int], target: int) -> int:
    t = 0
    for i in range(0, len(nums) + 1):
        t += nums[i]
    return t
"""
            # Student renames the loop variable
            buggy_code_3 = """
def binary_search(nums: list[int], target: int) -> int:
    t = 0
    for idx in range(len(nums) + 1):
        t += nums[idx]
    return t
"""
            # 1st Occurrence
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code_1)
            await asyncio.sleep(0.3)
            b1 = await ui.wait_for_bubble(timeout=3.0)
            assert b1 is not None
            assert b1["mistake_id"] == "boundary_off_by_one"
            assert b1["hint_level"] == 1
            assert b1["pet_state"] in ("asking", "curious")

            # 2nd Occurrence -> hint level escalates
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code_2)
            await asyncio.sleep(0.3)
            b2 = await ui.wait_for_bubble(timeout=3.0)
            assert b2 is not None
            assert b2["mistake_id"] == "boundary_off_by_one"
            assert b2["hint_level"] >= 2

            # 3rd Occurrence -> Stressed pet state and higher hint level
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code_3)
            await asyncio.sleep(0.3)
            b3 = await ui.wait_for_bubble(timeout=3.0)
            assert b3 is not None
            assert b3["mistake_id"] == "boundary_off_by_one"
            assert b3["pet_state"] in ("stressed", "detective")
            assert b3["hint_level"] >= 3

            # Student passes tests
            pass_result = {
                "lesson_id": "binary-search",
                "language": "python",
                "results": [{"name": "test_pass", "passed": True}],
                "all_passed": True,
            }
            ui.clear()
            await pipeline.after_tests(editor.student_id, str(lesson_file), "python", pass_result)
            assert "celebrating" in ui.pet_states

            # Next attempt after pass -> recurrence is reset, hint level drops back to 1
            buggy_code_after = """
def binary_search(nums: list[int], target: int) -> int:
    t = 0
    for k in range(len(nums) + 1):
        t += nums[k]
    return t
"""
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code_after)
            await asyncio.sleep(0.3)
            b_after = await ui.wait_for_bubble(timeout=3.0)
            assert b_after is not None
            assert b_after["hint_level"] == 1
            assert b_after["pet_state"] in ("asking", "curious")

    asyncio.run(run())
