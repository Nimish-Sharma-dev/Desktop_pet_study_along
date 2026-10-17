"""Fake editor and UI clients speaking Contract 1 and Contract 5."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional
from pathlib import Path


class FakeUiClient:
    """Simulates a Tauri / Web UI connected to the daemon's hub."""

    def __init__(self) -> None:
        self.messages: List[Dict[str, Any]] = []
        self.bubbles: List[Dict[str, Any]] = []
        self.pet_states: List[str] = []
        self.graph_updates: List[Dict[str, Any]] = []
        self.mastery_updates: List[Dict[str, Any]] = []
        self.confetti: List[Dict[str, Any]] = []
        self.modes: List[str] = []
        self.reviews: List[Dict[str, Any]] = []
        self._new_event = asyncio.Event()

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Called by Hub.broadcast or Hub.to_ui."""
        self.messages.append(data)
        chan = data.get("channel")
        payload = data.get("payload", {})

        if chan == "bubble":
            self.bubbles.append(payload)
        elif chan == "pet_state":
            st = payload.get("state")
            if st:
                self.pet_states.append(st)
        elif chan == "graph_update":
            self.graph_updates.append(payload)
        elif chan == "mastery_update":
            self.mastery_updates.append(payload)
        elif chan == "confetti":
            self.confetti.append(payload)
        elif chan == "mode":
            m = payload.get("mode")
            if m:
                self.modes.append(m)
        elif chan == "review":
            self.reviews.append(payload)

        self._new_event.set()

    async def wait_for_bubble(self, timeout: float = 6.0) -> Optional[Dict[str, Any]]:
        t_end = time.time() + timeout
        while time.time() < t_end:
            if self.bubbles:
                return self.bubbles[-1]
            self._new_event.clear()
            try:
                await asyncio.wait_for(self._new_event.wait(), max(0.1, t_end - time.time()))
            except asyncio.TimeoutError:
                break
        return self.bubbles[-1] if self.bubbles else None

    async def wait_for_state(self, expected_state: str, timeout: float = 6.0) -> bool:
        t_end = time.time() + timeout
        while time.time() < t_end:
            if expected_state in self.pet_states:
                return True
            self._new_event.clear()
            try:
                await asyncio.wait_for(self._new_event.wait(), max(0.1, t_end - time.time()))
            except asyncio.TimeoutError:
                break
        return expected_state in self.pet_states

    def clear(self) -> None:
        self.messages.clear()
        self.bubbles.clear()
        self.pet_states.clear()
        self.graph_updates.clear()
        self.mastery_updates.clear()
        self.confetti.clear()
        self.modes.clear()
        self.reviews.clear()
        self._new_event.clear()


class FakeEditorClient:
    """Emits Contract 1 compliant editor events."""

    def __init__(self, pipeline: Any, student_id: str = "local-user") -> None:
        self.pipeline = pipeline
        self.student_id = student_id

    async def send_event(
        self,
        event_type: str,
        file: str,
        content: Optional[str] = None,
        language: str = "python",
        cursor: Optional[Dict[str, int]] = None,
        diagnostics: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        ev = {
            "type": event_type,
            "ts": time.time(),
            "file": str(Path(file).resolve()),
            "language": language,
            "student_id": self.student_id,
        }
        if content is not None:
            ev["content"] = content
        if cursor is not None:
            ev["cursor"] = cursor
        if diagnostics is not None:
            ev["diagnostics"] = diagnostics

        await self.pipeline.ingest(ev)

    async def edit(self, file: str, content: str, language: str = "python", line: int = 1) -> None:
        await self.send_event("edit", file, content=content, language=language, cursor={"line": line, "character": 1})

    async def run_tests(self, file: str, language: str = "python") -> Dict[str, Any]:
        """Trigger after_tests flow simulating VS Code 'Tutor: Run Tests' command."""
        lesson = self.pipeline.find_lesson(file)
        if not lesson:
            raise ValueError(f"No lesson found for {file}")
        
        # Run tests through analysis adapter
        result = self.pipeline.b.analysis.run_tests(lesson["id"], language, lesson["_dir"])
        if isinstance(result, dict):
            res_dict = result
        else:
            res_dict = getattr(result, "model_dump", getattr(result, "dict", lambda: dict(result)))()
        
        res_dict["all_passed"] = bool(res_dict.get("results")) and all(r.get("passed") for r in res_dict["results"])
        await self.pipeline.after_tests(self.student_id, file, language, res_dict)
        return res_dict
