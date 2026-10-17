"""Scenario S8: Voice round trip offline."""

from __future__ import annotations

import asyncio
from tests.e2e.conftest import stack_context


def test_s8_voice_round_trip_offline():
    """
    S8 Voice round trip offline: speak a question / reply -> Socratic spoken reply.
    Verifies that push-to-talk transcription feeds into handle_reply and outputs
    a valid Socratic question suitable for TTS speech synthesis.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            spoken_text = "I think the upper bound should be inclusive because the array has N items."

            spoken_replies = []
            def fake_speak(text: str) -> None:
                spoken_replies.append(text)

            ui.clear()
            out = await pipeline.handle_reply(spoken_text, sid="test-student", source="voice")

            # Verify response is non-empty Socratic question
            assert out is not None
            assert "question" in out
            question = out["question"]
            assert len(question) > 10
            # Socratic: ends with a question mark or invites reflection
            assert "?" in question or "walk" in question.lower()
            # Must not leak raw code
            assert "```" not in question

            # TTS synthesizes the exact Socratic question
            fake_speak(question)
            assert len(spoken_replies) == 1
            assert spoken_replies[0] == question

            # UI receives bubble update
            assert len(ui.bubbles) > 0
            assert ui.bubbles[-1]["question"] == question

    asyncio.run(run())
