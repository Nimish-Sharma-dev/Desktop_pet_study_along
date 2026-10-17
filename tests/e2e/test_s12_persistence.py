"""Scenario S12: Student state persistence across restarts."""

from __future__ import annotations

import json
from pathlib import Path
from adapters.graph_adapter import GraphAdapter, DATA_STORE_PATH


def test_s12_state_persistence_across_restarts():
    """
    S12 Student closes and reopens everything -> history, mastery, streak
    and evolution stage persist.
    """
    sid = "persisted-student"

    # Step 1: Initial session - student makes progress
    g1 = GraphAdapter()
    g1.record_attempt(sid, "binary-search", True)
    g1.record_attempt(sid, "two-pointers", True)
    g1.record_attempt(sid, "recursion-basics", False, mistake_id="base_cases", line=12)
    m1 = g1.update_mastery(sid, "binary_search", True)
    m2 = g1.update_mastery(sid, "loop_invariants", True)

    prog1 = g1.get_progress(sid)
    streak1 = prog1["streak"]["current"]
    evo1 = prog1["evolution"]["stage"]
    assert evo1 in (1, 2, 3)

    # Verify data written to local persistent store
    assert DATA_STORE_PATH.exists()
    raw = json.loads(DATA_STORE_PATH.read_text(encoding="utf-8"))
    assert len(raw.get("attempts", [])) >= 3
    assert "binary_search" in raw.get("mastery", {})

    # Step 2: "Close everything" - drop g1 and instantiate brand new GraphAdapter
    del g1

    g2 = GraphAdapter()
    prog2 = g2.get_progress(sid)

    # Step 3: Verify all state preserved
    assert prog2["streak"]["current"] == streak1
    assert prog2["evolution"]["stage"] == evo1
    
    # Check mastery preservation
    concepts2 = {c["id"]: c["mastery"] for c in prog2["concepts"]}
    assert "binary_search" in concepts2
    assert concepts2["binary_search"] >= 0.5

    # Check lesson status preservation
    lessons2 = {l["id"]: l["status"] for l in prog2["lessons"]}
    assert lessons2.get("binary-search") == "done"
    assert lessons2.get("recursion-basics") in ("in_progress", "done")
