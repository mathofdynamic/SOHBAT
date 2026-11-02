from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def make_tray(settings, pause, quit_app):
    tray = QSystemTrayIcon(QIcon(str(Path(__file__).resolve().parents[1] / 'assets' / 'brand' / 'logo.png')))
    tray.setToolTip("SOHBAT · Hold Ctrl+Windows to dictate")
    open_timer = QTimer(tray)
    open_timer.setSingleShot(True)
    open_timer.timeout.connect(settings)

    def open_settings():
        # Let the shell/tray popup release focus before activating preferences.
        open_timer.start(40)

    def activated(reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            open_settings()

    tray.activated.connect(activated)
    menu = QMenu()
    for label, callback in [("Settings", open_settings), ("Pause", pause), ("Quit", quit_app)]:
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)
    tray.setContextMenu(menu)
    tray.show()
    return tray, menu
