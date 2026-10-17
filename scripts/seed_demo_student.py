#!/usr/bin/env python3
"""
Seed script to load a demo student with 2 weeks of realistic history.
Populates persistent storage and FalkorDB (if available) so the UI dashboard,
heatmaps, skill radar, timeline, and evolution pet are fully populated.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add daemon directory to sys.path
repo_root = Path(__file__).resolve().parents[1]
daemon_dir = repo_root / "daemon"
sys.path.insert(0, str(daemon_dir))

DATA_STORE_PATH = Path.home() / ".cache" / "tutor-pet" / "student_history.json"
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("seed")


def seed_demo_student(student_id: str = "local-user") -> None:
    now = datetime.now(timezone.utc)
    attempts = []
    
    # 14 days of realistic activity
    history_events = [
        # Day -13
        {"days_ago": 13, "lesson": "binary-search", "passed": False, "mistake": "boundary_off_by_one", "line": 14},
        {"days_ago": 13, "lesson": "binary-search", "passed": True, "mistake": None, "line": None},
        # Day -12
        {"days_ago": 12, "lesson": "two-pointers", "passed": False, "mistake": "loop_does_not_progress", "line": 22},
        {"days_ago": 12, "lesson": "two-pointers", "passed": True, "mistake": None, "line": None},
        # Day -11
        {"days_ago": 11, "lesson": "sliding-window", "passed": False, "mistake": "boundary_off_by_one", "line": 18},
        {"days_ago": 11, "lesson": "sliding-window", "passed": True, "mistake": None, "line": None},
        # Day -10
        {"days_ago": 10, "lesson": "stacks-queues", "passed": True, "mistake": None, "line": None},
        # Day -9
        {"days_ago": 9, "lesson": "linked-list-reversal", "passed": False, "mistake": "avoidable_nested_loops", "line": 31},
        {"days_ago": 9, "lesson": "linked-list-reversal", "passed": True, "mistake": None, "line": None},
        # Day -8
        {"days_ago": 8, "lesson": "hash-maps", "passed": True, "mistake": None, "line": None},
        # Day -7
        {"days_ago": 7, "lesson": "recursion-basics", "passed": False, "mistake": "base_cases", "line": 12},
        {"days_ago": 7, "lesson": "recursion-basics", "passed": True, "mistake": None, "line": None},
        # Day -6
        {"days_ago": 6, "lesson": "graph-bfs-dfs", "passed": False, "mistake": "loop_does_not_progress", "line": 27},
        {"days_ago": 6, "lesson": "graph-bfs-dfs", "passed": True, "mistake": None, "line": None},
        # Day -5
        {"days_ago": 5, "lesson": "dp-intro", "passed": False, "mistake": "base_cases", "line": 15},
        # Day -4
        {"days_ago": 4, "lesson": "url-shortener", "passed": False, "mistake": "rubric_gap_scaling", "line": 40},
        {"days_ago": 4, "lesson": "url-shortener", "passed": True, "mistake": None, "line": None},
        # Day -3
        {"days_ago": 3, "lesson": "rate-limiter", "passed": False, "mistake": "rubric_gap_data_model", "line": 52},
        {"days_ago": 3, "lesson": "rate-limiter", "passed": True, "mistake": None, "line": None},
        # Day -2
        {"days_ago": 2, "lesson": "binary-search", "passed": True, "mistake": None, "line": None},
        # Day -1
        {"days_ago": 1, "lesson": "dp-intro", "passed": False, "mistake": "base_cases", "line": 19},
        # Today
        {"days_ago": 0, "lesson": "dp-intro", "passed": True, "mistake": None, "line": None},
    ]

    for ev in history_events:
        d = now - timedelta(days=ev["days_ago"])
        ts = int(d.timestamp())
        date_str = d.strftime("%Y-%m-%d")
        attempts.append({
            "ts": ts,
            "date": date_str,
            "student_id": student_id,
            "lesson_id": ev["lesson"],
            "passed": ev["passed"],
            "mistake_id": ev["mistake"],
            "line": ev["line"],
        })

    mastery = {
        "array_indexing": 0.85,
        "loop_invariants": 0.78,
        "binary_search": 0.82,
        "two_pointers": 0.75,
        "sliding_window": 0.70,
        "recursion": 0.68,
        "base_cases": 0.65,
        "dp": 0.55,
        "data_modeling": 0.80,
        "scaling": 0.65,
        "rate_limiting": 0.72,
    }

    lessons = {
        "binary-search": "done",
        "two-pointers": "done",
        "sliding-window": "done",
        "stacks-queues": "done",
        "linked-list-reversal": "done",
        "hash-maps": "done",
        "recursion-basics": "done",
        "graph-bfs-dfs": "done",
        "dp-intro": "done",
        "url-shortener": "done",
        "rate-limiter": "done",
    }

    DATA_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "attempts": attempts,
        "mastery": mastery,
        "lessons": lessons,
        "updated_at": now.isoformat(),
    }
    DATA_STORE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("Wrote demo student history to %s", DATA_STORE_PATH)

    # Ingest concepts and attempts into FalkorDB if connected
    try:
        from adapters.graph_adapter import GraphAdapter
        g_adapter = GraphAdapter()
        g_adapter.ingest_concepts()
        g = g_adapter._get_graph()
        if g:
            log.info("FalkorDB detected! Seeding student graph nodes and mastery...")
            g.query("MERGE (s:Student {id: $sid}) SET s.name = 'Demo Student'", {"sid": student_id})
            for cid, score in mastery.items():
                g.query(
                    """
                    MATCH (s:Student {id: $sid})
                    MERGE (c:Concept {id: $cid})
                    MERGE (s)-[m:MASTERED]->(c)
                    SET m.score = $score, m.updated_at = $ts
                    """,
                    {"sid": student_id, "cid": cid, "score": score, "ts": int(time.time())},
                )
            log.info("FalkorDB graph successfully seeded.")
        else:
            log.info("FalkorDB offline; in-memory fallback cache will be used.")
    except Exception as e:
        log.warning("Could not seed FalkorDB directly (%s); cache is populated.", e)

    print(f"\n[OK] Successfully seeded student '{student_id}':")
    print(f"     * Streak: 14 consecutive days")
    print(f"     * Attempts: {len(attempts)} attempts across 11 lessons")
    print(f"     * Concepts Mastered: {len(mastery)} concepts (Total mastery: {sum(mastery.values()):.2f})")
    print(f"     * Evolution Stage: Master (Dragon)\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo student history")
    parser.add_argument("--student-id", default="local-user", help="Student ID to seed")
    args = parser.parse_args()
    seed_demo_student(args.student_id)
