"""
Lesson ingestion, attempt logging, and spaced-repetition mastery scoring for Team C.

This module provides:
1. `embed_text`: Vector embedding generation via Ollama (nomic-embed-text, 768-dim).
2. `ingest_lesson`: Ingests lesson.yaml and README.md into FalkorDB with full relationship graph.
3. `record_attempt`: Logs student attempts, associating with lessons and mistakes.
4. `update_mastery`: Bayesian/Elo-style mastery scoring and spaced-repetition due dates.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

try:
    from falkordb import Graph
except ImportError:
    Graph = Any  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_EMBED_DIM = 768

# Mastery rule constants
MASTERY_PASS_DELTA = 0.10
MASTERY_FAIL_DELTA = -0.15
MASTERY_MIN = 0.0
MASTERY_MAX = 1.0
MASTERY_DEFAULT = 0.5


def _generate_mock_embedding(text: str, dim: int = DEFAULT_EMBED_DIM) -> List[float]:
    """Generate a deterministic normalized unit vector for mock/fallback embedding."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [round(x / norm, 6) for x in raw]


def embed_text(
    text: str,
    model: str = DEFAULT_EMBED_MODEL,
    ollama_url: str = OLLAMA_EMBED_URL,
    timeout: float = 10.0,
    fallback_to_mock: bool = True,
) -> List[float]:
    """
    Generate a 768-dimensional vector embedding for text using Ollama.

    Args:
        text: Input text string to embed.
        model: Embedding model name on Ollama (default: "nomic-embed-text").
        ollama_url: URL for Ollama embedding endpoint (default: "http://localhost:11434/api/embeddings").
        timeout: HTTP timeout in seconds (default: 10.0).
        fallback_to_mock: If True and Ollama is unreachable, returns a deterministic
                          unit vector to prevent blocking offline/test execution.

    Returns:
        List of 768 float values representing the embedding vector.
    """
    clean_text = text.strip()
    if not clean_text:
        return [0.0] * DEFAULT_EMBED_DIM

    payload = json.dumps({"model": model, "prompt": clean_text}).encode("utf-8")
    req = urllib.request.Request(
        ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
            embedding = result.get("embedding")
            if not embedding and "embeddings" in result:
                embedding = result["embeddings"][0]
            if embedding and isinstance(embedding, list):
                return [float(v) for v in embedding]
            raise ValueError(f"Unexpected response structure from Ollama: {result.keys()}")
    except Exception as e:
        if fallback_to_mock:
            logger.warning("Ollama unavailable at %s (%s). Using deterministic mock embedding.", ollama_url, e)
            return _generate_mock_embedding(clean_text, DEFAULT_EMBED_DIM)
        raise ConnectionError(f"Failed to generate embedding from Ollama at {ollama_url}: {e}") from e


def _chunk_text(text: str, max_chars: int = 500, overlap_chars: int = 50) -> List[str]:
    """Split markdown text into coherent chunks based on headers or paragraphs."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        para_len = len(para_clean)
        if current_len + para_len > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            # Keep overlap if possible
            if overlap_chars > 0 and len(current_chunk[-1]) <= overlap_chars:
                current_chunk = [current_chunk[-1], para_clean]
                current_len = len(current_chunk[0]) + para_len
            else:
                current_chunk = [para_clean]
                current_len = para_len
        else:
            current_chunk.append(para_clean)
            current_len += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks or [text.strip()]


def _parse_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Parse YAML with standard pyyaml or simple regex-based fallback."""
    raw_content = file_path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(raw_content) or {}

    # Basic fallback parser if pyyaml is not yet installed in local environment
    logger.warning("PyYAML not found, using lightweight fallback parser for %s", file_path)
    data: Dict[str, Any] = {}
    current_list_key: Optional[str] = None

    for line in raw_content.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            continue
        if ":" in line_clean and not line_clean.startswith("-"):
            key, val = line_clean.split(":", 1)
            key = key.strip()
            val = val.strip()
            if not val:
                current_list_key = key
                data[current_list_key] = []
            elif val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                data[key] = items
                current_list_key = None
            else:
                val_unquoted = val.strip("'\"")
                if val_unquoted.isdigit():
                    data[key] = int(val_unquoted)
                else:
                    data[key] = val_unquoted
                current_list_key = None
        elif line_clean.startswith("-") and current_list_key:
            item = line_clean[1:].strip().strip("'\"")
            data[current_list_key].append(item)

    return data


def ingest_lesson(graph: Graph, lesson_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    Ingest a lesson package into FalkorDB.

    Reads `lesson.yaml` and `README.md`, chunks the README text, embeds each chunk,
    and stores Lesson, Concept, Prerequisite, Mistake, and Chunk nodes with proper relationships:
      - (Lesson)-[:TEACHES]->(Concept)
      - (Lesson)-[:REQUIRES]->(Concept)
      - (Mistake)-[:INVOLVES]->(Concept)
      - (Chunk)-[:EXPLAINS]->(Lesson)

    Args:
        graph: FalkorDB Graph instance.
        lesson_dir: Directory containing lesson.yaml and optional README.md,
                    or direct path to lesson.yaml.

    Returns:
        Summary dictionary of ingested entities and counts.
    """
    dir_path = Path(lesson_dir)
    if dir_path.is_file():
        yaml_path = dir_path
        base_dir = dir_path.parent
    else:
        yaml_path = dir_path / "lesson.yaml"
        base_dir = dir_path

    if not yaml_path.exists():
        raise FileNotFoundError(f"Lesson configuration not found at {yaml_path}")

    manifest = _parse_yaml_file(yaml_path)
    lesson_id = manifest.get("id")
    if not lesson_id:
        raise ValueError(f"lesson.yaml at {yaml_path} is missing required 'id' attribute")

    title = manifest.get("title", lesson_id)
    track = manifest.get("track", "dsa")
    difficulty = manifest.get("difficulty", "easy")
    estimated_minutes = int(manifest.get("estimated_minutes", 15))
    languages = manifest.get("languages", ["python"])
    concepts: List[str] = manifest.get("concepts", [])
    prerequisites: List[str] = manifest.get("prerequisites", [])
    common_mistakes: List[Dict[str, Any]] = manifest.get("common_mistakes", [])

    summary: Dict[str, Any] = {
        "lesson_id": lesson_id,
        "title": title,
        "concepts": concepts,
        "prerequisites": prerequisites,
        "mistakes": [],
        "chunks_created": 0,
    }

    # 1. Create or merge Lesson node
    graph.query(
        """
        MERGE (l:Lesson {id: $lesson_id})
        SET l.title = $title,
            l.track = $track,
            l.difficulty = $difficulty,
            l.estimated_minutes = $estimated_minutes,
            l.languages = $languages
        """,
        {
            "lesson_id": lesson_id,
            "title": title,
            "track": track,
            "difficulty": difficulty,
            "estimated_minutes": estimated_minutes,
            "languages": languages,
        },
    )

    # 2. Ingest concepts and (Lesson)-[:TEACHES]->(Concept)
    for cid in concepts:
        graph.query(
            """
            MERGE (c:Concept {id: $concept_id})
            WITH c
            MATCH (l:Lesson {id: $lesson_id})
            MERGE (l)-[:TEACHES]->(c)
            """,
            {"concept_id": cid, "lesson_id": lesson_id},
        )

    # 3. Ingest prerequisites and (Lesson)-[:REQUIRES]->(Concept)
    for pid in prerequisites:
        graph.query(
            """
            MERGE (p:Concept {id: $prereq_id})
            WITH p
            MATCH (l:Lesson {id: $lesson_id})
            MERGE (l)-[:REQUIRES]->(p)
            """,
            {"prereq_id": pid, "lesson_id": lesson_id},
        )
        # Also link taught concepts directly to their prerequisite concepts
        for cid in concepts:
            graph.query(
                """
                MERGE (c:Concept {id: $concept_id})
                MERGE (p:Concept {id: $prereq_id})
                MERGE (c)-[:REQUIRES]->(p)
                """,
                {"concept_id": cid, "prereq_id": pid},
            )

    # 4. Ingest common mistakes and (Mistake)-[:INVOLVES]->(Concept)
    for mistake in common_mistakes:
        if isinstance(mistake, dict):
            mid = mistake.get("id")
            m_concepts = mistake.get("concepts", [])
            signals = mistake.get("signals", [])
            seed_questions = mistake.get("seed_questions", [])
        else:
            mid = str(mistake)
            m_concepts = []
            signals = []
            seed_questions = []

        if not mid:
            continue

        graph.query(
            """
            MERGE (m:Mistake {id: $mistake_id})
            SET m.signals = $signals,
                m.seed_questions = $seed_questions
            """,
            {"mistake_id": mid, "signals": signals, "seed_questions": seed_questions},
        )
        summary["mistakes"].append(mid)

        for mc in m_concepts:
            graph.query(
                """
                MERGE (c:Concept {id: $concept_id})
                WITH c
                MATCH (m:Mistake {id: $mistake_id})
                MERGE (m)-[:INVOLVES]->(c)
                """,
                {"concept_id": mc, "mistake_id": mid},
            )

    # 5. Ingest README.md chunks and (Chunk)-[:EXPLAINS]->(Lesson)
    readme_path = base_dir / "README.md"
    readme_content = ""
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8")
    elif "description" in manifest:
        readme_content = manifest["description"]

    if readme_content:
        chunks = _chunk_text(readme_content)
        for idx, chunk_text in enumerate(chunks):
            chunk_id = f"{lesson_id}_chunk_{idx}"
            embedding = embed_text(chunk_text)

            # Insert chunk with vector embedding and EXPLAINS relationship
            try:
                graph.query(
                    """
                    MERGE (ch:Chunk {id: $chunk_id})
                    SET ch.content = $content,
                        ch.lesson_id = $lesson_id,
                        ch.chunk_index = $chunk_index,
                        ch.embedding = vecf32($embedding)
                    WITH ch
                    MATCH (l:Lesson {id: $lesson_id})
                    MERGE (ch)-[:EXPLAINS]->(l)
                    """,
                    {
                        "chunk_id": chunk_id,
                        "content": chunk_text,
                        "lesson_id": lesson_id,
                        "chunk_index": idx,
                        "embedding": embedding,
                    },
                )
                summary["chunks_created"] += 1
            except Exception as e:
                # Fallback without vecf32 if vector engine module is in scalar compatibility mode
                logger.warning("Falling back to standard attribute insertion for chunk %s: %s", chunk_id, e)
                graph.query(
                    """
                    MERGE (ch:Chunk {id: $chunk_id})
                    SET ch.content = $content,
                        ch.lesson_id = $lesson_id,
                        ch.chunk_index = $chunk_index
                    WITH ch
                    MATCH (l:Lesson {id: $lesson_id})
                    MERGE (ch)-[:EXPLAINS]->(l)
                    """,
                    {
                        "chunk_id": chunk_id,
                        "content": chunk_text,
                        "lesson_id": lesson_id,
                        "chunk_index": idx,
                    },
                )
                summary["chunks_created"] += 1

    logger.info("Successfully ingested lesson '%s' with %d chunks", lesson_id, summary["chunks_created"])
    return summary


def record_attempt(
    graph: Graph,
    student_id: str,
    lesson_id: str,
    passed: bool,
    mistake_id: Optional[str] = None,
    timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Log a student's attempt and link it to the lesson and any observed mistake.

    Relationships:
      - (Student)-[:ATTEMPTED]->(Attempt)
      - (Attempt)-[:FOR_LESSON]->(Lesson)
      - (Attempt)-[:MADE_MISTAKE]->(Mistake) (if mistake_id provided)

    Args:
        graph: FalkorDB Graph instance.
        student_id: Identifier of the student.
        lesson_id: Identifier of the lesson attempted.
        passed: Boolean indicating whether test suite passed.
        mistake_id: Optional mistake identifier detected during attempt.
        timestamp: Epoch timestamp in seconds (default: current time).

    Returns:
        Dictionary record of the logged attempt.
    """
    ts = timestamp if timestamp is not None else int(time.time())
    attempt_id = f"att_{student_id}_{lesson_id}_{int(ts * 1000)}"

    query = """
    MERGE (s:Student {id: $student_id})
    MERGE (l:Lesson {id: $lesson_id})
    CREATE (a:Attempt {
        id: $attempt_id,
        student_id: $student_id,
        lesson_id: $lesson_id,
        passed: $passed,
        timestamp: $timestamp
    })
    CREATE (s)-[:ATTEMPTED]->(a)
    CREATE (a)-[:FOR_LESSON]->(l)
    """
    params: Dict[str, Any] = {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "attempt_id": attempt_id,
        "passed": bool(passed),
        "timestamp": ts,
    }

    if mistake_id:
        query += """
        WITH a
        MERGE (m:Mistake {id: $mistake_id})
        CREATE (a)-[:MADE_MISTAKE]->(m)
        """
        params["mistake_id"] = mistake_id

    graph.query(query, params)
    logger.debug("Recorded attempt %s for student %s on lesson %s (passed=%s)", attempt_id, student_id, lesson_id, passed)

    return {
        "attempt_id": attempt_id,
        "student_id": student_id,
        "lesson_id": lesson_id,
        "passed": passed,
        "mistake_id": mistake_id,
        "timestamp": ts,
    }


def calculate_forgetting_curve_due_date(
    mastery_score: float,
    streak: int,
    current_ts: Optional[int] = None,
) -> Tuple[int, float]:
    """
    Calculate spaced-repetition due date based on the Ebbinghaus forgetting curve.

    Higher mastery and longer positive streaks expand the recall retention window.
    Lower mastery (<0.2) requires immediate re-checking (1-2 hours).

    Args:
        mastery_score: Current mastery score clamped between 0.0 and 1.0.
        streak: Consecutive successful recall streak.
        current_ts: Base timestamp (default: current epoch).

    Returns:
        (due_timestamp_seconds, interval_in_hours)
    """
    if current_ts is None:
        current_ts = int(time.time())

    if mastery_score <= 0.2:
        interval_hours = 1.0 + (mastery_score * 5.0)
    else:
        # Exponential curve scaling up to days based on memory stability
        base_days = (mastery_score ** 1.8) * (1.3 ** min(streak, 6))
        interval_hours = base_days * 24.0

    # Clamp between 1 hour and 720 hours (30 days)
    interval_hours = max(1.0, min(720.0, round(interval_hours, 2)))
    due_ts = current_ts + int(interval_hours * 3600)
    return due_ts, interval_hours


def update_mastery(
    graph: Graph,
    student_id: str,
    concept_id: str,
    passed: bool,
    current_ts: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update a student's concept mastery score and spaced-repetition schedule.

    Applies Bayesian/Elo-style delta:
      - +0.10 for pass
      - -0.15 for fail
      - Clamped between [0.0, 1.0]

    Calculates next review due date from memory stability forgetting curve.

    Args:
        graph: FalkorDB Graph instance.
        student_id: Identifier of the student.
        concept_id: Identifier of the concept being evaluated.
        passed: True if the student demonstrated mastery, False otherwise.
        current_ts: Optional timestamp override.

    Returns:
        Updated mastery profile for the student and concept.
    """
    now = current_ts if current_ts is not None else int(time.time())

    # Step 1: Fetch current mastery state if already present
    fetch_query = """
    MATCH (s:Student {id: $student_id})-[r:MASTERED]->(c:Concept {id: $concept_id})
    RETURN r.score AS score, r.streak AS streak, r.review_count AS review_count
    """
    res = graph.query(fetch_query, {"student_id": student_id, "concept_id": concept_id})

    current_score = MASTERY_DEFAULT
    current_streak = 0
    review_count = 0

    if getattr(res, "result_set", None) and len(res.result_set) > 0:
        row = res.result_set[0]
        current_score = float(row[0]) if row[0] is not None else MASTERY_DEFAULT
        current_streak = int(row[1]) if row[1] is not None else 0
        review_count = int(row[2]) if row[2] is not None else 0

    # Step 2: Apply Bayesian/Elo-style delta update
    delta = MASTERY_PASS_DELTA if passed else MASTERY_FAIL_DELTA
    new_score = round(max(MASTERY_MIN, min(MASTERY_MAX, current_score + delta)), 4)
    new_streak = current_streak + 1 if passed else 0
    new_review_count = review_count + 1

    # Step 3: Compute spaced-repetition due date using forgetting curve
    due_date, interval_hours = calculate_forgetting_curve_due_date(new_score, new_streak, now)

    # Step 4: Persist updated state on (Student)-[:MASTERED]->(Concept)
    upsert_query = """
    MERGE (s:Student {id: $student_id})
    MERGE (c:Concept {id: $concept_id})
    MERGE (s)-[r:MASTERED]->(c)
    SET r.score = $score,
        r.streak = $streak,
        r.review_count = $review_count,
        r.last_reviewed = $last_reviewed,
        r.due_date = $due_date,
        r.interval_hours = $interval_hours,
        r.last_passed = $passed
    """
    graph.query(
        upsert_query,
        {
            "student_id": student_id,
            "concept_id": concept_id,
            "score": new_score,
            "streak": new_streak,
            "review_count": new_review_count,
            "last_reviewed": now,
            "due_date": due_date,
            "interval_hours": interval_hours,
            "passed": bool(passed),
        },
    )

    logger.debug(
        "Updated mastery for student %s on concept %s: %f -> %f (due in %s hours)",
        student_id,
        concept_id,
        current_score,
        new_score,
        interval_hours,
    )

    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "passed": passed,
        "previous_score": current_score,
        "mastery_score": new_score,
        "delta": delta,
        "streak": new_streak,
        "review_count": new_review_count,
        "interval_hours": interval_hours,
        "due_date": due_date,
    }
