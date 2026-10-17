"""Pretends to be the UI: prints everything on /ws/ui. Usage: python scripts/ui_listener.py"""
import asyncio
import json
import sys

import websockets


async def main(url):
    async with websockets.connect(url) as ws:
        async for m in ws:
            d = json.loads(m)
            print(f"[{d['channel']:>14}] {json.dumps(d['payload'])[:160]}")

asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:7777/ws/ui"))
