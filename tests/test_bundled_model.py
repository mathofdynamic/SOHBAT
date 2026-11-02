from sohbat import config as config_module
from sohbat.config import Config


def test_fresh_install_uses_bundled_model(tmp_path, monkeypatch):
    application = tmp_path/'app'
    model = application/'models'/'tiny-streaming-en'
    model.mkdir(parents=True)
    monkeypatch.setattr(config_module, 'ROOT', tmp_path/'preferences')
    monkeypatch.setattr(config_module, 'LEGACY_ROOT', tmp_path/'legacy')
    monkeypatch.setattr(config_module.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(config_module.sys, 'executable', str(application/'SOHBAT.exe'))
    assert Config.load().model_path == str(model)


def test_upgrade_preserves_preferences_and_external_model(tmp_path, monkeypatch):
    external = tmp_path/'external-model'
    external.mkdir()
    monkeypatch.setattr(config_module, 'ROOT', tmp_path/'preferences')
    monkeypatch.setattr(config_module, 'LEGACY_ROOT', tmp_path/'legacy')
    original = Config(model_path=str(external), hotkey='<alt>+<space>', autostart=True)
    original.save()
    before = (config_module.ROOT/'config.json').read_bytes()
    assert Config.load() == original
    assert (config_module.ROOT/'config.json').read_bytes() == before

def test_missing_larger_model_falls_back_with_tiny_architecture(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, 'ROOT', tmp_path/'preferences')
    monkeypatch.setattr(config_module, 'LEGACY_ROOT', tmp_path/'legacy')
    bundled = tmp_path/'tiny'
    bundled.mkdir()
    monkeypatch.setattr(config_module, 'bundled_model_path', lambda: str(bundled))
    Config(model_path=str(tmp_path/'missing'), model_arch=5).save()
    loaded = Config.load()
    assert loaded.model_path == str(bundled)
    assert loaded.model_arch == 2
