"""Pytest fixtures and helpers for E2E test scenarios."""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Tuple

import pytest

# Ensure repo_root and daemon are on sys.path
repo_root = Path(__file__).resolve().parents[2]
daemon_dir = repo_root / "daemon"
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(daemon_dir) not in sys.path:
    sys.path.insert(0, str(daemon_dir))

from config import Config
from routing import Hub, Pipeline, load_backends
from tests.e2e.fake_editor import FakeEditorClient, FakeUiClient


@asynccontextmanager
async def stack_context(
    tmp_path: Path | None = None,
    student_id: str | None = None,
) -> AsyncGenerator[Tuple[Pipeline, FakeEditorClient, FakeUiClient], None]:
    """Helper context manager to spin up a fully integrated pipeline with fast debounce."""
    import uuid
    sid = student_id or f"student-{uuid.uuid4().hex[:8]}"
    cfg = Config()
    cfg.debounce_seconds = 0.05
    cfg.llm_timeout_seconds = 10
    cfg.min_confidence = 0.25
    cfg.cooldowns.bubble_seconds = 0.0
    cfg.cooldowns.same_mistake_minutes = 0.0
    cfg.inspector = True
    cfg.default_student = sid
    allowlist = [str(repo_root / "lessons")]
    if tmp_path:
        allowlist.append(str(tmp_path))
    cfg.allowlisted_paths = allowlist
    cfg.mock.analysis = False
    cfg.mock.tutor = False
    cfg.mock.graph = False

    hub = Hub()
    backends = load_backends(cfg)
    pipeline = Pipeline(cfg, hub, backends)
    await pipeline.start()

    ui_client = FakeUiClient()
    hub.ui.add(ui_client)

    editor_client = FakeEditorClient(pipeline, student_id=sid)

    try:
        from analysis.analyzer import _DEFAULT
        _DEFAULT.reset()
    except Exception:
        pass

    try:
        yield pipeline, editor_client, ui_client
    finally:
        await pipeline.stop()
        try:
            from analysis.analyzer import _DEFAULT
            _DEFAULT.reset()
        except Exception:
            pass


@pytest.fixture
def repo_path() -> Path:
    return repo_root


@pytest.fixture
def lessons_path() -> Path:
    return repo_root / "lessons"
