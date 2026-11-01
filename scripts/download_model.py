import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moonshine_voice import ModelArch
from moonshine_voice.download import get_model_for_language
from sohbat.config import Config

for attempt in range(3):
    try:
        path, arch = get_model_for_language(wanted_language="en",
                                            wanted_model_arch=ModelArch.TINY_STREAMING)
        break
    except Exception as error:
        print(f"Model download attempt {attempt + 1} failed: {error}", file=sys.stderr)
        if attempt == 2:
            raise SystemExit("Download unavailable. Retry scripts/download-model.ps1 later.")
        time.sleep(1)
config = Config.load()
config.model_path = str(path)
config.save()
print(f"Downloaded architecture {arch} to {path}")
