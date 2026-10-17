# Module D: Pet + Dashboard UI (Tauri + React)

Everything the student sees: the desktop pet and the translucent dark dashboard. It talks to the real daemon only:
`ws://localhost:7777/ws/ui` plus the REST endpoints of Contract 5. There is no mock data in this project. When the daemon is
not reachable the UI shows honest offline/empty states.

## Run
Prerequisites (Windows): Node 20+, Rust (https://rustup.rs, restart the terminal after installing), Microsoft C++ Build Tools
("Desktop development with C++"), WebView2 (preinstalled on Win 11).

```bash
# 1. start the daemon (A's app.py, port 7777), FalkorDB (6379) and Ollama (11434) as usual
# 2. the app
cd ui
npm install
npm run tauri dev        # first build compiles Rust: 5-10 min, later runs are fast
```
Daemon on another host/port: copy `.env.example` to `.env` and set `VITE_DAEMON_URL`.
Project inside OneDrive? Build outside it: `$env:CARGO_TARGET_DIR="C:\cargo-target\tutor-pet"`.
Installer: `npm run tauri build`. Browser-only preview (no Tauri window features): `npm run dev`, then `localhost:1420/`, `/dashboard.html`, `/?gallery`.
The tray icon is the only way to quit: Open dashboard / Reset pet position / Quit.

## Integration (read this first, daemon owners)
1. **CORS**: the daemon must allow the app's origins. Snippet in `../docs/contracts.md` section 1.
2. **Check it**: with the daemon running, `npm run check:daemon` (from `ui/`). Edit code in VS Code while it listens 20s. It verifies REST, CORS, the
   WebSocket and validates every message with the same validators the UI uses. Output is PASS / WARN / FAIL with the exact deviation.
3. **In-app**: contract deviations also show live in the dashboard (Dev feed page + a title-bar badge), so integration problems are visible without a console.
4. Exact payload examples and the tolerances (percent vs 0..1, seconds vs ms, id schemes) are in `../docs/contracts.md` sections 3-4.

What each screen needs from the daemon:
| screen | needs |
|---|---|
| Pet states, bubble, hint meter, reply box | WS `pet_state`, `bubble`; `POST /api/reply` |
| Mic button | `POST /api/voice/start`, `/stop` |
| Confetti, repeat-mistake overlays | WS `confetti`; repeated `bubble.mistake_id` |
| Evolution bar | `GET /api/progress` `evolution` (or `streak` + `concepts`: derived with default thresholds) and WS `mastery_update` |
| Progress page | `GET /api/progress` (each widget has its own key; missing key = empty widget) |
| Live Graph | `GET /api/graph` snapshot + WS `graph_update` (with `highlight`) |
| Inspector drawer | `bubble.graph_trace` {cypher, query_ms, nodes, edges}; `POST /api/inspector` |
| Command center | WS `mode` + `review`; optional `GET /api/review` |

## Scripts (in `ui/`)
| command | what |
|---|---|
| `npm run tauri dev` / `tauri build` | desktop app |
| `npm run check:daemon [-- url seconds]` | integration check against the real daemon |
| `npm run typecheck` / `build` | tsc / tsc + vite build |
| `npm run gen:media` | regenerate placeholder art in `public/media` |

## Layout
```
src-tauri/        Rust: window placement + position memory, click-through poller, glass window, tray
src/types/        contracts.ts: every contract type (source of truth)
src/api/          rest client, auto-reconnect ws, frame-batched feed, normalize.ts (validation of everything the daemon sends)
src/config/       evolution.ts: fallback stage thresholds (used only if the daemon sends no evolution)
src/store/        zustand store; one reducer for every /ws/ui channel
src/pet/          PetApp, Bubble, PetSprite, art/ (loader + built-in fallback art), Overlays, Confetti, EvolutionBar, ArtGallery
src/dashboard/    shell (TitleBar, Sidebar) + pages/ + progress/ + graph/ + inspector/ + command/
public/media/     placeholder pet art + README with the file-naming rules (real art drops in with no code change)
```

## Acceptance map
| acceptance | where | how to see it (with the real daemon) |
|---|---|---|
| All 8 pet states from /media and from fallback art | `pet/art/*`, `public/media` | `localhost:1420/?gallery`: `file` / `fallback` badge, "force fallback art" toggle |
| graph_update lights Student > Attempt > Mistake > Concept | `dashboard/graph/*` | Live Graph page while the pet reacts to your code |
| Inspector shows Cypher + real `query_ms` per reaction | `dashboard/inspector/*` | toggle Inspector in the title bar (keep the dashboard open) |
| Mode switch toggles command center + radar | `dashboard/command/*` | daemon sends `mode: system_design` + `review` |
| Smooth with graph open and events streaming | frame-batched feed, memoized nodes/edges | leave Live Graph open during a busy session |

## 2-minute demo script (real daemon, real VS Code)
Setup: daemon + FalkorDB + Ollama running, app running, a lesson open in VS Code (e.g. binary-search).
| time | do | say |
|---|---|---|
| 0:00 | Pet idles bottom-right. Drag it. | "A desktop pet that watches your code, fully local. It never gives the fix, only questions." |
| 0:15 | Write a binary search with an off-by-one and run the tests | "It's thinking... then a guiding question. Hint level and target concept are on the bubble." |
| 0:40 | Type an answer in the bubble, Enter; re-run with the same bug twice | "Same mistake again: detective glasses. Third time: stressed, and the tutor escalates." |
| 1:00 | Fix it, tests pass | "Confetti, mastery goes up, the evolution bar moves." |
| 1:10 | Click the pet | "Dashboard: streak, heatmap, skill radar, weakest concepts, recurring mistakes, hint dependency, next lesson, spaced repetition." |
| 1:30 | Live Graph, trigger another reaction | "Each reaction is a real graph query: Student, Attempt, Mistake, Concept light up. Weak concepts pulse red." |
| 1:45 | Toggle Inspector, trigger a reaction | "The exact Cypher, the sub-graph returned, and the measured query time. Not a fake number." |
| 1:55 | Switch to a system design lesson | "Command center, hard hat, live review radar updating as scores arrive." |

## Troubleshooting
- `cargo metadata: program not found`: Rust missing, or the terminal was not restarted after installing it.
- Pet/dashboard shows "daemon not reachable": check `npm run check:daemon`; usually the daemon is down or CORS is missing (FAIL lines say which).
- Dark box behind the pet: window transparency not applied on that Windows build; report it.
- Dashboard not glassy: native acrylic failed, so it falls back to a near-opaque dark background on purpose.
- Inspector drawer never opens: it lives in the dashboard window, so keep the dashboard open (it can sit behind the editor), and make sure every `bubble` carries `graph_trace`.
- Yellow "contract warning" badge: open Dev feed; each line names the field the daemon sent wrong or left out.

## Known limits
- Inspector needs the dashboard window open. No single-instance guard (launching twice = two pets), no autostart.
- Voice: only start/stop exists in the contract; the UI assumes the daemon feeds the transcript to the tutor and replies with a `bubble`.
- Verified here: typecheck, build, `cargo check` (Linux), the validators against conforming and deliberately broken daemons, layout and Cypher tokenizer tests. Window behaviour (transparency, click-through, acrylic) needs a run on a real Windows machine.
