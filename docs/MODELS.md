# Models

SOHBAT defaults to Moonshine Tiny Streaming English, architecture 2. Normal startup reads local model files and never starts a download.

## Automatic setup

Run `./scripts/download-model.ps1` from the repository root.

## Manual setup

Download all eight files from the official model manifest used by `moonshine-voice==0.1.5`:

| File | Bytes |
|---|---:|
| [adapter.ort](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/adapter.ort) | 1,319,664 |
| [cross_kv.ort](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/cross_kv.ort) | 1,287,544 |
| [decoder_kv.ort](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/decoder_kv.ort) | 32,583,720 |
| [encoder.ort](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/encoder.ort) | 7,675,440 |
| [frontend.model.ort](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/frontend.model.ort) | 23,344 |
| [frontend.weights.ort](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/frontend.weights.ort) | 2,093,464 |
| [streaming_config.json](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/streaming_config.json) | 509 |
| [tokenizer.bin](https://download.moonshine.ai/model/tiny-streaming-en/quantized_26_08_21/tokenizer.bin) | 249,974 |

Save them directly inside `models/tiny-streaming-en`, keeping filenames unchanged. Then configure SOHBAT:

```powershell
.venv/Scripts/python -c "from pathlib import Path; from sohbat.config import Config; c=Config.load(); c.model_path=str(Path('models/tiny-streaming-en').resolve()); c.save()"
```

Run `.venv/Scripts/python scripts/benchmark.py` to check recognition with the supplied fixtures. File integrity should be checked against the installed package's native manifest when obtaining weights through an alternative download method.

Small and Medium Streaming use architecture numbers 4 and 5. Both downloader and engine constructor must be changed together. Higher-capacity models change memory and latency. Refer to the [official model documentation](https://moonshine-voice.readthedocs.io/en/stable/) before changing architecture.
