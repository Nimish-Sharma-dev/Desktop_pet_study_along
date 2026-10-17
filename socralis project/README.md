# Socratic Code-Tutor Pet

A desktop pet that watches a student's VS Code work live, remembers their history in FalkorDB (graph + vector), and teaches DSA and system design by asking guiding questions—never by giving the fix. Works for any programming language and runs completely locally.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   VS Code Extension (A)     |
                      |   Captures editor buffer &  |
                      |   diagnostics over WS       |
                      +--------------+--------------+
                                     | Contract 1 (/ws/editor)
                                     v
                      +-----------------------------+
                      |   Core Daemon :7777 (A)     |
                      |   FastAPI router & dispatch |
                      +-------+-------------+-------+
                              |             |
        Contract 2/3 (Finding)|             | Contract 5 (/ws/ui)
                              v             v
       +-----------------------------+   +-----------------------------+
       | Code Analysis & Sandbox (B) |   | Pet Desktop Widget & UI (D) |
       | AST, tests & lesson packs   |   | Tauri + React + Live Graph  |
       +--------------+--------------+   +-----------------------------+
                      |
                      | Finding
                      v
       +---------------------------------------------+
       | Team C: FalkorDB Graph + Tutor Engine       |
       | - FalkorDB Knowledge Graph + Vector HNSW    |
       | - Progressive Hint Escalation (L0 - L4)     |
       | - Socratic Dialogue (qwen2.5-coder:7b)      |
       | - Regex Guardrails & Seed Fallbacks         |
       +---------------------------------------------+
```

---

## Modules

* [`/daemon`](daemon/): Python core backend orchestrating event ingestion, graph queries, and pedagogical responses.
  * Detailed documentation for the **Graph + RAG + Tutor Engine**: see [**`daemon/README.md`**](daemon/README.md).
* `/extension`: VS Code extension capturing student keystrokes, focus changes, and test executions (Team A).
* `/lessons`: Curated YAML lesson packages defining concepts, prerequisites, common mistakes, and seed questions (Team B).
* `/ui`: Tauri + React desktop pet application with live knowledge graph visualizer and interactive dialogue bubble (Team D).

---

## Team C Subsystem Quick Links

* [**Team C Module Documentation**](daemon/README.md)
* **Graph Schema & Indexes**: [`daemon/graph/schema.py`](daemon/graph/schema.py)
* **Ingestion, Attempts & Mastery**: [`daemon/graph/ingest.py`](daemon/graph/ingest.py)
* **Hybrid Search & Bottleneck Retrieval**: [`daemon/graph/retrieval.py`](daemon/graph/retrieval.py)
* **Output Guardrails**: [`daemon/tutor/guard.py`](daemon/tutor/guard.py)
* **Socratic Tutor Engine**: [`daemon/tutor/engine.py`](daemon/tutor/engine.py)
* **Database Seed Script**: [`daemon/seeds/seed_data.py`](daemon/seeds/seed_data.py)
* **Test Suites**: [`daemon/tests/test_guard.py`](daemon/tests/test_guard.py) and [`daemon/tests/test_queries.py`](daemon/tests/test_queries.py)
