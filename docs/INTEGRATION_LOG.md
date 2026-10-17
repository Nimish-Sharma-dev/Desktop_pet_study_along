# Integration Log: Socratic Code-Tutor Pet

This log tracks every modification made across modules, boundaries, adapters, schemas, and configurations.

| Timestamp | Module / File | Change Type | Description / Rationale |
|---|---|---|---|
| 2026-10-17 | `ui/src-tauri/src/lib.rs` | Bug Fix (Module D) | Replaced synchronous `open_dashboard` and tray event handling with asynchronous non-blocking implementations to prevent WebView2 main-thread deadlocks on Windows. |
| 2026-10-17 | `daemon/analysis/sandbox.py` | Cross-Platform (Module B) | Added graceful fallback for Linux-only `resource` module (`RLIMIT_*`) on Windows so that test runners and sandboxes can execute. |
| 2026-10-17 | `daemon/tutor/guard.py` | Bug Fix (Module C) | Fixed assignment regex to match expressions starting with parentheses (e.g. `mid = (left + right) // 2`). |
| 2026-10-17 | `daemon/contracts.py` | Integration (Boundary) | Defined canonical Pydantic v2 data models for all 6 contracts crossing module boundaries. |
| 2026-10-17 | `daemon/adapters/` | Integration (Boundary) | Built thin adapter layer bridging Module A, Module B, Module C, and Module D without rewriting internal module code. |
| 2026-10-17 | `daemon/routing.py` & `app.py` | Integration (Module A) | Upgraded pipeline to broadcast full Contract 4 `TutorOutput` on `bubble`, emit `review` on `design.md`, record attempts, update mastery on test pass, and added `/api/review` endpoint. |
| 2026-10-17 | `config.yaml` | Configuration | Unified configuration for ports, model tags, debounce, cooldowns, allowlist, and inspector/voice feature flags. |
| 2026-10-17 | `daemon/adapters/graph_adapter.py` | Integration (Boundary) | Added `get_graph` alias pointing to `get_graph_snapshot` to satisfy Contract 5 REST `/api/graph`. |
| 2026-10-17 | `daemon/app.py` | Integration (Module A) | Updated CORS regex for `https://tauri.localhost`, added `/api/review` endpoint, and fixed backend names in `/api/health`. |
| 2026-10-17 | `daemon/graph/` & `daemon/tutor/` | Compatibility (Module C) | Added import fallback between `daemon.<pkg>` and `<pkg>` so execution works when `daemon/` is the current working directory. |
| 2026-10-17 | `daemon/adapters/tutor_adapter.py` & `daemon/routing.py` | Integration (Boundary) | Enhanced `reset_recurrence` to reset student mistake counts upon passing tests. |
