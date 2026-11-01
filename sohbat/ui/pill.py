"""Nonactivating translucent island with interruptible critically damped motion."""
import ctypes
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget

from sohbat.ui.typography import install_font


class Spring:
    def __init__(self, value, omega=30.0):
        self.value, self.velocity, self.target, self.omega = float(value), 0.0, float(value), omega

    def step(self, dt):
        offset = self.value - self.target
        carry = self.velocity + self.omega * offset
        decay = math.exp(-self.omega * dt)
        self.value = self.target + (offset + carry * dt) * decay
        self.velocity = (self.velocity - self.omega * carry * dt) * decay


class Pill(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint |
                         Qt.WindowType.WindowDoesNotAcceptFocus |
                         Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        install_font(QApplication.instance())
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.resize(520, 90)
        self.state, self.text, self.level, self.phase = '', '', 0.0, 0.0
        self.width_spring, self.height_spring = Spring(44), Spring(30)
        self.alpha = Spring(0, 36)
        self.reduced_motion = False
        self.reduced_transparency = False
        self.closing = False
        self.last_tick = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.dismiss = QTimer(self)
        self.dismiss.setSingleShot(True)
        self.dismiss.timeout.connect(self.fade_out)
        self.configure()

    def configure(self, reduced_motion=False, reduced_transparency=False):
        enabled = ctypes.c_int(1)
        ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0)
        self.reduced_motion = reduced_motion or not bool(enabled.value)
        self.reduced_transparency = reduced_transparency
        self.update()

    def fade_out(self):
        self.closing = True
        self.width_spring.target = 44
        self.height_spring.target = 30
        self.alpha.target = 0
        self.last_tick = time.perf_counter()
        self.timer.start()

    def show_state(self, state, text=''):
        changed = state != self.state or (state in ('done', 'error') and text != self.text) or not self.isVisible() or self.closing
        self.state, self.text = state, text
        widths = {'listening': 400, 'processing': 210, 'done': 178, 'error': 460}
        self.width_spring.target = widths.get(state, 300)
        self.height_spring.target = 56
        self.alpha.target = 1
        self.closing = False
        if not self.isVisible():
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            rect = screen.availableGeometry()
            self.move(rect.center().x()-self.width()//2, rect.bottom()-self.height()-24)
            self.show()
        if changed:
            self.dismiss.stop()
            if state in ('done', 'error'):
                self.dismiss.start((120 if text in ('', 'Inserted', 'Preview complete') else 1600) if state == 'done' else 4300)
        if self.reduced_motion:
            self.width_spring.value = self.width_spring.target
            self.height_spring.value = self.height_spring.target
        if not self.timer.isActive():
            self.last_tick = time.perf_counter()
            self.timer.start()
        self.update()

    def hideEvent(self, event):
        self.timer.stop()
        self.dismiss.stop()
        self.width_spring.value, self.height_spring.value, self.alpha.value = 44, 30, 0
        self.width_spring.velocity = self.height_spring.velocity = self.alpha.velocity = 0
        super().hideEvent(event)

    def tick(self):
        now = time.perf_counter()
        dt = min(.05, now-self.last_tick)
        self.last_tick = now
        if not self.reduced_motion:
            self.width_spring.step(dt)
            self.height_spring.step(dt)
        self.alpha.step(dt)
        if not self.reduced_motion:
            self.phase += dt * 7
        if self.closing and self.alpha.value < .012:
            self.hide()
            return
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        opacity = min(1.0, max(0.0, self.alpha.value))
        painter.setOpacity(opacity)
        width, height = self.width_spring.value, self.height_spring.value
        rect = QRectF((self.width()-width)/2, 68-height, width, height)
        radius = height/2
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setBrush(QColor(20, 23, 29, 248 if self.reduced_transparency else 224))
        painter.setPen(QPen(QColor(255, 255, 255, 48), 1))
        painter.drawPath(path)
        painter.setClipPath(path)
        reveal = max(0.0, min(1.0, (width-75)/120))
        painter.setOpacity(opacity*reveal)
        center = rect.center().y()
        x = rect.left()+24
        accent = QColor('#83b7ff') if self.state != 'error' else QColor('#ffbd72')
        painter.setPen(QPen(accent, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if self.state == 'listening':
            for index in range(5):
                pulse = .6 if self.reduced_motion else abs(math.sin(self.phase+index*.65))
                extent = 3 + self.level*17*pulse
                painter.drawLine(QPointF(x+index*4, center-extent/2), QPointF(x+index*4, center+extent/2))
        elif self.state == 'done':
            painter.drawLine(QPointF(x, center), QPointF(x+5, center+5))
            painter.drawLine(QPointF(x+5, center+5), QPointF(x+15, center-6))
        elif self.state == 'processing':
            painter.drawArc(QRectF(x, center-7, 14, 14), int(self.phase*130)*16, 250*16)
        else:
            painter.drawLine(QPointF(x+6, center-7), QPointF(x+6, center+2))
            painter.drawPoint(QPointF(x+6, center+7))
        font = QFont('Inter')
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        label = self.text or {'listening': 'Listening…', 'processing': 'Finishing…', 'done': 'Inserted', 'error': 'Please try again'}.get(self.state, '')
        if self.state == 'listening':
            label = label[-43:]
        text_rect = QRectF(rect.left()+58, rect.top(), max(0, width-80), height)
        label = painter.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, int(text_rect.width()))
        gradient = QLinearGradient(text_rect.topLeft(), text_rect.topRight())
        gradient.setColorAt(0, QColor(245, 247, 252, 150 if self.state == 'listening' and self.text else 255))
        gradient.setColorAt(.12, QColor('#f5f7fc'))
        gradient.setColorAt(1, QColor('#f5f7fc'))
        painter.setPen(QPen(gradient, 1))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
