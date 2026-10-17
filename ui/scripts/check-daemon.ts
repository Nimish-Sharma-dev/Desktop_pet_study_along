// Integration check against the REAL daemon (run from ui/):
//   npm run check:daemon                         -> http://localhost:7777, listens 20s
//   npm run check:daemon -- http://localhost:7777 40
// Verifies: REST endpoints answer and parse, CORS lets the Tauri webview call them, /ws/ui connects,
// and every message that arrives matches the contract (same validators the UI uses).
// Trigger activity in VS Code while it listens so the daemon actually emits events.
import WebSocket from 'ws';
import { parseGraph, parseProgress, parseReview, parseUiMessage, setIssueSink } from '../src/api/normalize';

const base = (process.argv[2] ?? 'http://localhost:7777').replace(/\/$/, '');
const seconds = Number(process.argv[3] ?? 20);
const wsUrl = base.replace(/^http/, 'ws') + '/ws/ui';

let ctx = 'setup';
const issues = new Map<string, Set<string>>(); // message -> contexts
setIssueSink((list) => list.forEach((i) => { (issues.get(i) ?? issues.set(i, new Set()).get(i)!).add(ctx); }));

const lines: { level: 'PASS' | 'WARN' | 'FAIL'; text: string }[] = [];
const log = (level: 'PASS' | 'WARN' | 'FAIL', text: string) => { lines.push({ level, text }); console.log(`${level}  ${text}`); };

async function getJson(path: string): Promise<unknown | undefined> {
  try {
    const res = await fetch(base + path);
    if (!res.ok) { log('FAIL', `GET ${path} -> HTTP ${res.status}`); return undefined; }
    return await res.json();
  } catch (e) {
    log('FAIL', `GET ${path} unreachable (${(e as Error).message}). Is the daemon running on ${base}?`);
    return undefined;
  }
}

console.log(`Checking daemon at ${base} (ws ${wsUrl}), listening ${seconds}s\n`);

// ---- REST ----
ctx = 'GET /api/progress';
const prog = await getJson('/api/progress');
if (prog !== undefined) { const p = parseProgress(prog); log('PASS', `GET /api/progress parsed (${p.concepts.length} concepts, ${p.daily_activity.length} activity days, ${p.lessons.length} lessons)`); }
ctx = 'GET /api/graph';
const graph = await getJson('/api/graph');
if (graph !== undefined) { const g = parseGraph(graph); log(g.nodes.length ? 'PASS' : 'WARN', `GET /api/graph parsed (${g.nodes.length} nodes, ${g.edges.length} edges)${g.nodes.length ? '' : ': empty graph (ok before ingest_lesson)'}`); }
ctx = 'GET /api/review';
const rev = await getJson('/api/review');
if (rev !== undefined) log('PASS', `GET /api/review answered (${parseReview(rev) ? 'has a review' : 'no review yet'})`);
try {
  const res = await fetch(base + '/api/inspector', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled: false }) });
  log(res.ok ? 'PASS' : 'FAIL', `POST /api/inspector -> HTTP ${res.status}`);
} catch (e) { log('FAIL', `POST /api/inspector unreachable (${(e as Error).message})`); }

// ---- CORS: the app runs from these origins and calls the daemon with fetch() ----
for (const origin of ['http://localhost:1420', 'http://tauri.localhost', 'https://tauri.localhost', 'tauri://localhost']) {
  try {
    const res = await fetch(base + '/api/reply', { method: 'OPTIONS', headers: { Origin: origin, 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type' } });
    const allow = res.headers.get('access-control-allow-origin');
    const ok = allow === '*' || allow === origin;
    log(ok ? 'PASS' : 'FAIL', `CORS preflight from ${origin}: ${ok ? 'allowed' : `blocked (allow-origin: ${allow ?? 'none'})`}`);
  } catch (e) { log('FAIL', `CORS preflight from ${origin} failed (${(e as Error).message})`); }
}

// ---- WebSocket ----
ctx = '/ws/ui';
const counts = new Map<string, number>();
let bubbles = 0, bubblesWithMs = 0, connected = false;
await new Promise<void>((resolve) => {
  const ws = new WebSocket(wsUrl);
  const done = setTimeout(() => { ws.close(); resolve(); }, seconds * 1000);
  ws.on('open', () => { connected = true; log('PASS', `WebSocket connected: ${wsUrl}`); });
  ws.on('error', (e) => { log('FAIL', `WebSocket error: ${(e as Error).message}`); clearTimeout(done); resolve(); });
  ws.on('message', (data) => {
    let raw: unknown;
    try { raw = JSON.parse(String(data)); } catch { ctx = '/ws/ui'; issues.set('ws: non-JSON message', new Set(['/ws/ui'])); return; }
    const channel = typeof raw === 'object' && raw && 'channel' in raw ? String((raw as { channel: unknown }).channel) : '?';
    ctx = `ws:${channel}`;
    const msg = parseUiMessage(raw);
    counts.set(channel, (counts.get(channel) ?? 0) + 1);
    if (msg?.channel === 'bubble') { bubbles++; if (msg.payload.graph_trace.query_ms !== null && msg.payload.graph_trace.cypher) bubblesWithMs++; }
  });
});

if (connected) {
  const total = [...counts.values()].reduce((a, b) => a + b, 0);
  if (!total) log('WARN', `no messages in ${seconds}s. Edit code in VS Code (or trigger a test run) while this runs`);
  else log('PASS', `received ${total} messages: ${[...counts].map(([c, n]) => `${c}×${n}`).join(', ')}`);
  if (bubbles) log(bubblesWithMs === bubbles ? 'PASS' : 'WARN', `${bubblesWithMs}/${bubbles} bubbles carried graph_trace with cypher + numeric query_ms (inspector needs all of them)`);
  else log('WARN', 'no bubble seen: inspector, hint badge and reply flow were not exercised');
}

// ---- contract warnings ----
console.log('');
if (issues.size) {
  console.log(`Contract warnings (${issues.size}):`);
  for (const [msg, where] of issues) console.log(`  - ${msg}   [${[...where].join(', ')}]`);
  log('WARN', `${issues.size} contract warning(s) above: the UI tolerates them but the affected widgets show empty/derived data`);
} else log('PASS', 'no contract warnings');

const fails = lines.filter((l) => l.level === 'FAIL').length, warns = lines.filter((l) => l.level === 'WARN').length;
console.log(`\n${fails ? 'FAILED' : 'OK'}: ${fails} failure(s), ${warns} warning(s)`);
process.exit(fails ? 1 : 0);
