"""Scenario S7: System Design command center mode, radar chart updates, and rubric question."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tests.e2e.conftest import stack_context


def test_s7_system_design_radar_and_rubric_question(lessons_path):
    """
    S7 System design: open the URL shortener lesson -> command center + hard hat
    -> edit design.md -> radar chart updates -> a rubric question is asked.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            design_file = lessons_path / "url-shortener" / "starter" / "design.md"
            content = design_file.read_text(encoding="utf-8")

            # Step 1: Open file / focus sends mode switch to system_design
            ui.clear()
            await editor.send_event("file_open", str(design_file))
            await asyncio.sleep(0.1)
            assert "system_design" in ui.modes

            # Step 2: Student edits design.md
            ui.clear()
            await editor.edit(str(design_file), content)
            await asyncio.sleep(0.3)

            # Step 3: Verify radar chart / review payload broadcast
            assert len(ui.reviews) > 0, "Expected review channel message for system design radar"
            last_review = ui.reviews[-1]
            assert last_review["design_id"] == "url-shortener"
            assert "axes" in last_review
            assert len(last_review["axes"]) >= 8

            # Step 4: Verify Socratic question asked for rubric gap
            bubble = await ui.wait_for_bubble(timeout=3.0)
            assert bubble is not None, "Expected Socratic question on rubric gap"
            assert bubble["mistake_id"].startswith("rubric_gap_")
            assert "```" not in bubble["question"]
            assert len(bubble["question"]) > 10

    asyncio.run(run())
