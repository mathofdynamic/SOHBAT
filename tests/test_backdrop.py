from types import SimpleNamespace

from sohbat import backdrop_windows as backdrop_module
from sohbat.backdrop_windows import DesktopBackdrop


def test_sampling_failure_restores_window_capture_policy(monkeypatch):
    calls = []
    monkeypatch.setattr(backdrop_module.user32, 'GetWindowDisplayAffinity', lambda *args: 1)
    monkeypatch.setattr(backdrop_module.user32, 'SetWindowDisplayAffinity',
                        lambda hwnd, value: calls.append(value) or 1)

    def fail_capture():
        raise RuntimeError('Screen capture unavailable')

    widget = SimpleNamespace(winId=lambda: 123, isVisible=lambda: True, screen=fail_capture)
    backdrop = DesktopBackdrop()
    backdrop.failed = False
    backdrop.refresh(widget, force=True)
    assert calls == [0x11, 0]
    assert backdrop.failed
    assert backdrop.image is None
    assert not backdrop._sampling


def test_hidden_material_releases_cached_pixels():
    backdrop = DesktopBackdrop()
    backdrop.image = object()
    backdrop.last_capture = 10
    backdrop.hide()
    assert backdrop.image is None
    assert backdrop.last_capture == 0
