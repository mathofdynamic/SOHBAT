from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox


class Switch(QCheckBox):
    """A keyboard-accessible checkbox with a position-based on/off affordance."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(44, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def hitButton(self, position):
        return self.rect().contains(position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#007aff' if self.isChecked() else '#86868f'))
        painter.drawRoundedRect(QRectF(3, 5, 38, 22), 11, 11)
        painter.setBrush(QColor('white'))
        painter.drawEllipse(QRectF(23 if self.isChecked() else 5, 7, 18, 18))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#007aff'), 1.5, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(QRectF(1, 2, 42, 28), 13, 13)
