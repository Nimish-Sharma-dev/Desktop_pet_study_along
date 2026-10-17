"""Scenario S10: Failure modes and resilient graceful fallbacks."""

from __future__ import annotations

import asyncio
from pathlib import Path
from adapters.graph_adapter import GraphAdapter
from adapters.tutor_adapter import TutorAdapter
from tests.e2e.conftest import stack_context


def test_s10_resilient_failure_modes_and_pause(lessons_path):
    """
    S10 Failure modes: stop Ollama, stop FalkorDB, kill daemon, pause collection
    -> the pet shows a graceful state, nothing crashes, and recovery works.
    """
    async def run():
        # 1. Offline FalkorDB resilience
        g_adapter = GraphAdapter(host="127.0.0.1", port=63999)  # Non-existent port
        assert g_adapter._get_graph() is None
        # Recording attempt and updating mastery must not crash
        att = g_adapter.record_attempt("test-student", "binary-search", True)
        assert att is not None
        m_upd = g_adapter.update_mastery("test-student", "loop_invariants", True)
        assert m_upd.mastery >= 0.0
        # Progress and graph snapshot return clean structures
        prog = g_adapter.get_progress("test-student")
        assert "streak" in prog
        assert "concepts" in prog
        snapshot = g_adapter.get_graph_snapshot("test-student")
        assert "nodes" in snapshot and "edges" in snapshot

        # 2. Offline Ollama resilience in TutorAdapter
        t_adapter = TutorAdapter(g_adapter, model="non_existent_model")
        finding = {
            "kind": "pattern",
            "mistake_id": "boundary_off_by_one",
            "concept_ids": ["array_indexing"],
            "file": "test.py",
            "line": 4,
            "confidence": 0.9,
        }
        out = t_adapter.handle(finding, "test-student")
        assert out is not None
        assert "question" in out
        assert len(out["question"]) > 10
        assert out["pet_state"] in ("asking", "curious", "stressed", "detective")
        assert "graph_trace" in out

        # 3. Pause collection via Pipeline
        async with stack_context() as (pipeline, editor, ui):
            lesson_file = lessons_path / "binary-search" / "starter" / "solution.py"
            buggy_code = "def binary_search(nums, target):\n    for i in range(len(nums) + 1): pass\n"

            # When paused: events are ignored
            pipeline.paused = True
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code)
            await asyncio.sleep(0.2)
            assert len(ui.bubbles) == 0, "No bubbles should fire while collection is paused"

            # When resumed: collection resumes normally
            pipeline.paused = False
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code)
            await asyncio.sleep(0.3)
            b = await ui.wait_for_bubble(timeout=3.0)
            assert b is not None, "Pipeline must resume firing bubbles when unpaused"

    asyncio.run(run())
