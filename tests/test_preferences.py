from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from sohbat.config import Config
from sohbat.ui.settings import Settings
from sohbat.ui.tray import make_tray


def test_tray_opens_preferences_and_reports_save_errors():
    app = QApplication.instance() or QApplication([])
    received = []
    window = Settings(Config(), lambda *args: received.append(args))
    tray, menu = make_tray(window.open_preferences, lambda: None, lambda: None)
    menu.actions()[0].trigger()
    app.processEvents()
    assert window.isVisible()
    window.navigation.setFocus()
    QTest.keyClick(window.navigation, Qt.Key.Key_Down)
    assert window.pages.currentIndex() == 1
    window.compatibility.setFocus()
    original = window.compatibility.isChecked()
    QTest.keyClick(window.compatibility, Qt.Key.Key_Space)
    assert window.compatibility.isChecked() != original
    window.compatibility.setChecked(False)
    window.submit()
    assert received[-1][6] is False
    assert "Saved." in window.feedback.text()

    def fail(*args):
        raise ValueError("Invalid shortcut")

    window.apply_changes = fail
    window.submit()
    assert "Invalid shortcut" in window.feedback.text()
    window.close()
    tray.hide()
