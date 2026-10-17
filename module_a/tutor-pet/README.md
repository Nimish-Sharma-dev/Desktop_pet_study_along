# Tutor Pet: role A (extension, daemon, voice)

Everything is local. The daemon binds to 127.0.0.1 only; no cloud calls anywhere.

```
extension/  VS Code extension (TypeScript): events out, commands in, pause toggle, allowlist, redaction
daemon/     app.py (FastAPI) + routing.py (debounce/batch/cooldowns) + voice/ + mocks/ (stubs for B, C)
docs/mocks/ JSON samples of every contract + a sample lesson (copy it, see step 3)
docker-compose.yml   FalkorDB (localhost only)
```

## Setup (about 10 minutes)

**Prereqs:** Python 3.10+, Node 18+, VS Code 1.85+, Docker. Ollama is only needed once C's real tutor lands.

1. **FalkorDB:** `docker compose up -d` (Redis port 6379, browser UI at http://localhost:3000).
2. **Daemon:**
   ```
   cd daemon && python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python app.py            # or: uvicorn app:app --host 127.0.0.1 --port 7777
   ```
   Config is `daemon/config.yaml` (ports, models, debounce, cooldowns, allowlist, which modules are mocked).
   `LOG_LEVEL=DEBUG` shows every raw event.
3. **Lessons folder (the allowlist):**
   `mkdir -p ~/tutor-lessons && cp -r docs/mocks/lessons/* ~/tutor-lessons/`
4. **Extension:** `cd extension && npm install && npm run compile`, then open `/extension` in VS Code and press F5
   (Extension Development Host). Or `npm run package` and install the `.vsix`.
   Open `~/tutor-lessons/binary-search/solution.py`. The status bar shows **Tutor** (click = pause/resume).
5. **Voice (optional):** `pip install -r requirements-voice.txt`, install whisper.cpp (`whisper-cli`) and Piper,
   download one ggml model and one Piper `.onnx` voice, set the paths and `voice.enabled: true` in `config.yaml`,
   then `python -m voice.check`. Hold **Ctrl+Alt+Space** to talk. macOS needs Accessibility + Input Monitoring
   permission for pynput; on Wayland use `POST /api/voice/start|stop` (the UI's mic button) instead of the hotkey.

## Demo script (no VS Code needed, 2 minutes)

```
cd daemon
python scripts/ui_listener.py            # terminal 1: prints what the UI would receive
python scripts/sim_editor.py             # terminal 2: 6 edits + a diagnostic, like the extension
curl -XPOST localhost:7777/api/run_tests -H 'content-type: application/json' \
     -d '{"file":"'$HOME'/tutor-lessons/binary-search/solution.py","language":"python"}'   # run 3x: 3rd run passes -> confetti
curl -XPOST localhost:7777/api/pause -H 'content-type: application/json' -d '{"paused":true}'  # then edit: silence
pytest tests                              # 9 tests: debounce, pause, allowlist, redaction, cooldowns, 3s latency
```

## What the daemon does

`/ws/editor` enqueues events and returns immediately. A quiet period of `debounce_seconds` after the last
edit/diagnostic closes a batch; "thinking" is broadcast at that moment, then analysis and the tutor run in worker
threads with a timeout. Cooldowns: one bubble per `bubble_seconds`, no repeat of a `mistake_id` within
`same_mistake_minutes`. Replies (typed, panel, voice) share one path (`Pipeline.handle_reply`). Any tutor output
containing a code fence is replaced with a generic question (safety net for "never output fixes").
Sleep after 5 idle minutes; `mode` is derived from the lesson's `track`.

## Privacy

Extension: only files inside `tutor.allowlistedFolders`, never `.env*`/`.pem`/`.key`, secrets redacted before
sending, pause gates every outgoing event (pending timers are cancelled and the daemon is told to drop everything).
Daemon: allowlist and redaction enforced a second time. Keep `tutor.allowlistedFolders` and `allowlisted_paths` in sync.

## Contract addenda (need sign-off from B, C, D)

1. **Positions are 1-based** (line and col) everywhere on the wire, including `open_file`.
2. `file_open` events carry an optional `"action": "open" | "close"`.
3. `test_run` events carry an optional `"test_result"` (Contract 2 object) so `analysis.analyze` sees the failures.
4. **Daemon -> editor commands** use the same `/ws/editor` socket: `{"command": "show_hint|open_file|open_lesson|accept_reply", ...}`.
   Other modules can trigger them via `POST /api/editor/command`.
5. **C:** `tutor.handle(finding, student_id)` cannot take a student's reply. The daemon calls an optional
   `tutor.handle_reply(text, student_id, last_finding)`; if absent it falls back to `handle()` with `student_reply` added to the finding.
6. **C:** `/api/progress` and `/api/graph` need `graph.get_progress(student_id)` and `graph.get_graph(student_id)`
   (shapes in `mocks/graph_stub.py`). `graph.ingest_lesson(path)` is called once per lesson with the path to `lesson.yaml`.
7. **D:** `bubble` payload is `{text, question, hint_level, targets_concept, mistake_id}`; `pet_state` is `{state}`;
   `graph_update` is always sent, but `cypher`/`query_ms` only when the inspector is enabled.
8. **B:** `analysis.analyze` receives the lesson as the parsed `lesson.yaml` dict plus `_dir` and `_path`, or `None`.

## Switching to the real modules

Set `mock.analysis`/`mock.tutor`/`mock.graph` to `false` in `config.yaml` one at a time. The daemon imports
`analysis`, `tutor`, `graph` from `/daemon` and falls back to the stub (with a warning) if the import fails.

## Known limits

Pausing is per window (workspaceState); the daemon pause is global. `open_lesson` adds a workspace folder rather
than replacing the window. Redaction is regex-based: it catches common key formats and quoted `password = "..."`
literals, not every possible secret.
