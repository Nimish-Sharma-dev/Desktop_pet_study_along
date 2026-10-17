"""Local push-to-talk voice: sounddevice -> whisper.cpp (STT) -> tutor pipeline -> Piper (TTS).
No network. Heavy imports are lazy so the daemon runs without voice deps installed."""
from __future__ import annotations

import logging
import subprocess
import tempfile
import threading
import wave
from pathlib import Path

log = logging.getLogger("tutor.voice")
SR = 16000  # whisper.cpp wants 16 kHz mono 16-bit


class VoiceService:
    def __init__(self, cfg, on_text, on_state=None):
        self.cfg, self.on_text = cfg, on_text
        self.on_state = on_state or (lambda s: None)
        self._lock = threading.Lock()
        self._stream = None
        self._frames: list = []
        self._hotkey = None

    def start_hotkey(self) -> None:
        from .hotkey import HoldToTalk
        self._hotkey = HoldToTalk(self.cfg.hotkey, self.start_recording, self.stop_recording)
        self._hotkey.start()
        log.info("hold %s to talk", self.cfg.hotkey)

    def shutdown(self) -> None:
        if self._hotkey:
            self._hotkey.stop()

    # ---- recording
    def start_recording(self) -> None:
        import sounddevice as sd
        with self._lock:
            if self._stream:
                return
            self._frames = []
            self._stream = sd.InputStream(samplerate=SR, channels=1, dtype="int16",
                                          callback=lambda indata, n, t, s: self._frames.append(indata.copy()))
            self._stream.start()
        self.on_state("curious")  # "listening"

    def stop_recording(self) -> None:
        with self._lock:
            s, self._stream = self._stream, None
            if not s:
                return
            s.stop()
            s.close()
            frames, self._frames = self._frames, []
        import numpy as np
        audio = np.concatenate(frames) if frames else np.zeros(0, dtype="int16")
        if len(audio) < SR * 0.4:  # accidental tap
            self.on_state("idle")
            return
        self.on_state("thinking")
        threading.Thread(target=self._transcribe_and_dispatch, args=(audio,), daemon=True).start()

    def _transcribe_and_dispatch(self, audio) -> None:
        try:
            text = self.transcribe(audio)
            if not text:
                self.on_state("idle")
                return
            log.info("heard: %s", text)
            self.on_text(text)  # same tutor pipeline as typed replies
        except Exception:
            log.exception("voice pipeline failed")
            self.on_state("idle")

    # ---- speech to text (whisper.cpp)
    def transcribe(self, audio) -> str:
        with tempfile.TemporaryDirectory() as d:
            wav = Path(d) / "in.wav"
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(SR)
                w.writeframes(audio.tobytes())
            cmd = [a.format(model=self.cfg.whisper_model, wav=str(wav)) for a in self.cfg.whisper_cmd]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
        text = " ".join(l.strip() for l in r.stdout.splitlines() if l.strip())
        if text.startswith("[") and text.endswith("]"):  # e.g. [BLANK_AUDIO]
            return ""
        return text

    # ---- text to speech (Piper)
    def speak(self, text: str) -> None:
        import numpy as np
        import sounddevice as sd
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.wav"
            cmd = [a.format(model=self.cfg.piper_model, out=str(out)) for a in self.cfg.piper_cmd]
            subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=60, check=True)
            with wave.open(str(out)) as w:
                sr = w.getframerate()
                data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        sd.play(data, sr)
        sd.wait()
