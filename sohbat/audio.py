import threading
from collections import deque
from math import gcd
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly


class Microphone:
    def __init__(self):
        self.blocks: deque = deque(maxlen=100)
        self.lock = threading.Lock()
        self.level = 0.0
        self.error = ""
        self.stream: Any = None
        self.rate = 16000

    def start(self, device=None):
        self.blocks.clear()
        self.error = ""
        info = sd.query_devices(device, "input")
        self.rate = int(info["default_samplerate"])
        try:
            sd.check_input_settings(device=device, channels=1, samplerate=16000, dtype="float32")
            self.rate = 16000
        except sd.PortAudioError:
            pass
        self.stream = sd.InputStream(device=device, channels=1, samplerate=self.rate,
                                     dtype="float32", blocksize=self.rate // 50,
                                     callback=self._capture)
        self.stream.start()

    def _capture(self, data, frames, timing, status):
        with self.lock:
            if status or len(self.blocks) == self.blocks.maxlen:
                self.error = "Microphone audio lost. Try again."
            self.blocks.append(data[:, 0].copy())
        self.level = min(1.0, float(np.sqrt(np.mean(data * data))) * 8)

    def drain(self):
        with self.lock:
            blocks = list(self.blocks)
            self.blocks.clear()
        if not blocks:
            return np.empty(0, dtype=np.float32)
        samples = np.concatenate(blocks)
        if self.rate != 16000:
            divisor = gcd(self.rate, 16000)
            samples = resample_poly(samples, 16000 // divisor, self.rate // divisor)
        return np.asarray(samples, dtype=np.float32)

    def stop(self):
        if self.stream is not None:
            stream = self.stream
            self.stream = None
            try:
                stream.stop()
            finally:
                stream.close()
