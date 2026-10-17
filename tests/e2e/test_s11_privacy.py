"""Scenario S11: Privacy enforcement and secret redaction."""

from __future__ import annotations

import asyncio
from pathlib import Path
from redact import redact
from tests.e2e.conftest import stack_context


def test_s11_allowlist_enforcement_and_secret_redaction(tmp_path):
    """
    S11 Privacy: a file outside the allowlist is never sent;
    a hard-coded API key in a buffer is redacted before it reaches the daemon or the graph.
    """
    async def run():
        async with stack_context() as (pipeline, editor, ui):
            # 1. File outside allowlist
            outside_file = tmp_path / "private_outside" / "confidential.py"
            outside_file.parent.mkdir(parents=True, exist_ok=True)
            outside_file.write_text("def secret(): pass\n", encoding="utf-8")

            ui.clear()
            await editor.edit(str(outside_file), "def secret(): pass\n")
            await asyncio.sleep(0.2)
            # Nothing should be in pipeline batches or emitted to UI
            assert len(ui.bubbles) == 0
            assert len(ui.messages) == 0

            # 2. Secret Redaction Unit & Ingest Pipeline
            raw_text_with_keys = (
                "OPENAI_KEY = 'sk-proj-abc123456789012345678901234567890'\n"
                "AWS_SECRET = 'AKIAIOSFODNN7EXAMPLE'\n"
                "def test(): return 42\n"
            )
            redacted = redact(raw_text_with_keys)
            assert "sk-proj-" not in redacted
            assert "AKIAIOSFODNN7EXAMPLE" not in redacted
            assert "[REDACTED" in redacted

            # 3. Pipeline Ingest Redaction
            allowlisted_file = pipeline.cfg.allowlist()[0] / "binary-search" / "starter" / "solution.py"
            captured_content = []
            orig_analyze = pipeline.b.analysis.analyze
            
            def intercept_analyze(batch, lesson):
                for e in batch:
                    captured_content.append(e.get("content", ""))
                return orig_analyze(batch, lesson)

            pipeline.b.analysis.analyze = intercept_analyze
            await editor.edit(str(allowlisted_file), raw_text_with_keys)
            await asyncio.sleep(0.3)

            assert len(captured_content) > 0
            for content in captured_content:
                assert "sk-proj-" not in content
                assert "AKIAIOSFODNN7EXAMPLE" not in content

    asyncio.run(run())
