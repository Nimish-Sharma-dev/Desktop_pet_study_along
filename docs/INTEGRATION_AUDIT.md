# Integration Audit Report: Socratic Code-Tutor Pet

## 1. Executive Summary

This audit assesses the integration boundaries between the four separate modules:
- **Module A**: Extension (VS Code / TypeScript) + Daemon (`app.py`, `routing.py`, `config.py`) + Voice
- **Module B**: Analysis (Tree-sitter, test runners, sandbox, guess-spam, rubric) + Lessons (`/lessons`)
- **Module C**: Graph (FalkorDB, schema, ingest, retrieval) + Tutor (Socratic engine, guard, Ollama)
- **Module D**: UI (Tauri + React, desktop pet, dashboard, live graph, inspector, command center)

The core contract specifications were evaluated against the implementation in each module. Key mismatches, missing endpoints/channels, and platform incompatibilities (particularly Windows vs Linux assumptions) were identified and cataloged below.

---

## 2. Contracts Matrix

| Contract | Description | Producer | Consumer | Status | Key Differences / Issues |
|---|---|---|---|---|---|
| **Contract 1** | Editor Event (`/ws/editor`) | Module A (`extension.ts`) | Module A (`daemon/routing.py`), Module B (`analysis`) | **MISMATCH** | • 1-based positions are used on wire; analysis expects clean line coordinates.<br>• Windows backslash paths in file paths require normalization against allowlist.<br>• Extension sends `diagnostics` and `file_open` action fields. |
| **Contract 2** | Test Result | Module B (`runners.run_tests`) | Module A (`daemon/app.py`, `routing.py`), Module C (`graph`) | **MISMATCH** | • `sandbox.py` imports Linux-only `resource` module, failing on Windows with `ModuleNotFoundError`.<br>• On test pass, daemon was omitting mastery update and attempt recording in graph.<br>• Result schema requires `lesson_id`, `language`, `duration_ms`, `results: [...]`, `all_passed`. |
| **Contract 3** | Finding | Module B (`analyze`, `score_design`) | Module A (`daemon/routing.py`), Module C (`tutor.handle`) | **MATCH (WITH ADAPTER)** | • Fields match (`kind`, `mistake_id`, `concept_ids`, `file`, `line`, `evidence`, `confidence`, `lesson_id`).<br>• Analysis emits `Finding` dataclass, whereas daemon & tutor expect dictionaries or Pydantic models.<br>• `score_design` emits rubric gaps as findings (`rubric_gap_<axis>`). |
| **Contract 4** | Tutor Output | Module C (`tutor.engine.handle`) | Module A (`daemon/routing.py`), Module D (`ui /ws/ui`) | **MISMATCH** | • Daemon's `_emit()` stripped `graph_trace` and `pet_state` from the `bubble` websocket frame.<br>• UI requires full `TutorOutput` inside every `bubble` payload for inspector drawer.<br>• `graph_trace.query_ms` must be real measured FalkorDB latency (not mock/fabricated).<br>• Guardrail in Module C had a regex defect failing on assignments starting with parenthesis `mid = (left + right) // 2`. |
| **Contract 5** | UI Websockets & REST | Module A (`daemon/app.py`), Module C (`graph`) | Module D (`ui/src/api`, `dashboard`) | **MISMATCH / MISSING** | • `mastery_update` channel sent full progress dict instead of `{concept_id, mastery, delta, evolution}`.<br>• `graph_update` channel omitted `highlight: {node_ids, edges, reason}`.<br>• `confetti` payload was `{lesson_id}` instead of `{reason, count}`.<br>• `review` channel and `GET /api/review` endpoint for system design radar were completely missing in daemon.<br>• `GET /api/progress` was not implemented in Module C (`graph.get_progress` missing).<br>• `GET /api/graph` snapshot was missing in Module C (`get_graph` returned FalkorDB graph object, not UI `{nodes, edges}` snapshot).<br>• Pet state `stressed` was not emitted by tutor engine during repeated mistakes.<br>• CORS required support for `tauri://localhost`, `http://tauri.localhost`, `https://tauri.localhost`. |
| **Contract 6** | `lesson.yaml` Format | Module B (`/lessons`) | Module A (`find_lesson`), Module B (`analyzer`), Module C (`ingest.py`) | **MISMATCH** | • `lesson.yaml` prerequisites list lesson IDs (e.g. `recursion-basics`), but `ingest_lesson` created `Concept` nodes for them.<br>• `concepts.yaml` was not ingested by `ingest_lesson`, breaking deep concept prerequisite chains (`(:Concept)-[:REQUIRES]->(:Concept)`).<br>• `ingest_lesson` in Module C expected `(graph, lesson_dir)` while daemon called `ingest_lesson(path)`. |

---

## 3. Specific Risk Points Audit

