"""Scenario S4: Guess spam detection vs genuine rewrite."""

from __future__ import annotations

import asyncio
from pathlib import Path
from analysis.tests import spam_fixtures as F
from tests.e2e.conftest import stack_context


def test_s4_guess_spam_nudge_and_genuine_rewrite(lessons_path):
    """
    S4 Guess spam: 5 rename/reshuffle edits with no logic change -> early L0 nudge.
    A genuine rewrite is NOT flagged.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            lesson_file = lessons_path / "binary-search" / "starter" / "solution.py"

            # 5 Rename edits with zero logic change from canonical benchmark
            ui.clear()
            for step in F.RENAMES:
                await editor.edit(str(lesson_file), step)
                await asyncio.sleep(0.08)

            # Wait for early L0 nudge
            bubble = await ui.wait_for_bubble(timeout=3.0)
            assert bubble is not None, "Expected early L0 nudge on guess spam"
            assert bubble["mistake_id"] == "guess_and_check" or bubble["hint_level"] == 0
            assert bubble["pet_state"] in ("detective", "curious", "asking")
            assert bubble["hint_level"] == 0

            # Genuine rewrite steps
            ui.clear()
            for step in F.REWRITE:
                await editor.edit(str(lesson_file), step)
                await asyncio.sleep(0.08)

            # Check that guess_and_check is NOT flagged on genuine rewrite
            guess_spam_bubbles = [b for b in ui.bubbles if b.get("mistake_id") == "guess_and_check"]
            assert len(guess_spam_bubbles) == 0, "Genuine rewrite must not trigger guess spam"

    asyncio.run(run())
