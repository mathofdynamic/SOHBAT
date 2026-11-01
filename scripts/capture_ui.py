"""Capture native Qt views, transparency, timing, interruption and focus evidence."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontInfo
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from sohbat.config import Config
from sohbat.inject import foreground
from sohbat.ui.pill import Pill
from sohbat.ui.settings import Settings

out = Path(sys.argv[1] if len(sys.argv)>1 else '.perfection/island-round-1')
out.mkdir(parents=True, exist_ok=True)
app = QApplication([])
pill = Pill()
settings = Settings(Config.load(), lambda *args: None, pill)
settings.show()
app.processEvents()
report = {'actual_sizes': {}, 'font': QFontInfo(app.font()).family(), 'preferences': [], 'motion': []}
for theme in ['light', 'dark']:
    settings.theme.setCurrentIndex(settings.theme.findData(theme))
    for size in [(680,560), (620,500)]:
        settings.resize(*size)
        for page in range(3):
            settings.navigation.setCurrentRow(page)
            app.processEvents()
            path = f'{theme}-{size[0]}-page{page}.png'
            settings.grab().save(str(out/path))
            report['preferences'].append(path)
            report['actual_sizes'][path] = [settings.width(), settings.height()]
settings.resize(680,560)
settings.navigation.setCurrentRow(0)
settings.save.setFocus()
app.processEvents()
settings.grab().save(str(out/'keyboard-focus-save.png'))
from PySide6.QtWidgets import QPushButton
refresh = next(button for button in settings.findChildren(QPushButton) if button.text() == 'Refresh devices')
refresh.setFocus()
app.processEvents()
settings.grab().save(str(out/'keyboard-focus-refresh.png'))
settings.mode.setCurrentIndex(settings.mode.findData('toggle'))
app.processEvents()
settings.grab().save(str(out/'toggle-mode.png'))
settings.mode.setCurrentIndex(settings.mode.findData('hold'))

def fail(*args):
    raise ValueError('Choose a valid keyboard shortcut.')
settings.apply_changes = fail
settings.submit()
app.processEvents()
settings.grab().save(str(out/'save-error.png'))
from PySide6.QtCore import QTimer

def capture_shortcut():
    modal = app.activeModalWidget()
    if modal:
        modal.grab().save(str(out/'shortcut-dialog.png'))
        modal.reject()

QTimer.singleShot(100, capture_shortcut)
settings.edit_shortcut()
settings.hide()

host = QWidget()
host.setWindowTitle('SOHBAT verification backdrop')
host.setStyleSheet('QWidget {background: #d4dbea;} QLineEdit { background: white; color: #202124; font: 14px Inter; padding: 12px; }')
layout = QVBoxLayout(host)
field = QLineEdit('Backdrop text remains behind the translucent overlay')
layout.addWidget(field)
pill.show_state('listening')
host.setGeometry(pill.geometry().adjusted(-10,-12,10,12))
host.show()
host.activateWindow()
field.setFocus()
app.processEvents()
before_focus = foreground()
pill.raise_()
QTest.qWait(200)
report['focus_unchanged'] = foreground() == before_focus
report['click_through'] = bool(pill.windowFlags() & Qt.WindowType.WindowTransparentForInput)
report['nonactivating'] = bool(pill.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus)
for state, text in [('listening','A small thought becomes a sentence.'), ('processing',''), ('done','Inserted'), ('error','Microphone unavailable. Choose another input.')]:
    pill.show_state(state,text)
    pill.dismiss.stop()
    pill.level=.6
    QTest.qWait(320)
    pixmap = pill.grab()
    pixmap.save(str(out/f'pill-{state}.png'))
    if state == 'listening':
        report['outer_corner_alpha'] = pixmap.toImage().pixelColor(0,0).alpha()
        report['surface_alpha'] = pixmap.toImage().pixelColor(pill.width()//2,20).alpha()
    composite = host.grab()
    from PySide6.QtGui import QPainter
    painter = QPainter(composite)
    painter.drawPixmap(10,12,pill.grab())
    painter.end()
    composite.save(str(out/f'composite-{state}.png'))
pill.configure(True,True)
pill.show_state('listening','Reduced motion and transparency')
QTest.qWait(180)
pill.grab().save(str(out/'pill-reduced.png'))
pill.show_state('processing')
pill.dismiss.stop()
QTest.qWait(200)
phase = pill.phase
pill.grab().save(str(out/'reduced-processing-1.png'))
QTest.qWait(200)
pill.grab().save(str(out/'reduced-processing-2.png'))
report['reduced_phase_change'] = pill.phase-phase
pill.hide()
pill.configure(False,False)
pill.show_state('listening','Interruptible expansion')
start = time.perf_counter()
for frame in range(30):
    QTest.qWait(16)
    if frame == 5:
        pill.fade_out()
    if frame == 8:
        before = pill.width_spring.value
        velocity = pill.width_spring.velocity
        pill.show_state('listening','Reopened during exit')
        report['retarget_position_jump'] = pill.width_spring.value-before
        report['retarget_velocity_jump'] = pill.width_spring.velocity-velocity
    if frame in (0,3,5,7,8,10,14,20,29):
        pill.grab().save(str(out/f'motion-{frame:02}.png'))
    report['motion'].append({'ms':round((time.perf_counter()-start)*1000,2),'width':pill.width_spring.value,'alpha':pill.alpha.value})
pill.show_state('done','Paused')
QTest.qWait(400)
report['informational_status_visible_at_400_ms'] = pill.isVisible()
pill.grab().save(str(out/'pill-paused.png'))
pill.show_state('done','Inserted')
start = time.perf_counter()
while pill.isVisible() and time.perf_counter()-start < 1:
    QTest.qWait(10)
report['done_to_hidden_ms'] = (time.perf_counter()-start)*1000
report['idle_timer_stopped'] = not pill.timer.isActive()
report['hidden_after_done'] = not pill.isVisible()
(out/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('motion','preferences')},indent=2))
host.close()
