import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from platformdirs import user_config_dir

ROOT = Path(user_config_dir("SOHBAT", appauthor=False))
LEGACY_ROOT = Path(user_config_dir("Flowlet", appauthor=False))


def bundled_model_path() -> str:
    if getattr(sys, 'frozen', False):
        path = Path(sys.executable).parent / 'models' / 'tiny-streaming-en'
        if path.is_dir():
            return str(path)
    return ''


@dataclass
class Config:
    hotkey: str = "<ctrl>+<cmd>"
    mode: str = "hold"
    mic_device: int | None = None
    paste_method: str = "clipboard"
    autostart: bool = False
    pill_position: str = "bottom-center"
    strip_fillers: bool = True
    model_path: str = ""
    compatibility: bool = True
    theme: str = "system"
    reduced_motion: bool = False
    reduced_transparency: bool = False

    @classmethod
    def load(cls):
        path = ROOT / "config.json"
        legacy = False
        if not path.exists():
            path = LEGACY_ROOT / "config.json"
            legacy = True
        if not path.exists():
            return cls(model_path=bundled_model_path())
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise TypeError("Configuration must be an object")
        result = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if result.mode not in ("hold", "toggle") or result.paste_method not in ("clipboard", "typing"):
            raise ValueError("Invalid dictation mode or paste method")
        if not isinstance(result.hotkey, str) or not isinstance(result.model_path, str):
            raise TypeError("Invalid hotkey or model path")
        if result.mic_device is not None and (type(result.mic_device) is not int or result.mic_device < 0):
            raise ValueError("Invalid microphone device")
        if type(result.autostart) is not bool or type(result.strip_fillers) is not bool:
            raise ValueError("Invalid configuration toggle")
        if not result.model_path or not Path(result.model_path).is_dir():
            result.model_path = bundled_model_path() or result.model_path
        if legacy:
            model = Path(result.model_path)
            legacy_models = LEGACY_ROOT / "models"
            if model.is_dir() and model.resolve().is_relative_to(legacy_models.resolve()):
                destination = ROOT / "models" / model.resolve().relative_to(legacy_models.resolve())
                shutil.copytree(model, destination, dirs_exist_ok=True)
                result.model_path = str(destination)
            result.save()
        return result

    def save(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        target = ROOT / "config.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8-sig")
        temporary.replace(target)

