"""Run real cached-model streaming checks; no network."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import psutil
from scipy.io import wavfile
from scipy.signal import resample_poly
from math import gcd
from sohbat.config import Config
from sohbat.engine.moonshine_engine import MoonshineEngine

started = time.perf_counter()
engine = MoonshineEngine(Config.load().model_path)
report = {'model_load_seconds': time.perf_counter() - started, 'clips': []}
expected = json.loads(Path('tests/fixtures/expected.json').read_text(encoding='utf-8-sig'))
for index, phrase in enumerate(expected):
    rate, samples = wavfile.read(f'tests/fixtures/clip{index}.wav')
    samples = samples.astype(np.float32) / 32768
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    divisor = gcd(rate, 16000)
    samples = resample_poly(samples, 16000 // divisor, rate // divisor).astype(np.float32)
    engine.start_stream()
    first_partial = None
    for offset in range(0, len(samples), 1600):
        engine.feed_audio(samples[offset:offset+1600])
        if first_partial is None and engine.partial_text():
            first_partial = (offset+1600)/16000
    start = time.perf_counter()
    actual = engine.finalize()
    report['clips'].append(dict(expected=phrase, actual=actual,
                                duration=len(samples)/16000, first_partial=first_partial,
                                finalize_ms=(time.perf_counter()-start)*1000))
time.sleep(2)
process = psutil.Process()
report['rss_mb'] = process.memory_info().rss / 1024**2
report['idle_cpu_percent'] = process.cpu_percent(interval=3)
engine.close()
Path('.perfection').mkdir(exist_ok=True)
Path('.perfection/benchmark.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
