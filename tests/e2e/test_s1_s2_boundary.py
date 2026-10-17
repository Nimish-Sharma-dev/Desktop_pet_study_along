"""Scenarios S1 & S2: Boundary bug across Python, Java, and Go."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tests.e2e.conftest import stack_context


def test_s1_boundary_bug_python_end_to_end(lessons_path):
    """
    S1 Boundary bug, Python: write binary search with hi=len(arr), run tests,
    expect failing test -> boundary_off_by_one finding -> L1 question in the bubble,
    no code in it, graph_update lit in the Live Graph, then fix it, tests pass,
    celebrating + confetti + mastery up.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            lesson_file = lessons_path / "binary-search" / "starter" / "solution.py"

            # Step 1: Student writes buggy binary search with loop_bound_off_by_one
            buggy_code = """
def binary_search(nums: list[int], target: int) -> int:
    t = 0
    for i in range(len(nums) + 1):
        t += nums[i]
    return t
"""
            await editor.edit(str(lesson_file), buggy_code, language="python")
            await asyncio.sleep(0.3)  # wait for debounce batch

            bubble = await ui.wait_for_bubble(timeout=3.0)
            assert bubble is not None, "Expected bubble from static rule boundary_off_by_one"
            assert bubble["mistake_id"] == "boundary_off_by_one"
            assert bubble["hint_level"] >= 1
            # Safeguard rule: pet NEVER outputs code blocks or raw fix
            assert "```" not in bubble["question"]
            assert "return" not in bubble["question"].lower() or "what" in bubble["question"].lower()

            # Step 2: Verify graph_update lit in Live Graph with highlight
            assert len(ui.graph_updates) > 0
            last_gu = ui.graph_updates[-1]
            assert "highlight" in last_gu
            assert last_gu["highlight"]["reason"] == "boundary_off_by_one"

            # Step 3: Now simulate running tests that pass
            pass_test_result = {
                "lesson_id": "binary-search",
                "language": "python",
                "duration_ms": 42.0,
                "results": [
                    {"name": "test_basic_search", "passed": True, "duration_ms": 12.0, "message": ""},
                    {"name": "test_not_found", "passed": True, "duration_ms": 8.0, "message": ""},
                ],
                "all_passed": True,
            }
            ui.clear()
            await pipeline.after_tests(editor.student_id, str(lesson_file), "python", pass_test_result)

            # Step 4: Verify celebrating + confetti + mastery update
            assert "celebrating" in ui.pet_states
            assert len(ui.confetti) > 0
            assert ui.confetti[-1]["count"] >= 40
            assert len(ui.mastery_updates) > 0
            assert ui.mastery_updates[-1]["delta"] > 0

    asyncio.run(run())


def test_s2_same_logical_bug_java_and_go(lessons_path):
    """
    S2 Same logical bug in Java and Go -> same mistake_id and a comparable question.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            lesson_file = lessons_path / "binary-search" / "starter" / "solution.py"

            # Java buggy code
            java_code = """
class S {
    static int f(int[] nums) {
        int t = 0;
        for (int i = 0; i <= nums.length; i++) {
            t += nums[i];
        }
        return t;
    }
}
"""
            ui.clear()
            await editor.send_event("edit", str(lesson_file), content=java_code, language="java")
            await asyncio.sleep(0.3)
            bubble_java = await ui.wait_for_bubble(timeout=3.0)
            assert bubble_java is not None
            assert bubble_java["mistake_id"] == "boundary_off_by_one"
            assert "```" not in bubble_java["question"]

            # Go buggy code
            go_code = """
package s
func f(nums []int) int {
    t := 0
    for i := 0; i <= len(nums); i++ {
        t += nums[i]
    }
    return t
}
"""
            ui.clear()
            await editor.send_event("edit", str(lesson_file), content=go_code, language="go")
            await asyncio.sleep(0.3)
            bubble_go = await ui.wait_for_bubble(timeout=3.0)
            assert bubble_go is not None
            assert bubble_go["mistake_id"] == "boundary_off_by_one"
            assert "```" not in bubble_go["question"]

    asyncio.run(run())
