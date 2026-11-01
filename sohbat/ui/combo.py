from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QStyle, QStyleOptionComboBox, QStylePainter


class ComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.currentTextChanged.connect(self.setToolTip)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = self.fontMetrics().elidedText(
            option.currentText, Qt.TextElideMode.ElideRight, max(0, self.width()-42))
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)
