from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def make_tray(settings, pause, quit_app):
    tray = QSystemTrayIcon(QIcon(str(Path(__file__).resolve().parents[1] / 'assets' / 'brand' / 'logo.png')))
    tray.setToolTip("SOHBAT · Hold Ctrl+Windows to dictate")
    menu = QMenu()
    for label, callback in [("Settings", settings), ("Pause", pause), ("Quit", quit_app)]:
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)
    tray.setContextMenu(menu)
    tray.show()
    return tray, menu
