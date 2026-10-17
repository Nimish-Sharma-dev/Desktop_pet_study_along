# Contract 5 additions (Module D)

Contracts 1-6 are unchanged. These fill gaps the UI needs; **team sign-off needed** (A routes, C produces).

## `/ws/ui` payloads (daemon -> UI)
All messages: `{ "channel": "...", "payload": {...} }`

| channel | payload |
|---|---|
| `pet_state` | `{ "state": PetState, "reason"?: string }` |
| `bubble` | full **Contract 4 TutorOutput** (includes `graph_trace`) |
| `graph_update` | `{ "nodes": Node[], "edges": Edge[], "highlight": { "node_ids": string[], "edges": Edge[], "reason"?: string } }` — `nodes`/`edges` are upserts; `highlight` is the path to light up |
| `mastery_update` | `{ "concept_id", "mastery": 0..1, "delta", "evolution": Evolution }` |
| `confetti` | `{ "reason"?: string, "count"?: number }` |
| `mode` | `{ "mode": "dsa" \| "system_design" }` — mode switch only, no scores |
| `review` | **new**, separate channel: `{ "design_id", "axes": [{ "id","label","score","max" }], "notes"?: string[] }` |

A new `review` message replaces the scores for that `design_id`. Axes are data-driven (any rubric axes render).

`Node = { id, label: "Student|Attempt|Mistake|Concept|Lesson", props }`, `Edge = { from, to, type }`
(types used: `MADE`, `SHOWED`, `RESOLVED`, `INVOLVES`, `PREREQUISITE_OF`).

`graph_trace.query_ms` must be the real measured FalkorDB time. The UI displays it unmodified.

## `Evolution` (in `mastery_update` and `/api/progress`)
```json
{ "stage": 2, "variant": "blob|wizard|dragon", "stage_name": "Apprentice",
  "next_stage_name": "Master", "progress": 0.56, "streak": 7, "mastery_total": 6.24,
  "next": { "min_streak": 14, "min_mastery_total": 10 } }
```

## REST (UI -> daemon)
- `GET /api/progress` -> see `Progress` in `ui/src/types/contracts.ts`
- `GET /api/graph` -> `{ nodes, edges }`
- `GET /api/review?design_id=` -> `ReviewPayload | null`  (**new**)
- `POST /api/reply {text}`, `POST /api/voice/start|stop`, `POST /api/inspector {enabled}`

Source of truth for shapes: `ui/src/types/contracts.ts`.

## Inspector (developer toggle)
`POST /api/inspector {enabled}` only tells the daemon the flag. The drawer is driven purely by `bubble.graph_trace`
(`cypher`, `query_ms`, `nodes`, `edges`), so the daemon should always include a real `graph_trace` in every `bubble`.

---
# Integration notes for the daemon (A) and tutor/graph (C)

## 1. CORS (required)
The app is a Tauri webview, so `fetch()` calls to `http://localhost:7777` are cross-origin. The daemon must answer
preflights for these origins (WebSocket is not affected):
`http://localhost:1420` (dev), `http://tauri.localhost` and `https://tauri.localhost` (Windows build), `tauri://localhost` (macOS/Linux build).
FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:1420", "http://tauri.localhost",
                   "https://tauri.localhost", "tauri://localhost"], allow_methods=["*"], allow_headers=["*"])
```

## 2. What the UI sends
| call | body | notes |
|---|---|---|
| `GET /api/progress` | | shape below; also refetched ~1s after bubble/confetti/mastery events and every 60s |
| `GET /api/graph` | | `{nodes, edges}` snapshot on every (re)connect |
| `GET /api/review?design_id=` | | latest review or `null` |
| `POST /api/reply` | `{text}` | student's typed answer |
| `POST /api/voice/start` / `stop` | none | UI assumes the daemon feeds the transcript to the tutor and replies with a normal `bubble` |
| `POST /api/inspector` | `{enabled}` | flag only; the drawer is driven by `bubble.graph_trace` |
| WS `/ws/ui` | receive only | |

## 3. Example payloads (what the UI is built and tested against)
```jsonc
// ws: pet_state
{"channel":"pet_state","payload":{"state":"thinking","reason":"analysing"}}
// ws: bubble  (full Contract 4; graph_trace on EVERY bubble so the inspector always has data)
{"channel":"bubble","payload":{"question":"What happens with one element?","hint_level":1,
 "targets_concept":"loop_invariants","mistake_id":"boundary_off_by_one","pet_state":"asking",
 "graph_trace":{"cypher":"MATCH (s:Student {id:$sid})-[:MADE]->(a:Attempt)-[:SHOWED]->(m:Mistake)-[:INVOLVES]->(c:Concept) RETURN s,a,m,c",
  "query_ms":3.2,"nodes":[{"id":"student:local-user","label":"Student","props":{}}],"edges":[{"from":"attempt:7","to":"mistake:boundary_off_by_one","type":"SHOWED"}]}}}
