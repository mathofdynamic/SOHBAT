"""Blur the desktop under our own window, without capturing the island itself.

Screen pixels stay in memory. The window's capture-affinity setting is restored
immediately after sampling; normal screenshots can still include the overlay.
"""
import ctypes
import logging
import sys
import time
from ctypes import wintypes

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsBlurEffect, QGraphicsPixmapItem, QGraphicsScene

logger = logging.getLogger(__name__)
user32 = ctypes.windll.user32
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
user32.GetWindowDisplayAffinity.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowDisplayAffinity.restype = wintypes.BOOL


class DesktopBackdrop:
    padding = 32

    def __init__(self):
        self.image = None
        self.failed = sys.getwindowsversion().build < 19041
        self.last_capture = 0.0
        self.capture_ms = 0.0
        self._sampling = False

    def refresh(self, widget, force=False):
        if self.failed or self._sampling:
            return
        now = time.perf_counter()
        if not force and now-self.last_capture < .1:
            return
        self._sampling = True
        self.last_capture = now
        previous = wintypes.DWORD()
        hwnd = int(widget.winId())
        affinity_changed = False
        try:
            if widget.isVisible():
                if not user32.GetWindowDisplayAffinity(hwnd, ctypes.byref(previous)):
                    raise ctypes.WinError()
                if not user32.SetWindowDisplayAffinity(hwnd, 0x11):
                    raise ctypes.WinError()
                affinity_changed = True

            try:
                margin = self.padding
                source = widget.screen().grabWindow(0, widget.x()-margin, widget.y()-margin,
                    widget.width()+margin*2, widget.height()+margin*2)
            finally:
                if affinity_changed:
                    if not user32.SetWindowDisplayAffinity(hwnd, previous.value):
                        raise ctypes.WinError()
                    affinity_changed = False
            if source.isNull():
                raise RuntimeError('Desktop sampling returned an empty image')
            # Work at half resolution. The cached material is intentionally diffuse;
            # foreground text and waveform are painted separately at native resolution.
            ratio = source.devicePixelRatio()
            reduced = source.scaled(max(1, source.width()//2), max(1, source.height()//2),
                Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            reduced.setDevicePixelRatio(1)
            scene = QGraphicsScene()
            item = QGraphicsPixmapItem(reduced)
            effect = QGraphicsBlurEffect()
            effect.setBlurRadius(16*ratio)
            effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
            item.setGraphicsEffect(effect)
            scene.addItem(item)
            image = QImage(reduced.size(), QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            try:
                scene.render(painter, QRectF(image.rect()), QRectF(reduced.rect()))
            finally:
                painter.end()
            result = QPixmap.fromImage(image).scaled(source.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            result.setDevicePixelRatio(ratio)
            self.image = result
            self.capture_ms = (time.perf_counter()-now)*1000
        except Exception:
            logger.exception('Backdrop blur unavailable; using an opaque surface')
            self.failed = True
            self.image = None
        finally:
            if affinity_changed:
                user32.SetWindowDisplayAffinity(hwnd, previous.value)
            self._sampling = False

    def hide(self):
        self.image = None
        self.last_capture = 0.0

    def close(self):
        self.hide()