### 3.1 Field names, casing, and types
- **Editor Events**: Casing is camelCase/snake_case consistent with `type`, `ts`, `file`, `language`, `student_id`, `content`, `cursor`, `selection`, `diagnostics`. Line numbers are 1-based everywhere on the wire.
- **Findings**: `kind` in `('test_failure', 'diagnostic', 'pattern', 'guess_spam')`, `line` is integer (0 if unknown), `confidence` clamped to 0.0-1.0 float.
- **Tutor Output**: `question`, `hint_level` (0-4), `targets_concept`, `mistake_id`, `pet_state`, `graph_trace` (`cypher`, `query_ms`, `nodes`, `edges`).
- **Graph Trace**: Node schema `{id: string, label: string, props: dict}`, Edge schema `{from: string, to: string, type: string}`.

### 3.2 Mistake IDs Alignment
- Lessons declare 31 distinct mistake IDs in `common_mistakes` across 11 lessons.
- Analysis rules map AST and regex signals to lesson mistake IDs (`boundary_off_by_one`, `loop_does_not_progress`, `avoidable_nested_loops`, `rubric_gap_<axis>`, `guess_and_check`).
- FalkorDB `Mistake` nodes: Ingested dynamically from `lesson.yaml` common mistakes and seeded in `seed_data.py`. All IDs match snake_case conventions.

### 3.3 Concept IDs Alignment
- `concepts.yaml` defines 44 concepts covering DSA and System Design.
- Every concept referenced in `lesson.yaml` (`concepts` and `common_mistakes.concepts`) exists in `concepts.yaml`.
- **Mismatch**: `prerequisites` in `lesson.yaml` contains lesson IDs (e.g. `dp-intro` requires `recursion-basics`). An adapter is required during ingestion to link lesson-to-lesson dependencies and ingest `concepts.yaml` separately for concept-to-concept prerequisite traversal.

### 3.4 Pet State Names
- Valid state set across UI, Daemon, and Tutor: `idle`, `curious`, `thinking`, `asking`, `celebrating`, `sleeping`, `stressed`, `detective`.
- UI SVG assets in `public/media/` and character variants (`dragon`, `wizard`, `dragon-s3`, `wizard-s3`) include all 8 states.
- **Mismatch**: Module C `tutor/engine.py` only returned `asking` or `detective`. It never emitted `stressed` on repeated mistakes.

### 3.5 `/api/progress` Dashboard & Evolution Completeness
- Module D UI requires:
  - `streak`: `{ current, best }`
  - `daily_activity`: `[{ date, count }]`
  - `skill_radar`: `{ dsa: [...], system_design: [...] }`
  - `concepts`: `[{ id, name, track, mastery }]`
  - `recent_mistakes`: `[{ mistake_id, count, last_seen, concept_ids }]`
  - `patterns`: `[{ mistake_id, kind, count }]`
  - `hint_dependency`: `[{ date, avg_hint_level }]`
  - `lessons`: `[{ id, title, track, status, progress }]`
  - `recommended_next`: `{ lesson_id, reason }`
  - `spaced_repetition_due`: `[{ concept_id, due_at, interval_days }]`
  - `timeline`: `[{ ts, kind, label }]`
  - `evolution`: `{ stage, variant, stage_name, next_stage_name, progress, streak, mastery_total, next }`
- Module C had no implementation of `get_progress`. Daemon must assemble and compute this full structure from FalkorDB and persistent student metrics.

### 3.6 System Design Rubric Scorer & Radar Pipeline
- Module B provides `score_design(design_md, lesson) -> dict` returning `radar`, `axes`, `findings`.
- Module A daemon only processed code files and never routed `design.md` files through `score_design`.
- Daemon must intercept `design.md` edits/saves in system design lessons, invoke `score_design`, broadcast `review` message to `/ws/ui`, and forward rubric gap findings to `tutor.handle`.

### 3.7 Embedding Dimension Alignment
- `schema.py` vector index dimension: 768 (`cosine`).
- `ingest.py` Ollama model `nomic-embed-text`: 768.
- Deterministic mock embedding fallback: 768.
- Dimensions match across schema, ingestion, and search.

---

## 4. Remediation Strategy

1. **Canonical Schema (`/daemon/contracts.py`)**: Define canonical Pydantic v2 models for all contracts (EditorEvent, TestResult, Finding, TutorOutput, GraphTrace, GraphNode, GraphEdge, UiMessage, Progress, Evolution, Review).
2. **Adapter Layer (`/daemon/adapters/`)**:
   - `analysis_adapter.py`: Adapts `analyze`, `run_tests`, `score_design`, and handles Windows platform differences.
   - `graph_adapter.py`: Adapts `ingest_lesson` (supporting single `path` argument), ingests `concepts.yaml`, implements `get_progress` and `get_graph` snapshot for UI.
   - `tutor_adapter.py`: Adapts `tutor.handle`, ensures `stressed` state escalation on 3rd repeat, fixes guard assignment regex.
3. **Daemon Core Enhancements (`/daemon/routing.py`, `app.py`)**:
   - Emit full Contract 4 `TutorOutput` inside `bubble` websocket frame.
   - Implement `review` channel and `/api/review` endpoint.
   - Record attempts in FalkorDB on every finding, and update mastery on test pass.
   - Add outgoing bubble code safeguard.
