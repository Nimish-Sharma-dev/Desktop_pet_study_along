"""Global hold-to-talk hotkey via pynput. e.g. "ctrl+alt+space"."""
from __future__ import annotations

from pynput import keyboard

K = keyboard.Key
_ALIASES = {
    "ctrl": {K.ctrl, K.ctrl_l, K.ctrl_r}, "alt": {K.alt, K.alt_l, K.alt_r, getattr(K, "alt_gr", K.alt)},
    "shift": {K.shift, K.shift_l, K.shift_r}, "cmd": {K.cmd, K.cmd_l, K.cmd_r},
    "space": {K.space}, "f9": {K.f9}, "f10": {K.f10},
}


def _norm(key):
    if isinstance(key, keyboard.KeyCode):
        return key.char.lower() if key.char else key.vk
    return key


class HoldToTalk:
    def __init__(self, combo: str, on_press, on_release):
        self.req = [_ALIASES.get(p.strip().lower(), {p.strip().lower()}) for p in combo.split("+")]
        self.on_press_cb, self.on_release_cb = on_press, on_release
        self.down: set = set()
        self.active = False
        self.listener = keyboard.Listener(on_press=self._press, on_release=self._release)

    def _satisfied(self) -> bool:
        return all(self.down & alts for alts in self.req)

    def _press(self, key):
        self.down.add(_norm(key))
        if not self.active and self._satisfied():
            self.active = True
            self.on_press_cb()

    def _release(self, key):
        self.down.discard(_norm(key))
        if self.active and not self._satisfied():
            self.active = False
            self.on_release_cb()

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()
