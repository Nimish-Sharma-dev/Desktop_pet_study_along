import asyncio
import os
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import Config, CooldownCfg  # noqa: E402
from mocks import analysis_stub, graph_stub, tutor_stub  # noqa: E402
from redact import redact  # noqa: E402
from routing import Pipeline  # noqa: E402


class FakeHub:
    def __init__(self):
        self.ui, self.cmds = [], []

    async def to_ui(self, channel, payload):
        self.ui.append((time.time(), channel, payload))

    async def to_editor(self, command, **kw):
        self.cmds.append((command, kw))

    def channels(self, name):
        return [p for _, c, p in self.ui if c == name]


def make(tmp, analyze=None, tutor=None, debounce=0.3, bubble_s=0, same_min=5):
    cfg = Config(allowlisted_paths=[str(tmp)], debounce_seconds=debounce,
                 cooldowns=CooldownCfg(bubble_seconds=bubble_s, same_mistake_minutes=same_min))
    be = SimpleNamespace(analysis=SimpleNamespace(analyze=analyze or analysis_stub.analyze, run_tests=analysis_stub.run_tests),
                         tutor=tutor or tutor_stub, graph=graph_stub)
    hub = FakeHub()
    return Pipeline(cfg, hub, be), hub, str(tmp / "x.py")


def ev(file, t="edit", **kw):
    return {"type": t, "ts": 1, "file": file, "language": "python", "content": "x = 1", **kw}


def test_debounce_collapses_burst(tmp_path):
    calls = []
    p, hub, f = make(tmp_path, analyze=lambda b, l: calls.append([e["type"] for e in b]) or [])

    async def run():
        for i in range(5):
            await p.ingest(ev(f, content=f"x={i}"))
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.9)
    asyncio.run(run())
    assert calls == [["edit"] * 5]
    assert hub.channels("pet_state")[-2]["state"] == "thinking" or any(s["state"] == "thinking" for s in hub.channels("pet_state"))


def test_pause_stops_everything(tmp_path):
    calls = []
    p, hub, f = make(tmp_path, analyze=lambda b, l: calls.append(1) or [])
    p.paused = True

    async def run():
        await p.ingest(ev(f))
        await asyncio.sleep(0.8)
    asyncio.run(run())
    assert not calls and not hub.ui


def test_outside_allowlist_ignored(tmp_path):
    calls = []
    p, hub, _ = make(tmp_path, analyze=lambda b, l: calls.append(1) or [])

    async def run():
        await p.ingest(ev("/etc/passwd"))
        await p.ingest(ev(str(tmp_path / ".env")))
        await asyncio.sleep(0.8)
    asyncio.run(run())
    assert not calls


def test_secrets_redacted_before_analysis(tmp_path):
    seen = []
    p, _, f = make(tmp_path, analyze=lambda b, l: seen.append(b[0]["content"]) or [])
    secret = "sk-abcdefghijklmnopqrstuvwxyz123456"

    async def run():
        await p.ingest(ev(f, content=f'api_key = "{secret}"\npassword = "hunter22"'))
        await asyncio.sleep(0.8)
    asyncio.run(run())
    assert secret not in seen[0] and "hunter22" not in seen[0] and "[REDACTED" in seen[0]


def test_same_mistake_cooldown(tmp_path):
    fixed = lambda b, l: [{"kind": "pattern", "mistake_id": "m1", "concept_ids": ["c"], "file": "f", "line": 1,
                           "evidence": "", "confidence": 0.9, "lesson_id": "l"}]
    p, hub, f = make(tmp_path, analyze=fixed)

    async def run():
        for _ in range(2):
            await p.ingest(ev(f))
            await asyncio.sleep(0.8)
    asyncio.run(run())
    assert len(hub.channels("bubble")) == 1


def test_bubble_rate_limit(tmp_path):
    seq = iter(["a", "b"])
    one = lambda b, l: [{"kind": "pattern", "mistake_id": next(seq), "concept_ids": [], "file": "f", "line": 1,
                         "evidence": "", "confidence": 0.9, "lesson_id": "l"}]
    p, hub, f = make(tmp_path, analyze=one, bubble_s=60)

    async def run():
        for _ in range(2):
            await p.ingest(ev(f))
            await asyncio.sleep(0.8)
    asyncio.run(run())
    assert len(hub.channels("bubble")) == 1


def test_code_in_tutor_output_is_blocked(tmp_path):
    bad = SimpleNamespace(handle=lambda f, s: {"question": "Use this:\n```py\nhi = n-1\n```", "pet_state": "asking"})
    p, hub, f = make(tmp_path, tutor=bad)

    async def run():
        await p.ingest(ev(f))
        await asyncio.sleep(0.8)
    asyncio.run(run())
    assert "```" not in hub.channels("bubble")[0]["text"]


def test_edit_to_bubble_within_3s_with_default_debounce(tmp_path):
    p, hub, f = make(tmp_path, debounce=1.5)

    async def run():
        t0 = time.time()
        await p.ingest(ev(f))
        while not hub.channels("bubble") and time.time() - t0 < 5:
            await asyncio.sleep(0.05)
        return time.time() - t0
    dt = asyncio.run(run())
    assert dt < 3.0, dt


def test_redact_unit():
    assert "AKIA" not in redact("key AKIAABCDEFGHIJKLMNOP end")
    assert "total = 3" in redact("total = 3")
    assert "BEGIN" not in redact("-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----")
