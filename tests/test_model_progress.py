import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication

from sohbat.config import Config
from sohbat.ui.settings import Settings


def test_model_progress_and_retry_states(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(Settings, 'refresh_mics', lambda self: None)
    window = Settings(Config(), lambda *args: None)
    window.navigation.setCurrentRow(3)
    window.downloading_arch = 4
    window.show_download_progress(.42, 'adapter.ort')
    assert window.download_progress.value() == 420
    assert window.download_percent.text() == '42%'
    assert 'adapter.ort' not in window.download_status.text()
    window.model_downloaded('unused', 4)
    assert window.download_progress.maximum() == 0
    window.show_model_result('Download failed: Offline')
    assert window.download_button.isEnabled()
    assert window.download_button.text() == 'Try again'
    assert 'Offline' in window.download_detail.text()
    assert not window.save.isVisible()
    window.close()
    app.processEvents()
