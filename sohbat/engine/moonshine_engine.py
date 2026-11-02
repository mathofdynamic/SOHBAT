from pathlib import Path
from typing import Any

import numpy as np
from moonshine_voice import ModelArch, Transcriber
from numpy.typing import NDArray


class MoonshineEngine:
    """All methods are called on one worker thread."""

    def __init__(self, model_path: str, model_arch: int = 2):
        if not model_path or not Path(model_path).is_dir():
            raise FileNotFoundError("Model missing. Run scripts/download-model.ps1 first.")
        self.transcriber = Transcriber(model_path, ModelArch(model_arch))
        self.stream: Any = None
        self.lines: dict[int, str] = {}

    def start_stream(self) -> None:
        self.lines.clear()
        self.stream = self.transcriber.create_stream(update_interval=0.15)
        self.stream.add_listener(self._event)
        self.stream.start()

    def _event(self, event):
        if hasattr(event, "error"):
            raise event.error
        self.lines[event.line.line_id] = event.line.text

    def feed_audio(self, samples: NDArray[np.float32]) -> None:
        if self.stream is not None:
            self.stream.add_audio(samples.tolist(), 16000)

    def partial_text(self) -> str:
        return " ".join(self.lines.values()).strip()

    def finalize(self) -> str:
        if self.stream is None:
            return ""
        try:
            result = self.stream.stop()
            if result is None:
                raise RuntimeError("Speech processing failed")
            return " ".join(line.text for line in result.lines).strip()
        finally:
            self.stream.close()
            self.stream = None

    def close(self) -> None:
        if self.stream is not None:
            self.stream.close()
        self.transcriber.close()
