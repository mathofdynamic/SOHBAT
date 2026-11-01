import ctypes
import time
from typing import Any

from pynput import keyboard


class Gesture:
    def __init__(self, callback, mode="hold", clock=time.monotonic):
        self.callback, self.mode, self.clock = callback, mode, clock
        self.down: Any = None
        self.active = False

    def press(self):
        if self.down is not None:
            return
        self.down = self.clock()
        if self.mode == "hold":
            self.active = True
            self.callback("start")

    def release(self):
        if self.down is None:
            return
        elapsed = self.clock() - self.down
        self.down = None
        if self.mode == "hold":
            self.active = False
            self.callback("stop" if elapsed >= .25 else "cancel")
        elif elapsed >= .25:
            self.active = not self.active
            self.callback("start" if self.active else "stop")


class GlobalHotkey:
    def __init__(self, chord, mode, callback):
        self.gesture = Gesture(callback, mode)
        self.keys = set(keyboard.HotKey.parse(chord))
        self.pressed = set()
        self.armed = not any(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000
                             for vk in range(8, 256))
        self.listener = keyboard.Listener(on_press=self.press, on_release=self.release)
        self.listener.start()

    def press(self, key):
        if not self.armed:
            return
        self.pressed.add(self.listener.canonical(key))
        if self.keys <= self.pressed:
            self.gesture.press()

    def release(self, key):
        if not self.armed:
            self.armed = not any(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000
                                 for vk in range(8, 256))
            return
        self.pressed.discard(self.listener.canonical(key))
        if not self.keys <= self.pressed:
            self.gesture.release()

    def close(self):
        self.listener.stop()

    def reset(self):
        self.gesture.active = False
        self.gesture.down = None
