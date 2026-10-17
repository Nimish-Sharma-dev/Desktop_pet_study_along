"""
Demo seed data generation script for Socratic Code-Tutor Pet (Team C).

Initializes:
1. Schema constraints and indexes in FalkorDB.
2. Demo curriculum concepts, lessons, prerequisites, and mistakes.
3. Demo student profile (`local-user`).
4. Initial mastery scores and spaced-repetition schedules.
5. Sample historical failed attempts demonstrating mistake recurrence.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure repository root is on Python module search path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from daemon.graph.ingest import (
    embed_text,
    record_attempt,
    update_mastery,
)
from daemon.graph.schema import (
    DEFAULT_GRAPH_NAME,
    DEFAULT_HOST,
    DEFAULT_PORT,
    get_client,
    get_graph,
    init_schema,
)

logger = logging.getLogger(__name__)


def seed_database(graph_name: str = DEFAULT_GRAPH_NAME) -> Dict[str, Any]:
    """
    Seed FalkorDB with demo student history, lessons, concepts, and attempts.

    Returns:
        Summary dictionary of seeded records.
    """
    logger.info("Connecting to FalkorDB on %s:%s...", DEFAULT_HOST, DEFAULT_PORT)
    client = get_client(host=DEFAULT_HOST, port=DEFAULT_PORT)
    graph = get_graph(client, graph_name=graph_name)

    # 1. Initialize FalkorDB schema & constraints
    logger.info("Initializing schema constraints and vector indexes...")
    schema_summary = init_schema(graph)

    # 2. Seed Core Concepts and Dependencies (Variables -> Array Indexing -> Binary Search)
    logger.info("Seeding concepts and prerequisite dependency graph...")
    concepts = [
        {"id": "variables", "name": "Variable Assignment & Arithmetic"},
        {"id": "array_indexing", "name": "Array Offsets & Index Boundaries"},
        {"id": "pointers", "name": "Two-Pointer Navigation"},
        {"id": "loop_invariants", "name": "Loop Invariants & Halting Conditions"},
        {"id": "binary_search", "name": "Binary Search Algorithm"},
        {"id": "divide_and_conquer", "name": "Divide and Conquer Technique"},
    ]

    for c in concepts:
        graph.query(
            "MERGE (c:Concept {id: $id}) SET c.name = $name",
            {"id": c["id"], "name": c["name"]},
        )

    # Concept prerequisite chains:
    # binary_search -> REQUIRES -> array_indexing -> REQUIRES -> variables
    dependencies = [
        ("binary_search", "array_indexing"),
        ("binary_search", "loop_invariants"),
        ("binary_search", "divide_and_conquer"),
        ("array_indexing", "variables"),
        ("pointers", "variables"),
    ]

    for source, target in dependencies:
        graph.query(
            """
            MATCH (s:Concept {id: $source}), (t:Concept {id: $target})
            MERGE (s)-[:REQUIRES]->(t)
            """,
            {"source": source, "target": target},
        )

    # 3. Seed Lessons & Relationships
    logger.info("Seeding lesson packages and conceptual links...")
    lessons = [
        {
            "id": "binary-search",
            "title": "Binary Search",
            "track": "dsa",
            "difficulty": "easy",
            "estimated_minutes": 20,
            "languages": ["python", "java", "cpp"],
            "teaches": ["binary_search", "loop_invariants", "divide_and_conquer"],
            "requires": ["array_indexing"],
        },
        {
            "id": "array-basics",
            "title": "Array Indexing Basics",
            "track": "dsa",
            "difficulty": "easy",
            "estimated_minutes": 15,
            "languages": ["python", "java"],
            "teaches": ["array_indexing", "pointers"],
            "requires": ["variables"],
        },
    ]

    for l in lessons:
        graph.query(
            """
            MERGE (lesson:Lesson {id: $id})
            SET lesson.title = $title,
                lesson.track = $track,
                lesson.difficulty = $difficulty,
                lesson.estimated_minutes = $estimated_minutes,
                lesson.languages = $languages
            """,
            {
                "id": l["id"],
                "title": l["title"],
                "track": l["track"],
                "difficulty": l["difficulty"],
                "estimated_minutes": l["estimated_minutes"],
                "languages": l["languages"],
            },
        )

        for tid in l["teaches"]:
            graph.query(
                """
                MATCH (lesson:Lesson {id: $lid}), (c:Concept {id: $cid})
                MERGE (lesson)-[:TEACHES]->(c)
                """,
                {"lid": l["id"], "cid": tid},
            )

        for rid in l["requires"]:
            graph.query(
                """
                MATCH (lesson:Lesson {id: $lid}), (p:Concept {id: $pid})
                MERGE (lesson)-[:REQUIRES]->(p)
                """,
                {"lid": l["id"], "pid": rid},
            )

    # 4. Seed Common Mistakes & Seed Questions
    logger.info("Seeding common pedagogical mistakes...")
    mistakes = [
        {
            "id": "boundary_off_by_one",
            "concepts": ["array_indexing", "binary_search"],
            "signals": ["IndexError", "wrong_element", "single_element_fail"],
            "seed_questions": [
                "What happens when left == right?",
                "Which index represents the final valid element?",
            ],
        },
        {
            "id": "infinite_loop",
            "concepts": ["loop_invariants"],
            "signals": ["TimeoutError", "loop_hang"],
            "seed_questions": [
                "How does each step guarantee progress towards the termination condition?",
            ],
        },
    ]

    for m in mistakes:
        graph.query(
            """
            MERGE (mistake:Mistake {id: $id})
            SET mistake.signals = $signals,
                mistake.seed_questions = $seed_questions
            """,
            {
                "id": m["id"],
                "signals": m["signals"],
                "seed_questions": m["seed_questions"],
            },
        )

        for cid in m["concepts"]:
            graph.query(
                """
                MATCH (mistake:Mistake {id: $mid}), (c:Concept {id: $cid})
                MERGE (mistake)-[:INVOLVES]->(c)
                """,
                {"mid": m["id"], "cid": cid},
            )

    # 5. Seed Explanatory Chunks with Vector Embeddings
    logger.info("Seeding explanation chunks with embeddings...")
    chunks = [
        {
            "id": "binary-search_chunk_0",
            "lesson_id": "binary-search",
            "content": (
                "Binary search repeatedly divides the search interval in half. "
                "The loop invariant requires that if the target exists, it must lie within the range [left, right]. "
                "When left == right, a single candidate remains to be evaluated."
            ),
        },
        {
            "id": "binary-search_chunk_1",
            "lesson_id": "binary-search",
            "content": (
                "A common boundary error occurs when calculating mid = (left + right) // 2. "
                "If the update condition fails to advance left = mid + 1 or right = mid - 1, "
                "the search window will stop shrinking, resulting in an infinite loop."
            ),
        },
        {
            "id": "array-basics_chunk_0",
            "lesson_id": "array-basics",
            "content": (
                "Arrays in zero-indexed languages have valid indices ranging from 0 to N-1. "
                "Accessing index N triggers an out-of-bounds IndexError."
            ),
        },
    ]

    for idx, ch in enumerate(chunks):
        emb = embed_text(ch["content"])
        try:
            graph.query(
                """
                MERGE (chunk:Chunk {id: $id})
                SET chunk.content = $content,
                    chunk.lesson_id = $lesson_id,
                    chunk.chunk_index = $idx,
                    chunk.embedding = vecf32($embedding)
                WITH chunk
                MATCH (l:Lesson {id: $lesson_id})
                MERGE (chunk)-[:EXPLAINS]->(l)
                """,
                {
                    "id": ch["id"],
                    "content": ch["content"],
                    "lesson_id": ch["lesson_id"],
                    "idx": idx,
                    "embedding": emb,
                },
            )
        except Exception:
            # Fallback without vecf32 procedure if vector module is unavailable
            graph.query(
                """
                MERGE (chunk:Chunk {id: $id})
                SET chunk.content = $content,
                    chunk.lesson_id = $lesson_id,
                    chunk.chunk_index = $idx
                WITH chunk
                MATCH (l:Lesson {id: $lesson_id})
                MERGE (chunk)-[:EXPLAINS]->(l)
                """,
                {
                    "id": ch["id"],
                    "content": ch["content"],
                    "lesson_id": ch["lesson_id"],
                    "idx": idx,
                },
            )

    # 6. Seed Demo Student
    student_id = "local-user"
    logger.info("Seeding demo student '%s'...", student_id)
    graph.query(
        "MERGE (s:Student {id: $student_id}) SET s.name = $name",
        {"student_id": student_id, "name": "Local Developer"},
    )

    # 7. Seed Initial Mastery Scores
    # Student has strong fundamentals in variables, but weak scores in array indexing & binary search
    logger.info("Setting initial mastery scores for %s...", student_id)
    # Passed variables multiple times (mastery ~0.90)
    update_mastery(graph, student_id, "variables", passed=True)
    update_mastery(graph, student_id, "variables", passed=True)
    update_mastery(graph, student_id, "variables", passed=True)
    update_mastery(graph, student_id, "variables", passed=True)

    # Struggled with array indexing (mastery ~0.35, below 0.6 weak threshold)
    update_mastery(graph, student_id, "array_indexing", passed=False)

    # Struggled with loop invariants & binary search
    update_mastery(graph, student_id, "loop_invariants", passed=False)
    update_mastery(graph, student_id, "binary_search", passed=False)

    # 8. Log Historical Failed Attempts (Recurring mistake: boundary_off_by_one)
    logger.info("Logging sample failed attempts...")
    att1 = record_attempt(
        graph,
        student_id=student_id,
        lesson_id="binary-search",
        passed=False,
        mistake_id="boundary_off_by_one",
    )
    att2 = record_attempt(
        graph,
        student_id=student_id,
        lesson_id="binary-search",
        passed=False,
        mistake_id="boundary_off_by_one",
    )
    att3 = record_attempt(
        graph,
        student_id=student_id,
        lesson_id="binary-search",
        passed=False,
        mistake_id="infinite_loop",
    )

    summary = {
        "status": "success",
        "graph_name": graph_name,
        "schema": schema_summary,
        "student_id": student_id,
        "concepts_seeded": len(concepts),
        "lessons_seeded": len(lessons),
        "mistakes_seeded": len(mistakes),
        "chunks_seeded": len(chunks),
        "attempts_logged": [att1["attempt_id"], att2["attempt_id"], att3["attempt_id"]],
    }

    logger.info("Database seeding successfully completed!")
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        res = seed_database()
        print("\nSeed Data Summary:")
        for k, v in res.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"\nFailed to seed database: {e}")
        print("Ensure FalkorDB is running on localhost:6379.")