// ws: graph_update  (nodes/edges = upserts; highlight = the path to light up, ids must exist in the graph)
{"channel":"graph_update","payload":{"nodes":[{"id":"attempt:7","label":"Attempt","props":{"lesson_id":"binary-search","passed":false,"ts":1730000000}}],
 "edges":[{"from":"student:local-user","to":"attempt:7","type":"MADE"}],
 "highlight":{"node_ids":["student:local-user","attempt:7","mistake:boundary_off_by_one","concept:loop_invariants"],
  "edges":[{"from":"student:local-user","to":"attempt:7","type":"MADE"}],"reason":"boundary_off_by_one"}}}
// ws: mastery_update  (evolution optional; the UI derives it from streak + mastery when absent)
{"channel":"mastery_update","payload":{"concept_id":"loop_invariants","mastery":0.41,"delta":0.08}}
// ws: confetti / mode / review
{"channel":"confetti","payload":{"reason":"tests passed","count":140}}
{"channel":"mode","payload":{"mode":"system_design"}}
{"channel":"review","payload":{"design_id":"url-shortener","axes":[{"id":"scalability","label":"Scalability","score":6,"max":10},
 {"id":"fault_tolerance","label":"Fault tolerance","score":4,"max":10},{"id":"cost","label":"Cost","score":7,"max":10}],"notes":["single DB, no replica"]}}
```
`GET /api/progress` (all keys optional; missing ones just show an empty widget and a contract warning):
```jsonc
{"mode":"dsa","streak":{"current":6,"best":11},
 "daily_activity":[{"date":"2026-10-15","count":4}],
 "skill_radar":{"dsa":[{"axis":"Arrays","value":0.4}],"system_design":[{"axis":"Scalability","value":0.45}]},
 "concepts":[{"id":"loop_invariants","name":"Loop invariants","track":"dsa","mastery":0.28}],
 "recent_mistakes":[{"mistake_id":"boundary_off_by_one","count":5,"last_seen":"2026-10-16T09:00:00Z","concept_ids":["array_indexing","loop_invariants"]}],
 "patterns":[{"mistake_id":"boundary_off_by_one","kind":"recurring","count":5}],
 "hint_dependency":[{"date":"2026-10-15","avg_hint_level":2.4}],
 "lessons":[{"id":"binary-search","title":"Binary Search","track":"dsa","status":"in_progress","progress":0.6}],
 "recommended_next":{"lesson_id":"loop-invariants-drills","reason":"weakest linked concept"},
 "spaced_repetition_due":[{"concept_id":"loop_invariants","due_at":"2026-10-16T00:00:00Z","interval_days":3}],
 "timeline":[{"ts":1730000000,"kind":"pass","label":"Tests passed (binary-search)"}],
 "evolution":{"stage":2,"variant":"wizard","stage_name":"Apprentice","next_stage_name":"Master","progress":0.52,
              "streak":6,"mastery_total":6.1,"next":{"min_streak":14,"min_mastery_total":10}}}
```

## 4. Tolerances (the UI accepts these variations; anything else is reported as a contract warning)
- Scores/mastery as 0..1 or 0..100. Timestamps in epoch seconds or milliseconds (or ISO strings where a date is expected).
- Node ids may be numbers; labels are matched case-insensitively (`concept` = `Concept`); edges may use `source`/`target` instead of `from`/`to`; properties may be under `props` or `properties`.
- A Concept node links to `/api/progress` concepts via `props.concept_id` (or `key`/`slug`/`id`), else the id suffix after the last `:`, else its `name`.
- Unknown channels, unknown pet states and unknown modes are ignored/defaulted, never fatal.
- `query_ms` is never invented: if it is missing the inspector shows `n/a`.

## 5. Verify against the real daemon
From `ui/`: `npm run check:daemon` (optionally `-- http://host:port seconds`). Edit code in VS Code while it listens.
It checks the REST endpoints, CORS preflights for the app origins, the WebSocket, and validates every message with the
same code the UI runs. The same warnings also show live in the dashboard (Dev feed page, and a badge in the title bar).
