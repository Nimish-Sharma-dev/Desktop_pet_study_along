"""Typed config loader. Everything configurable lives in config.yaml."""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ServerCfg(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7777


class FalkorCfg(BaseModel):
    host: str = "localhost"
    port: int = 6379


class OllamaCfg(BaseModel):
    url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"


class CooldownCfg(BaseModel):
    bubble_seconds: float = 15
    same_mistake_minutes: float = 5


class MockCfg(BaseModel):
    analysis: bool = True
    tutor: bool = True
    graph: bool = True


class VoiceCfg(BaseModel):
    enabled: bool = False
    hotkey: str = "ctrl+alt+space"
    speak_replies: bool = True
    whisper_model: str = "models/ggml-base.en.bin"
    whisper_cmd: list[str] = ["whisper-cli", "-m", "{model}", "-f", "{wav}", "-nt", "-np"]
    piper_model: str = "models/en_US-lessac-medium.onnx"
    piper_cmd: list[str] = ["piper", "--model", "{model}", "--output_file", "{out}"]


class Config(BaseModel):
    server: ServerCfg = Field(default_factory=ServerCfg)
    falkordb: FalkorCfg = Field(default_factory=FalkorCfg)
    ollama: OllamaCfg = Field(default_factory=OllamaCfg)
    debounce_seconds: float = 1.5
    llm_timeout_seconds: float = 30
    min_confidence: float = 0.25
    sleep_after_seconds: float = 300
    cooldowns: CooldownCfg = Field(default_factory=CooldownCfg)
    allowlisted_paths: list[str] = ["~/tutor-lessons"]
    default_student: str = "local-user"
    mock: MockCfg = Field(default_factory=MockCfg)
    voice: VoiceCfg = Field(default_factory=VoiceCfg)

    def allowlist(self) -> list[Path]:
        return [Path(p).expanduser().resolve() for p in self.allowlisted_paths]

    def is_allowed(self, file: str) -> bool:
        """True only for files inside an allowlisted folder (and not obvious secret files)."""
        if not file:
            return False
        p = Path(file).expanduser().resolve()
        name = p.name.lower()
        if name.startswith(".env") or name.endswith((".pem", ".key")):
            return False
        return any(p == r or r in p.parents for r in self.allowlist())


def load_config(path: str | None = None) -> Config:
    path = path or os.environ.get("TUTOR_CONFIG") or str(Path(__file__).with_name("config.yaml"))
    p = Path(path)
    data = yaml.safe_load(p.read_text()) if p.is_file() else {}
    return Config.model_validate(data or {})
