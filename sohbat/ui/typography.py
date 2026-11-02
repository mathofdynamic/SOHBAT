"""Bundled typography shared by every SOHBAT surface."""
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from sohbat import __version__


def install_font(app: QCoreApplication | None) -> None:
    if not isinstance(app, QApplication):
        raise TypeError('SOHBAT requires a QApplication')
    path = Path(__file__).resolve().parents[1] / 'assets' / 'fonts' / 'Inter.ttf'
    font_id = QFontDatabase.addApplicationFont(str(path))
    if font_id < 0:
        raise RuntimeError('Bundled Inter font could not be loaded')
    font = QFont('Inter', 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    app.setApplicationName('SOHBAT')
    app.setApplicationVersion(__version__)
    app.setApplicationDisplayName('SOHBAT')
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parents[1] / 'assets' / 'brand' / 'app.ico')))

