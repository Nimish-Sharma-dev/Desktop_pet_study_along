# Team C: FalkorDB Graph + RAG + Socratic Tutor Engine

Welcome to the **Team C** submodule documentation for the **Socratic Code-Tutor Pet**. Team C is responsible for student knowledge modeling, FalkorDB vector+graph persistence, curriculum ingestion, pedagogical hint-level decision policies, and the local Socratic dialogue engine.

---

## 1. Module Structure

```
daemon/
├── graph/
│   ├── __init__.py           # Unified exports for the graph subsystem
│   ├── schema.py             # FalkorDB connection client, unique constraints & HNSW vector index
│   ├── ingest.py             # Lesson/README ingestion, Ollama embeddings, attempt & mastery logging
│   └── retrieval.py          # Hybrid search, variable-length bottleneck queries, pattern memory
├── tutor/
│   ├── __init__.py           # Unified exports for the tutor subsystem
│   ├── guard.py              # Regex guardrails blocking code leaks, syntax, assignments & returns
│   └── engine.py             # Socratic dialogue engine, hint level policy & Ollama generation loop
├── seeds/
│   ├── __init__.py
│   └── seed_data.py          # Database seeding script for local development and demos
└── tests/
    ├── __init__.py
    ├── test_guard.py         # Pytest suite validating output guardrails
    └── test_queries.py       # Pytest suite validating bottleneck and pattern memory queries
```

---

## 2. Prerequisites & Setup

### 2.1 Services & Dependencies

1. **FalkorDB** (Graph + Vector database running locally on port `6379`):
   ```bash
   # Run via Docker
   docker run -p 6379:6379 -it --rm falkordb/falkordb:latest
   ```

2. **Ollama** (Local LLM and Embeddings running on port `11434`):
   ```bash
   # Install required models
   ollama pull qwen2.5-coder:7b
   ollama pull nomic-embed-text
   ```

3. **Python Environment**:
   ```bash
   pip install falkordb pyyaml pytest
   ```

---

## 3. Quick Start & Verification

### 3.1 Seed Demo Data
To initialize the schema, provision indexes, and populate a demo student profile (`local-user`):
```bash
python -m daemon.seeds.seed_data
```

### 3.2 Run Unit Tests
To verify output guardrails and graph traversal logic:
```bash
pytest daemon/tests -v
```

---

## 4. Raw Cypher Query Reference

### 4.1 Schema Constraints & Supporting Indexes
FalkorDB enforces uniqueness on node properties with supporting exact-match range indexes:

```cypher
// Supporting range indexes
CREATE INDEX FOR (s:Student) ON (s.id)
CREATE INDEX FOR (l:Lesson) ON (l.id)
CREATE INDEX FOR (c:Concept) ON (c.id)
CREATE INDEX FOR (m:Mistake) ON (m.id)

// Unique ID constraints
CREATE CONSTRAINT FOR (s:Student) REQUIRE s.id IS UNIQUE
CREATE CONSTRAINT FOR (l:Lesson) REQUIRE l.id IS UNIQUE
CREATE CONSTRAINT FOR (c:Concept) REQUIRE c.id IS UNIQUE
CREATE CONSTRAINT FOR (m:Mistake) REQUIRE m.id IS UNIQUE
```

### 4.2 HNSW Vector Index Creation
Vector index created on `(:Chunk)` nodes on property `embedding` (768 dimensions, cosine similarity):

```cypher
CREATE VECTOR INDEX FOR (c:Chunk) ON (c.embedding)
OPTIONS {dimension: 768, similarityFunction: 'cosine'}
```

### 4.3 Hybrid Search Query (Vector Index + Graph Filtering)
Combines vector nearest-neighbor search (`db.idx.vector.queryNodes`) with Cypher relationship traversals to filter chunks explaining concepts where the student's mastery score is weak (`score < 0.6` or unattempted):

```cypher
CALL db.idx.vector.queryNodes('Chunk', 'embedding', $top_k, vecf32($query_embedding))
YIELD node AS chunk, score
MATCH (chunk)-[:EXPLAINS]->(lesson:Lesson)
MATCH (failed:Concept {id: $failed_concept_id})
OPTIONAL MATCH (failed)-[:REQUIRES*1..3]->(prereq:Concept)
OPTIONAL MATCH (lesson)-[:TEACHES]->(targetConcept:Concept)
WITH chunk, score, lesson, failed,
     coalesce(prereq, targetConcept, failed) AS concept
OPTIONAL MATCH (s:Student {id: $student_id})-[m:MASTERED]->(concept)
WHERE (m.score IS NULL OR m.score < $threshold)
RETURN chunk, score, lesson, concept, coalesce(m.score, 0.0) AS mastery_score
ORDER BY score ASC
LIMIT $top_k
```

