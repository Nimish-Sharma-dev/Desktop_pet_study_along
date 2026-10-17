"""Scenarios S5 & S6: Prerequisite bottleneck analysis and hybrid retrieval."""

from __future__ import annotations

import asyncio
from pathlib import Path
from analysis.microlesson import root_weak_concept, generate_micro_lesson
from tests.e2e.conftest import stack_context


def test_s5_bottleneck_detection_and_microlesson(tmp_path):
    """
    S5 Bottleneck: fail a DP lesson with weak recursion base cases seeded in the graph
    -> the bottleneck query returns recursion base_cases and a micro-lesson is offered.
    """
    # Seeded mastery: student struggles with base_cases (0.2) and recursion (0.35), tries dp
    mastery = {
        "dp": 0.20,
        "recursion": 0.35,
        "base_cases": 0.25,
        "array_indexing": 0.85,
    }

    # Verify prerequisite bottleneck analysis walks to root weak prerequisite
    root = root_weak_concept("dp", mastery)
    assert root == "base_cases", f"Expected 'base_cases' as root bottleneck, got {root}"

    # Generate micro lesson for root weak concept
    micro_dir = generate_micro_lesson(root, out_dir=tmp_path / "micro-base-cases", needed_by="dp")
    assert micro_dir.exists()
    assert (micro_dir / "lesson.yaml").is_file()
    assert (micro_dir / "README.md").is_file()
    assert (micro_dir / "starter").is_dir()
    assert (micro_dir / "tests").is_dir()


def test_s6_hybrid_retrieval_inspector_cypher_and_timing(lessons_path):
    """
    S6 Hybrid retrieval: a mistake triggers a single Cypher call with vector ranking;
    the inspector shows the Cypher and a real query_ms.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            pipeline.inspector = True
            lesson_file = lessons_path / "binary-search" / "starter" / "solution.py"

            buggy_code = """
def binary_search(nums: list[int], target: int) -> int:
    val = 0
    for idx in range(len(nums) + 1):
        val = nums[idx]
    return val
"""
            ui.clear()
            await editor.edit(str(lesson_file), buggy_code)
            await asyncio.sleep(0.3)

            bubble = await ui.wait_for_bubble(timeout=3.0)
            assert bubble is not None, "Expected bubble from finding"

            # Check inspector telemetry in bubble payload
            trace = bubble.get("graph_trace")
            assert trace is not None, "Contract 4 requires graph_trace in bubble"
            assert "cypher" in trace, "Expected Cypher query string in graph_trace"
            assert "MATCH" in trace["cypher"], "Expected valid Cypher pattern in graph_trace"
            
            # Query ms must be a real measured non-negative float
            assert "query_ms" in trace
            assert isinstance(trace["query_ms"], (int, float))
            assert trace["query_ms"] >= 0.0

            # Trace nodes and edges for live graph visualization
            assert "nodes" in trace and len(trace["nodes"]) >= 2
            assert any(n.get("label") == "Mistake" for n in trace["nodes"])
            assert any(n.get("label") == "Concept" for n in trace["nodes"])
            assert "edges" in trace and len(trace["edges"]) >= 1

    asyncio.run(run())
