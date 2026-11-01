import json

import sohbat.config as config_module
from sohbat.config import Config


def test_legacy_settings_and_managed_models_migrate(tmp_path, monkeypatch):
    legacy = tmp_path / 'legacy'
    current = tmp_path / 'current'
    model = legacy / 'models' / 'tiny-streaming-en'
    model.mkdir(parents=True)
    (model / 'streaming_config.json').write_text('{}')
    (legacy / 'config.json').write_text(json.dumps({
        'hotkey': '<ctrl>+<cmd>', 'model_path': str(model),
        'theme': 'dark', 'autostart': True,
    }))
    monkeypatch.setattr(config_module, 'ROOT', current)
    monkeypatch.setattr(config_module, 'LEGACY_ROOT', legacy)
    result = Config.load()
    assert result.theme == 'dark'
    assert result.autostart
    assert result.model_path == str(current / 'models' / 'tiny-streaming-en')
    assert (current / 'models' / 'tiny-streaming-en' / 'streaming_config.json').is_file()
    assert (legacy / 'config.json').is_file()
    assert Config.load() == result


def test_existing_sohbat_settings_take_precedence(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, 'ROOT', tmp_path / 'current')
    monkeypatch.setattr(config_module, 'LEGACY_ROOT', tmp_path / 'legacy')
    saved = Config(theme='light')
    saved.save()
    config_module.LEGACY_ROOT.mkdir()
    (config_module.LEGACY_ROOT / 'config.json').write_text('{invalid')
    assert Config.load().theme == 'light'