### 4.4 Variable-Length Bottleneck Path Query (`REQUIRES*1..3`)
Traverses backward along concept prerequisite chains to find the foundational root concept causing the student's failure:

```cypher
MATCH path = (failed:Concept {id: $failed_concept_id})-[:REQUIRES*1..3]->(root:Concept)
WHERE NOT (root)-[:REQUIRES]->(:Concept)
RETURN root, length(path) AS depth, nodes(path) AS path_nodes
ORDER BY depth DESC
LIMIT 1
```

### 4.5 Pattern Memory Query (Mistake Recurrence)
Aggregates a student's attempt history to track how frequently a specific mistake has occurred:

```cypher
MATCH (s:Student {id: $student_id})-[:ATTEMPTED]->(a:Attempt)-[:MADE_MISTAKE]->(m:Mistake {id: $mistake_id})
OPTIONAL MATCH (a)-[:FOR_LESSON]->(l:Lesson)
RETURN count(a) AS recurrence_count,
       collect(a.timestamp) AS timestamps,
       collect(DISTINCT l.id) AS lessons
```

### 4.6 Student Attempt Logging
Logs an attempt and associates it with the lesson and any observed mistake:

```cypher
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
WITH a
MERGE (m:Mistake {id: $mistake_id})
CREATE (a)-[:MADE_MISTAKE]->(m)
```

### 4.7 Bayesian/Elo Mastery & Forgetting Curve Schedule
Updates mastery state and records the next spaced-repetition due timestamp:

```cypher
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
```

---

## 5. Pedagogical Hint Level & Guardrails Policy

### 5.1 Progressive Hint Levels (0 to 4)
* **Level 0 (Metacognitive Pause)**: High-level question asking the student to reflect on their hypothesis or preconditions. **`guess_spam` always receives L0.**
* **Level 1 (Concept/Invariant)**: Question regarding the loop invariant or theoretical property.
* **Level 2 (Focus Redirection)**: Directs attention to the specific boundary condition, pointer, or check.
* **Level 3 (Edge Case Inquiry)**: Questions behavior on small or boundary inputs (e.g., single-element array, empty list).
* **Level 4 (Trace Walkthrough)**: Step-by-step trace inquiry of the failing execution case.

### 5.2 Strict Guardrail Rules ([`guard.py`](daemon/tutor/guard.py))
All LLM output from `qwen2.5-coder:7b` must pass regex validation:
1. **No Code Fences**: Any occurrence of ` ``` ` triggers immediate rejection.
2. **No Direct Fix Directives**: Imperative directives (`"change X to Y"`, `"replace X with Y"`, `"use X instead of Y"`, `"set X to Y"`) are blocked.
3. **No Assignments or Declarations**: Blocks programmatic assignments (`x = ...`, `let y = ...`, `i += 1`).
4. **No Return Statements**: Blocks code returns (`return -1`, `return None`).

If rejected, the tutor engine provides feedback to the model across **up to 3 retries**, ultimately falling back to a pre-validated Socratic seed question.

---

## 6. Contract Compliance

### Input: Contract 3 (`Finding` from Team B)
```json
{
  "kind": "test_failure|diagnostic|pattern|guess_spam",
  "mistake_id": "boundary_off_by_one",
  "concept_ids": ["array_indexing"],
  "file": "path/to/solution.py",
  "line": 14,
  "evidence": "single-element test raised IndexError",
  "confidence": 0.95,
  "lesson_id": "binary-search"
}
```

### Output: Contract 4 (`TutorOutput` to Team D)
```json
{
  "question": "What happens when the search space reduces to left == right?",
  "hint_level": 2,
  "targets_concept": "array_indexing",
  "mistake_id": "boundary_off_by_one",
  "pet_state": "asking",
  "graph_trace": {
    "cypher": "CALL db.idx.vector.queryNodes('Chunk', 'embedding', 3, vecf32($query_embedding)) ...",
    "query_ms": 3.2,
    "nodes": [
      {"id": "binary-search_chunk_0", "label": "Chunk", "props": {"lesson_id": "binary-search"}},
      {"id": "binary-search", "label": "Lesson", "props": {"title": "Binary Search"}},
      {"id": "array_indexing", "label": "Concept", "props": {"id": "array_indexing"}}
    ],
    "edges": [
      {"from": "binary-search_chunk_0", "to": "binary-search", "type": "EXPLAINS"},
      {"from": "binary-search", "to": "array_indexing", "type": "REQUIRES"}
    ]
  }
}
```
