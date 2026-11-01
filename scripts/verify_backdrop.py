"""Verify real backdrop blur over a controlled desktop pattern (Windows only)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from sohbat.inject import foreground
from sohbat.ui.pill import Pill


class Pattern(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        colors = ['#ef9999', '#a4c6f7', '#b1d9a3', '#f4d391']
        for x in range(0, self.width(), 6):
            color = colors[(x//100) % 4] if x % 12 else '#ffffff'
            painter.fillRect(x, 0, 6, self.height(), QColor(color))
        painter.setFont(QFont('Inter', 22))
        painter.setPen(QColor('#101010'))
        painter.drawText(10, 180, 'SHARP BACKGROUND TEXT   SHARP BACKGROUND TEXT')


def rgb(image):
    image = image.convertToFormat(image.Format.Format_RGBA8888)
    return np.frombuffer(image.bits(), dtype=np.uint8).reshape(image.height(), image.width(), 4)[:, :, :3].astype(float)


app = QApplication([])
host = Pattern(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
host.setGeometry(100, 100, 900, 320)
host.show()
host.activateWindow()
QTest.qWait(200)
output = Path('.perfection/blur')
output.mkdir(parents=True, exist_ok=True)


def grab():
    return host.screen().grabWindow(0, host.x(), host.y(), host.width(), host.height())


baseline = grab()
baseline.save(str(output/'before.png'))
original_focus = foreground()
pill = Pill()
pill.show_state('listening', 'Blurred desktop background')
pill.move(250, 200)
QTest.qWait(600)
blurred = grab()
blurred.save(str(output/'blurred.png'))
assert pill.backdrop.image is not None and not pill.backdrop.failed
ratio = blurred.devicePixelRatio()
left = round((pill.x()+(pill.width()-pill.width_spring.value)/2-host.x())*ratio)
top = round((pill.y()+68-pill.height_spring.value-host.y())*ratio)
width = round(pill.width_spring.value*ratio)
before, after = rgb(baseline.toImage()), rgb(blurred.toImage())
area = (slice(top+8, top+12), slice(left+60, left+width-30))
before_edges = float(np.abs(np.diff(before[area], axis=1)).mean())
after_edges = float(np.abs(np.diff(after[area], axis=1)).mean())
corner_difference = float(np.abs(before[top+2, left+2]-after[top+2, left+2]).max())
report = {
    'background_edge_energy_before': before_edges,
    'background_edge_energy_blurred': after_edges,
    'edge_energy_ratio': after_edges/before_edges,
    'corner_difference': corner_difference,
    'focus_unchanged': foreground() == original_focus,
    'sample_and_blur_ms': pill.backdrop.capture_ms,
    'click_through': bool(pill.windowFlags() & Qt.WindowType.WindowTransparentForInput),
}
assert after_edges < before_edges*.1
assert corner_difference == 0
assert report['focus_unchanged']
pill.configure(False, True)
QTest.qWait(200)
grab().save(str(output/'reduced.png'))
assert pill.backdrop.image is None
pill.backdrop.failed = True
pill.configure(False, False)
QTest.qWait(200)
grab().save(str(output/'fallback.png'))
pill.hide()
QTest.qWait(100)
report['hidden_timer_stopped'] = not pill.timer.isActive()
report['cached_pixels_released'] = pill.backdrop.image is None
report['reduced_transparency_and_failure_fallback'] = True
(output/'report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
pill.backdrop.close()
host.close()
