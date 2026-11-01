import json
import re
from pathlib import Path

import numpy as np
import pytest
from scipy.io import wavfile
from scipy.signal import resample_poly

from sohbat.engine.moonshine_engine import MoonshineEngine


def test_real_streaming():
    root = Path("models/tiny-streaming-en")
    if not root.exists():
        pytest.skip("Local model not installed")
    engine = MoonshineEngine(str(root))
    try:
        phrases = json.loads(Path("tests/fixtures/expected.json").read_text(encoding="utf-8-sig"))
        for index, expected in enumerate(phrases):
            rate, audio = wavfile.read(f"tests/fixtures/clip{index}.wav")
            audio = resample_poly(audio.astype(np.float32)/32768, 16000, rate)
            engine.start_stream()
            partial_before_end = False
            for offset in range(0, len(audio), 1600):
                engine.feed_audio(audio[offset:offset+1600].astype(np.float32))
                if offset+1600 < len(audio) and engine.partial_text():
                    partial_before_end = True
            actual = engine.finalize()
            words = lambda text: re.findall(r"\w+", text.lower())
            reference, result = words(expected), words(actual)
            assert len(reference) == len(result)
            assert sum(a != b for a, b in zip(reference, result)) / len(reference) <= .15
            assert partial_before_end
    finally:
        engine.close()
