"""Pipeline glue: editor events -> debounce/batch -> analysis -> tutor -> UI broadcast.

Design rules:
  * the editor socket handler only enqueues; it never waits on analysis or the LLM
  * analysis/tutor are sync interfaces owned by B/C, so they run in worker threads
  * "thinking" is broadcast immediately when a batch fires
"""
from __future__ import annotations

import asyncio
import dataclasses
import importlib
import logging
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

from config import Config
from redact import redact

log = logging.getLogger("tutor.pipeline")

VALID_TYPES = {"edit", "focus", "cursor", "diagnostics", "test_run", "file_open"}
MODES = {"dsa", "system_design"}
MAX_BATCH = 200
FALLBACK_Q = "Walk me through what you expect this part to do on the smallest input you can think of."


# ----------------------------------------------------------------- helpers
def as_dict(x: Any) -> dict | None:
    """Accept dicts, pydantic models or dataclasses from B/C's modules."""
    if x is None:
        return None
    if isinstance(x, dict):
        return x
    for attr in ("model_dump", "dict"):
        if hasattr(x, attr):
            return getattr(x, attr)()
    if dataclasses.is_dataclass(x):
        return dataclasses.asdict(x)
    return dict(x)


def sanitize_question(text: str) -> str:
    """Safety net for the core rule: the pet never outputs code or direct fixes."""
    text = (text or "").strip()
    if not text or "```" in text:
        return FALLBACK_Q
    return text[:600]


def load_backends(cfg: Config) -> SimpleNamespace:
    """Import analysis/tutor/graph; fall back to stubs per module (config.mock.*)."""
    ns = SimpleNamespace()
    for name in ("analysis", "tutor", "graph"):
        mod = None
        if not getattr(cfg.mock, name):
            try:
                mod = importlib.import_module(name)
            except ImportError as e:
                log.warning("real %s module not importable (%s); using stub", name, e)
        if mod is None:
            mod = importlib.import_module(f"mocks.{name}_stub")
        setattr(ns, name, mod)
        log.info("backend %-8s -> %s", name, mod.__name__)
    return ns


