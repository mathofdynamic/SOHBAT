import ctypes
import logging
from ctypes import wintypes

from pynput.keyboard import Controller, Key, KeyCode
from PySide6.QtCore import QMimeData, QTimer
from PySide6.QtWidgets import QApplication

from sohbat.accessibility import editable_focus

ctypes.windll.user32.GetForegroundWindow.restype = ctypes.c_void_p


class GuiThreadInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT)]


ctypes.windll.user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GuiThreadInfo)]
ctypes.windll.user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]


def has_text_focus(compatibility=True):
    local = QApplication.focusWidget()
    if local is not None and foreground() == int(local.window().winId()):
        return hasattr(local, "insert") and not getattr(local, "isReadOnly", lambda: False)()
    accessible = editable_focus()
    if accessible is not None:
        return accessible
    info = GuiThreadInfo()
    info.cbSize = ctypes.sizeof(info)
    if not ctypes.windll.user32.GetGUIThreadInfo(0, ctypes.byref(info)) or not info.hwndFocus:
        return False
    name = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetClassNameW(info.hwndFocus, name, 256)
    # Browser/editor canvas controls expose editability through accessibility,
    # rather than a native EDIT child. Their caret is the conservative fallback.
    return bool(info.hwndCaret) or "edit" in name.value.lower() or (
        compatibility and name.value.startswith(("Chrome_", "Mozilla", "Cef")))


def foreground():
    return ctypes.windll.user32.GetForegroundWindow()


logger = logging.getLogger(__name__)


class Injector:
    def __init__(self):
        self.keyboard = Controller()
        self.pending = False

    def insert(self, text, target, method="clipboard", compatibility=True):
        if not text:
            return
        if foreground() != target:
            raise RuntimeError("Focus changed. Text was not pasted.")
        if not has_text_focus(compatibility):
            raise RuntimeError("Focus an editable text field and try again.")
        if self.pending:
            raise RuntimeError("Clipboard busy. Try again.")
        if method == "typing":
            self.keyboard.type(text)
            return
        clipboard = QApplication.clipboard()
        old = clipboard.mimeData()
        saved = QMimeData()
        if old:
            for fmt in old.formats():
                saved.setData(fmt, old.data(fmt))
        clipboard.setText(text)
        self.pending = True

        def restore():
            try:
                if clipboard.text() == text:
                    clipboard.setMimeData(saved)
            except Exception:
                logger.exception("Clipboard restoration failed")
            finally:
                self.pending = False
        try:
            with self.keyboard.pressed(Key.ctrl):
                paste_key = KeyCode.from_vk(0x56)
                self.keyboard.press(paste_key)
                self.keyboard.release(paste_key)
        except Exception:
            restore()
            raise
        QTimer.singleShot(200, restore)
