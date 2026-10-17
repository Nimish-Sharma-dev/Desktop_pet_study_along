"""Sanity check for the offline voice stack:  python -m voice.check"""
import shutil
from pathlib import Path

from config import load_config

cfg = load_config().voice
print("whisper binary :", shutil.which(cfg.whisper_cmd[0]) or "NOT FOUND")
print("whisper model  :", cfg.whisper_model, "OK" if Path(cfg.whisper_model).is_file() else "MISSING")
print("piper binary   :", shutil.which(cfg.piper_cmd[0]) or "NOT FOUND")
print("piper model    :", cfg.piper_model, "OK" if Path(cfg.piper_model).is_file() else "MISSING")
try:
    import sounddevice as sd
    print("input devices  :", [d["name"] for d in sd.query_devices() if d["max_input_channels"] > 0][:3])
except Exception as e:
    print("sounddevice    : FAILED", e)
try:
    import pynput  # noqa: F401
    print("pynput         : OK (macOS: grant Accessibility + Input Monitoring; Wayland: use /api/voice/start|stop)")
except Exception as e:
    print("pynput         : FAILED", e)
