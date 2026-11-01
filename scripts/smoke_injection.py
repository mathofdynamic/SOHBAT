import sys
import ctypes
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLineEdit
from sohbat.inject import Injector, foreground

app = QApplication([])
field = QLineEdit()
field.setWindowTitle('SOHBAT injection smoke test')
field.resize(500, 70)
field.show()
field.activateWindow()
field.setFocus()
injector = Injector()
result = [1]

def paste():
    ctypes.windll.user32.SetForegroundWindow(ctypes.c_void_p(int(field.winId())))
    field.activateWindow()
    field.setFocus()
    app.processEvents()
    assert foreground() == int(field.winId()), "Test window did not receive foreground focus"
    app.clipboard().setText('clipboard sentinel')
    injector.insert('SOHBAT insertion verified.', int(field.winId()))
    QTimer.singleShot(500, verify)

def verify():
    assert field.text() == 'SOHBAT insertion verified.', repr(field.text())
    assert app.clipboard().text() == 'clipboard sentinel'
    print('PASS: focused Qt input received paste; clipboard restored')
    result[0] = 0
    app.quit()

QTimer.singleShot(800, paste)
QTimer.singleShot(5000, app.quit)
app.exec()
raise SystemExit(result[0])
