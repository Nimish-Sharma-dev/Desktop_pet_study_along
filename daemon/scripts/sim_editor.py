"""Pretends to be the VS Code extension. Usage: python scripts/sim_editor.py [--file PATH]"""
import argparse
import asyncio
import json
import os
import time

import websockets

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="ws://127.0.0.1:7777/ws/editor")
ap.add_argument("--file", default=os.path.expanduser("~/tutor-lessons/binary-search/solution.py"))
ap.add_argument("--language", default="python")
a = ap.parse_args()

CODE = "def search(arr, target):\n    lo, hi = 0, len(arr){}\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        # {}\n"


def ev(t, **kw):
    return {"type": t, "ts": int(time.time()), "file": a.file, "language": a.language,
            "student_id": "local-user", **kw}


async def main():
    async with websockets.connect(a.url) as ws:
        async def listen():
            async for m in ws:
                print("<- daemon command:", m)
        asyncio.create_task(listen())
        await ws.send(json.dumps(ev("focus", content=CODE.format("", "start"), cursor={"line": 2, "col": 1}, selection=None)))
        for i in range(6):  # a burst of keystrokes: should collapse into ONE batch ~1.5s after the last
            await ws.send(json.dumps(ev("edit", content=CODE.format("", f"typing {i}"), cursor={"line": 5, "col": i}, selection=None)))
            await asyncio.sleep(0.25)
        print("sent 6 edits; waiting for the debounced bubble...")
        await asyncio.sleep(5)
        await ws.send(json.dumps(ev("diagnostics", diagnostics=[{"line": 3, "severity": "error", "message": "unexpected indent"}])))
        await asyncio.sleep(5)

asyncio.run(main())