class Hub:
    """Holds the UI and editor sockets and fans messages out to them."""

    def __init__(self) -> None:
        self.ui: set = set()
        self.editors: set = set()
        self._lock = asyncio.Lock()

    async def _fanout(self, socks: set, msg: dict) -> None:
        async with self._lock:
            dead = []
            for ws in list(socks):
                try:
                    await ws.send_json(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                socks.discard(ws)

    async def to_ui(self, channel: str, payload: dict) -> None:
        await self._fanout(self.ui, {"channel": channel, "payload": payload})

    async def to_editor(self, command: str, **kw: Any) -> None:
        await self._fanout(self.editors, {"command": command, **kw})


# ---------------------------------------------------------------- pipeline
class Pipeline:
    def __init__(self, cfg: Config, hub: Hub, backends: SimpleNamespace) -> None:
        self.cfg, self.hub, self.b = cfg, hub, backends
        self.paused = False
        self.inspector = False
        self.last_activity = time.time()
        self._batches: dict[str, list[dict]] = {}
        self._timers: dict[str, asyncio.Task] = {}
        self._busy: set[str] = set()
        self._last_bubble = 0.0
        self._seen: dict[tuple[str, str], float] = {}
        self._last_finding: dict[str, dict] = {}
        self._lesson_cache: dict[Path, tuple[float, dict]] = {}
        self._ingested: set[str] = set()
        self._mode: str | None = None
        self._sleeping = False
        self._hold_until = 0.0
        self._watch: asyncio.Task | None = None

    # ---- lifecycle
    async def start(self) -> None:
        self._watch = asyncio.create_task(self._idle_watch())

    async def stop(self) -> None:
        for t in [self._watch, *self._timers.values()]:
            if t and not t.done():
                t.cancel()

    async def _idle_watch(self) -> None:
        while True:
            await asyncio.sleep(15)
            if not self._sleeping and time.time() - self.last_activity > self.cfg.sleep_after_seconds:
                self._sleeping = True
                await self.hub.to_ui("pet_state", {"state": "sleeping"})

    # ---- lessons
    def find_lesson(self, file: str) -> dict | None:
        p = Path(file).expanduser().resolve()
        roots = self.cfg.allowlist()
        for d in [p.parent, *p.parent.parents]:
            y = d / "lesson.yaml"
            if y.is_file():
                try:
                    m = y.stat().st_mtime
                    c = self._lesson_cache.get(d)
                    if c and c[0] == m:
                        return c[1]
                    data = yaml.safe_load(y.read_text()) or {}
                    data["_dir"], data["_path"] = str(d), str(y)
                    self._lesson_cache[d] = (m, data)
                    return data
                except Exception:
                    log.exception("bad lesson.yaml at %s", y)
                    return None
            if d in roots:
                break
        return None

    async def _note_lesson(self, lesson: dict | None) -> None:
        if not lesson:
            return
        track = lesson.get("track")
        mode = track if track in MODES else "dsa"
        if mode != self._mode:
            self._mode = mode
            await self.hub.to_ui("mode", {"mode": mode, "lesson_id": lesson.get("id")})
        if lesson["_path"] not in self._ingested:
            self._ingested.add(lesson["_path"])
            asyncio.create_task(self._ingest_lesson(lesson["_path"]))

    async def _ingest_lesson(self, path: str) -> None:
        try:
            await asyncio.to_thread(self.b.graph.ingest_lesson, path)
        except Exception:
            log.exception("graph.ingest_lesson failed for %s", path)

    # ---- ingest (called from /ws/editor; must be fast)
    async def ingest(self, ev: dict) -> None:
        if self.paused:
            return
        if ev.get("type") not in VALID_TYPES:
            log.debug("dropping event with bad type: %r", ev.get("type"))
            return
        file = ev.get("file", "")
        if not self.cfg.is_allowed(file):
            log.debug("dropping event outside allowlist: %s", file)
            return
        sid = ev.get("student_id") or self.cfg.default_student
        ev["student_id"] = sid
        if ev.get("content"):
            ev["content"] = redact(ev["content"])
        for d in ev.get("diagnostics") or []:
            d["message"] = redact(str(d.get("message", "")))
        log.debug("event %s %s", ev["type"], file)

        self.last_activity = time.time()
        if self._sleeping:
            self._sleeping = False
            await self.hub.to_ui("pet_state", {"state": "curious"})

        batch = self._batches.setdefault(sid, [])
        batch.append(ev)
        if len(batch) > MAX_BATCH:
            for i, e in enumerate(batch):
                if e["type"] == "cursor":
                    del batch[i]
                    break
            else:
                del batch[0]

        t = ev["type"]
        if t in ("focus", "file_open"):
            await self._note_lesson(self.find_lesson(file))
        if t == "edit":
            quiet = sid not in self._timers or self._timers[sid].done()
            if quiet and sid not in self._busy:
                await self.hub.to_ui("pet_state", {"state": "curious"})
            self._schedule(sid, self.cfg.debounce_seconds)
        elif t == "diagnostics":
            self._schedule(sid, self.cfg.debounce_seconds)
        elif t == "test_run":
            self._schedule(sid, 0)

    def _schedule(self, sid: str, delay: float) -> None:
        old = self._timers.get(sid)
        if old and not old.done():
            old.cancel()
        self._timers[sid] = asyncio.create_task(self._debounced(sid, delay))

    async def _debounced(self, sid: str, delay: float) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        batch = self._batches.pop(sid, [])
        if not batch:
            return
        counts = Counter(e["type"] for e in batch)
        last = batch[-1]
        log.info("batch student=%s file=%s lang=%s events=%s", sid, last.get("file"),
                 last.get("language"), dict(counts))
        await self.hub.to_ui("pet_state", {"state": "thinking"})  # immediate, before any slow work
        asyncio.create_task(self._process(sid, batch))

    # ---- background processing
    async def _process(self, sid: str, batch: list[dict]) -> None:
        if sid in self._busy:  # previous job still running: requeue and retry after next quiet period
            self._batches.setdefault(sid, [])[:0] = batch
            self._schedule(sid, self.cfg.debounce_seconds)
            return
        self._busy.add(sid)
        try:
            file = next((e["file"] for e in reversed(batch) if e.get("file")), "")
            lesson = self.find_lesson(file) if file else None
            await self._note_lesson(lesson)
            raw = await asyncio.wait_for(
                asyncio.to_thread(self.b.analysis.analyze, batch, lesson),
                self.cfg.llm_timeout_seconds)
            findings = [as_dict(f) for f in (raw or [])]
            finding = self._pick(findings, sid)
            if not finding:
                if time.time() > self._hold_until:
                    await self.hub.to_ui("pet_state", {"state": "idle"})
                return
            out = as_dict(await asyncio.wait_for(
                asyncio.to_thread(self.b.tutor.handle, finding, sid),
                self.cfg.llm_timeout_seconds))
            self._last_finding[sid] = finding
            self._last_bubble = time.time()
            self._seen[(sid, finding.get("mistake_id", ""))] = self._last_bubble
            await self._emit(out, sid)
        except Exception:
            log.exception("pipeline failure")
            await self.hub.to_ui("pet_state", {"state": "idle"})
        finally:
            self._busy.discard(sid)

    def _pick(self, findings: list[dict], sid: str) -> dict | None:
        now = time.time()
        if now - self._last_bubble < self.cfg.cooldowns.bubble_seconds:
            log.info("bubble cooldown active; skipping %d finding(s)", len(findings))
            return None
        for f in sorted(findings, key=lambda f: f.get("confidence", 0), reverse=True):
            if f.get("confidence", 1) < self.cfg.min_confidence:
                continue
            if now - self._seen.get((sid, f.get("mistake_id", "")), 0) < self.cfg.cooldowns.same_mistake_minutes * 60:
                continue
            return f
        return None

    async def _emit(self, out: dict, sid: str) -> None:
        q = sanitize_question(out.get("question", ""))
        out["question"] = q
        await self.hub.to_ui("pet_state", {"state": out.get("pet_state", "asking")})
        await self.hub.to_ui("bubble", {
            "text": q, "question": q,
            "hint_level": out.get("hint_level", 0),
            "targets_concept": out.get("targets_concept"),
            "mistake_id": out.get("mistake_id"),
        })
        trace = out.get("graph_trace")
        if trace:
            payload = dict(trace)
            if not self.inspector:  # inspector off -> live graph only, no query internals
                payload.pop("cypher", None)
                payload.pop("query_ms", None)
            await self.hub.to_ui("graph_update", payload)
        await self.hub.to_editor("show_hint", text=q, hint_level=out.get("hint_level", 0),
                                 concept=out.get("targets_concept"))
        try:
            progress = await asyncio.to_thread(self.b.graph.get_progress, sid)
            if progress:
                await self.hub.to_ui("mastery_update", as_dict(progress))
        except Exception:
            log.debug("mastery update unavailable", exc_info=True)

    # ---- typed or spoken reply (same path)
    async def handle_reply(self, text: str, sid: str, source: str = "typed") -> dict:
        text = redact(text or "").strip()
        log.info("reply (%s) student=%s: %.80s", source, sid, text)
        self.last_activity = time.time()
        await self.hub.to_ui("pet_state", {"state": "thinking"})
        last = self._last_finding.get(sid)
        try:
            fn = getattr(self.b.tutor, "handle_reply", None)
            if fn:
                out = await asyncio.wait_for(asyncio.to_thread(fn, text, sid, last), self.cfg.llm_timeout_seconds)
            elif last:
                out = await asyncio.wait_for(
                    asyncio.to_thread(self.b.tutor.handle, {**last, "student_reply": text}, sid),
                    self.cfg.llm_timeout_seconds)
            else:
                out = {"question": "What are you trying to make this code do, in one sentence?",
                       "hint_level": 0, "targets_concept": None, "mistake_id": None, "pet_state": "asking"}
        except Exception:
            log.exception("reply failure")
            out = {"question": FALLBACK_Q, "hint_level": 0, "pet_state": "asking"}
        out = as_dict(out)
        await self._emit(out, sid)
        return out

    # ---- test runs triggered by "Tutor: Run Tests"
    async def after_tests(self, sid: str, file: str, language: str, result: dict) -> None:
        results = result.get("results", [])
        if results and all(r.get("passed") for r in results):
            self._hold_until = time.time() + 4
            await self.hub.to_ui("pet_state", {"state": "celebrating"})
            await self.hub.to_ui("confetti", {"lesson_id": result.get("lesson_id")})
        await self.ingest({"type": "test_run", "ts": int(time.time()), "file": file, "language": language,
                           "test_result": result, "student_id": sid})
