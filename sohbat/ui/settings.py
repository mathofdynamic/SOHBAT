"""Compact, grouped desktop preferences."""
import logging
import threading
from pathlib import Path

import sounddevice as sd
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCursor, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sohbat.ui.combo import ComboBox
from sohbat.ui.switch import Switch
from sohbat.ui.typography import install_font


def pretty_shortcut(chord):
    names = {'<ctrl>': 'Ctrl', '<cmd>': 'Windows', '<alt>': 'Alt', '<shift>': 'Shift', '<space>': 'Space'}
    return ' + '.join(names.get(part, part.strip('<>').upper()) for part in chord.split('+'))


class Settings(QDialog):
    model_requested = Signal(str, int)
    def __init__(self, config, apply, pill=None):
        super().__init__()
        install_font(QApplication.instance())
        self.config, self.apply_changes, self.pill = config, apply, pill
        self.preview_pill = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.finish_preview)
        self.setWindowTitle('SOHBAT Settings')
        self.resize(680, 560)
        self.setMinimumSize(620, 500)
        self.setMaximumSize(840, 680)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        body = QHBoxLayout()
        body.setSpacing(0)
        outer.addLayout(body, 1)
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(154)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 26, 16, 18)
        brand = QLabel('SOHBAT')
        brand.setObjectName('brand')
        side.addWidget(brand)
        side.addWidget(self.note('Dictation, on device.'))
        side.addSpacing(26)
        self.navigation = QListWidget()
        self.navigation.addItems(['Recording', 'Text', 'Appearance', 'Models'])
        self.navigation.setAccessibleName('Settings categories')
        side.addWidget(self.navigation, 1)
        side.addWidget(self.note('English models\nOffline by design'))
        body.addWidget(sidebar)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)

        page = self.page('Recording', 'Choose how you start speaking and where we listen.')
        self.shortcut = QLineEdit(config.hotkey)
        self.shortcut.hide()
        self.shortcut_button = QPushButton(pretty_shortcut(config.hotkey))
        self.shortcut_button.setAccessibleName('Change recording shortcut')
        self.shortcut_button.clicked.connect(self.edit_shortcut)
        group = self.group(page)
        self.shortcut_hint = self.row(group, 'Keyboard shortcut', 'Hold to speak. Release to insert.', self.shortcut_button)
        self.mode = self.combo([('Hold to talk', 'hold'), ('Press to start / stop', 'toggle')], config.mode)
        self.row(group, 'Recording mode', 'Presses under 250 ms are ignored.', self.mode)
        group = self.group(page)
        self.mic = ComboBox()
        self.refresh_mics()
        self.mic.setCurrentIndex(max(0, self.mic.findData(config.mic_device)))
        self.row(group, 'Microphone', 'Uses your selected input device.', self.mic)
        refresh = QPushButton('Refresh devices')
        refresh.setObjectName('subtle')
        refresh.clicked.connect(self.refresh_mics)
        page.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignRight)
        page.addSpacing(8)
        page.addWidget(self.label('Try it here', 'section'))
        self.test_input = QLineEdit()
        self.test_input.setAccessibleName('Test dictation input')
        self.test_input.setPlaceholderText('Click here, hold your shortcut, and speak…')
        self.test_input.setMinimumHeight(42)
        page.addWidget(self.test_input)
        page.addWidget(self.note('Your words stay on this computer.'))
        page.addStretch()
        self.mode.currentIndexChanged.connect(self.update_recording_copy)
        self.update_recording_copy()

        page = self.page('Text', 'Keep the words you want. Insert them where you work.')
        group = self.group(page)
        self.paste = self.combo([('Clipboard paste', 'clipboard'), ('Simulated typing', 'typing')], config.paste_method)
        self.row(group, 'Insert using', 'Clipboard contents are restored after paste.', self.paste)
        self.compatibility = self.toggle(config.compatibility)
        self.row(group, 'Browser compatibility', 'Supports web and Electron editors.', self.compatibility)
        self.fillers = self.toggle(config.strip_fillers)
        self.row(group, 'Remove fillers', 'Remove “um” and “uh” from your text.', self.fillers)
        page.addWidget(self.note('Spacing, capitalization, and ending punctuation are cleaned up automatically.'))
        page.addSpacing(16)
        page.addWidget(self.label('Windows', 'section'))
        group = self.group(page)
        self.autostart = self.toggle(config.autostart)
        self.row(group, 'Open at sign-in', 'Ready when you start your day.', self.autostart)
        page.addStretch()

        page = self.page('Appearance', 'A quiet presence, only when you need it.')
        group = self.group(page)
        self.theme = self.combo([('System', 'system'), ('Light', 'light'), ('Dark', 'dark')], config.theme)
        self.row(group, 'Theme', 'Applies to this settings window.', self.theme)
        self.reduced_motion = self.toggle(config.reduced_motion)
        self.row(group, 'Reduce motion', 'Use a short fade instead of expansion.', self.reduced_motion)
        self.reduced_transparency = self.toggle(config.reduced_transparency)
        self.row(group, 'Reduce transparency', 'Use a more opaque recording overlay.', self.reduced_transparency)
        page.addSpacing(12)
        preview = QPushButton('Preview recording overlay')
        preview.clicked.connect(self.preview)
        page.addWidget(preview, alignment=Qt.AlignmentFlag.AlignLeft)
        page.addWidget(self.note('Appears while you speak. Keyboard focus stays in your app.'))
        page.addStretch()
        self.theme.currentIndexChanged.connect(self.update_theme)
        page = self.page('Models', 'A voice model that fits your workflow.')
        self.active_model = self.note(f'Active model: {self.model_name(config.model_arch)}')
        page.addWidget(self.active_model)
        group = self.group(page)
        self.models = self.combo([('Tiny Streaming', 2), ('Small Streaming', 4), ('Medium Streaming', 5)], config.model_arch)
        self.row(group, 'Speech model', 'English, on device', self.models)
        self.model_description = self.note('')
        self.models.currentIndexChanged.connect(self.update_model_description)
        page.addWidget(self.model_description)
        self.update_model_description()
        page.addSpacing(10)
        self.download_panel = QFrame()
        self.download_panel.setObjectName('group')
        progress_layout = QVBoxLayout(self.download_panel)
        progress_layout.setContentsMargins(16, 16, 16, 16)
        progress_layout.setSpacing(10)
        progress_header = QHBoxLayout()
        self.download_status = QLabel('Ready to download')
        self.download_status.setWordWrap(True)
        progress_header.addWidget(self.download_status, 1)
        self.download_percent = QLabel('')
        progress_header.addWidget(self.download_percent)
        progress_layout.addLayout(progress_header)
        self.download_progress = QProgressBar()
        self.download_progress.setAccessibleName('Model download progress')
        self.download_progress.setTextVisible(False)
        self.download_progress.setFixedHeight(6)
        self.download_progress.setRange(0, 1000)
        progress_layout.addWidget(self.download_progress)
        self.download_detail = self.note('Download once. Dictate offline.')
        progress_layout.addWidget(self.download_detail)
        page.addWidget(self.download_panel)
        self.download_panel.hide()
        self.download_button = QPushButton('Download and use')
        self.download_button.setObjectName('primary')
        self.download_button.clicked.connect(self.download_model)
        page.addWidget(self.download_button, alignment=Qt.AlignmentFlag.AlignLeft)
        page.addWidget(self.note('Model changes apply immediately. Internet is only needed to download.'))
        page.addStretch()
        self.navigation.setCurrentRow(0)

        footer = QFrame()
        footer.setObjectName('footer')
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(22, 12, 22, 12)
        self.feedback = QLabel('Changes apply when you save.')
        self.feedback.setObjectName('muted')
        self.feedback.setWordWrap(True)
        foot.addWidget(self.feedback, 1)
        close = QPushButton('Close')
        close.clicked.connect(self.hide)
        foot.addWidget(close)
        self.save = QPushButton('Save changes')
        self.save.setObjectName('primary')
        self.save.clicked.connect(self.submit)
        foot.addWidget(self.save)
        outer.addWidget(footer)
        self.navigation.currentRowChanged.connect(self.update_footer)
        self.update_theme()

    @staticmethod
    def label(text, name=''):
        widget = QLabel(text)
        widget.setObjectName(name)
        widget.setWordWrap(True)
        return widget

    @classmethod
    def note(cls, text):
        return cls.label(text, 'muted')

    def page(self, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(22, 20, 22, 12)
        layout.setSpacing(10)
        layout.addWidget(self.label(title, 'title'))
        layout.addWidget(self.note(subtitle))
        layout.addSpacing(8)
        self.pages.addWidget(widget)
        return layout

    @staticmethod
    def group(layout):
        frame = QFrame()
        frame.setObjectName('group')
        rows = QVBoxLayout(frame)
        rows.setContentsMargins(14, 2, 14, 2)
        rows.setSpacing(0)
        layout.addWidget(frame)
        return rows

    def row(self, group, title, subtitle, control):
        row = QHBoxLayout()
        row.setContentsMargins(0, 10, 0, 10)
        row.setSpacing(14)
        labels = QVBoxLayout()
        labels.setSpacing(4)
        label = self.label(title, 'rowTitle')
        label.setBuddy(control)
        labels.addWidget(label)
        hint = self.note(subtitle)
        labels.addWidget(hint)
        row.addLayout(labels, 1)
        control.setAccessibleName(title)
        if not isinstance(control, QCheckBox):
            control.setFixedWidth(192)
        row.addWidget(control)
        group.addLayout(row)
        return hint

    @staticmethod
    def combo(items, value):
        widget = ComboBox()
        for title, data in items:
            widget.addItem(title, data)
        widget.setCurrentIndex(max(0, widget.findData(value)))
        return widget

    @staticmethod
    def toggle(value):
        widget = Switch()
        widget.setChecked(value)
        return widget

    def refresh_mics(self):
        previous = self.mic.currentData()
        self.mic.clear()
        self.mic.addItem('System default', None)
        try:
            for index, device in enumerate(sd.query_devices()):
                if device['max_input_channels']:
                    self.mic.addItem(device['name'], index)
                    self.mic.setItemData(self.mic.count()-1, device['name'], Qt.ItemDataRole.ToolTipRole)
        except (sd.PortAudioError, OSError):
            self.mic.addItem('No microphone available', None)
        self.mic.setCurrentIndex(max(0, self.mic.findData(previous)))

    def update_recording_copy(self):
        toggle = self.mode.currentData() == 'toggle'
        self.shortcut_hint.setText('Press to start. Press again to insert.' if toggle else 'Hold to speak. Release to insert.')
        self.test_input.setPlaceholderText('Click here, press your shortcut, and speak…' if toggle else 'Click here, hold your shortcut, and speak…')

    def edit_shortcut(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Recording shortcut')
        dialog.setMinimumWidth(360)
        box = QVBoxLayout(dialog)
        box.setContentsMargins(22, 22, 22, 22)
        box.setSpacing(14)
        box.addWidget(self.label('Choose a shortcut', 'section'))
        box.addWidget(self.note('Press a key combination, or use Ctrl + Windows.'))
        capture = QKeySequenceEdit()
        capture.setAccessibleName('Capture keyboard shortcut')
        box.addWidget(capture)
        default = QPushButton('Use Ctrl + Windows')
        box.addWidget(default)
        def use_default():
            self.shortcut.setText('<ctrl>+<cmd>')
            dialog.accept()
        default.clicked.connect(use_default)
        use = QPushButton('Use shortcut')
        use.setObjectName('primary')
        use.setEnabled(False)
        box.addWidget(use)
        capture.keySequenceChanged.connect(lambda sequence: use.setEnabled(not sequence.isEmpty()))

        def captured():
            sequence = capture.keySequence().toString(QKeySequence.SequenceFormat.PortableText).split(',')[0]
            names = {'Ctrl': '<ctrl>', 'Alt': '<alt>', 'Shift': '<shift>', 'Meta': '<cmd>', 'Space': '<space>'}
            self.shortcut.setText('+'.join(names.get(part, f'<{part.lower()}>' if len(part)>1 else part.lower()) for part in sequence.split('+')))
            dialog.accept()
        use.clicked.connect(captured)
        dialog.exec()
        self.shortcut_button.setText(pretty_shortcut(self.shortcut.text()))

    def update_theme(self):
        dark = self.theme.currentData() == 'dark' or (self.theme.currentData() == 'system' and QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark)
        bg, sidebar, panel, text, muted, border, field, selection = (
            ('#1c1c1e', '#232326', '#2c2c2e', '#f5f5f7', '#b1b1b8', '#454549', '#37373a', '#323d55') if dark else
            ('#f5f5f7', '#ebebef', '#ffffff', '#202124', '#64646e', '#dcdce2', '#ffffff', '#dfe8fa'))
        chevron = (Path(__file__).resolve().parents[1] / "assets" / "chevron.svg").as_posix()
        action = '#66aaff' if dark else '#0066cc'
        self.setStyleSheet(f'''
            QDialog, QStackedWidget {{ background: {bg}; color: {text}; }}
            QWidget {{ color: {text}; font-family: 'Inter'; font-size: 12px; }}
            QFrame#sidebar {{ background: {sidebar}; border-right: 1px solid {border}; }}
            QLabel#brand {{ font-size: 21px; font-weight: 650; letter-spacing: -0.4px; }}
            QLabel#title {{ font-size: 23px; font-weight: 650; letter-spacing: -0.5px; }}
            QLabel#rowTitle, QLabel#section {{ font-weight: 600; }}
            QLabel#muted {{ color: {muted}; font-size: 11px; }}
            QFrame#group {{ background: {panel}; border: 1px solid {border}; border-radius: 11px; }}
            QFrame#group QLabel, QFrame#group QCheckBox {{ background: transparent; border: none; }}
            QFrame#footer {{ background: {bg}; border-top: 1px solid {border}; }}
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ padding: 10px 8px; border-radius: 7px; margin-bottom: 4px; }}
            QListWidget::item:selected {{ background: {selection}; color: {text}; font-weight: 600; }}
            QListWidget::item:hover {{ background: {selection}; }}
            QListWidget::item:focus {{ border: 1px solid #007aff; }}
            QLineEdit, QComboBox, QKeySequenceEdit {{ background: {field}; border: 1px solid {border}; border-radius: 7px; padding: 8px; selection-background-color: #0069d9; placeholder-text-color: {muted}; }}
            QLineEdit:focus, QComboBox:focus, QKeySequenceEdit:focus {{ border: 1px solid #007aff; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{ image: url({chevron}); width: 12px; height: 8px; }}
            QComboBox QAbstractItemView {{ background: {panel}; color: {text}; selection-background-color: {selection}; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; border: 1px solid {muted}; border-radius: 6px; background: {field}; }}
            QCheckBox::indicator:checked {{ background: #007aff; border: 1px solid #007aff; image: url(none); }}
            QCheckBox:focus {{ outline: 2px solid #007aff; }}
            QPushButton {{ background: {field}; color: {text}; border: 1px solid {border}; border-radius: 7px; padding: 8px 12px; font-weight: 500; }}
            QProgressBar {{ border: none; background: {border}; border-radius: 3px; }}
            QProgressBar::chunk {{ background: #007aff; border-radius: 3px; }}
            QPushButton:hover {{ border-color: #007aff; }}
            QPushButton:pressed {{ background: {selection}; }}
            QPushButton:focus {{ border: 2px solid #007aff; padding: 7px 11px; }}
            QPushButton#primary {{ background: #0069d9; color: white; border-color: #0069d9; }}
            QPushButton#primary:hover {{ background: #005bbb; }}
            QPushButton#primary:focus {{ border: 2px solid {text}; padding: 7px 11px; }}
            QPushButton:disabled {{ color: {muted}; }}
            QPushButton#primary:disabled {{ background: {border}; color: {muted}; border-color: {border}; }}
            QPushButton#subtle {{ border: 1px solid transparent; color: {action}; background: transparent; padding: 4px 6px; }}
            QPushButton#subtle:focus {{ border: 2px solid {action}; padding: 3px 5px; }}
        ''')

    def preview(self):

        from sohbat.ui.pill import Pill
        if self.preview_pill is None:
            self.preview_pill = Pill()
        self.preview_pill.configure(self.reduced_motion.isChecked(), self.reduced_transparency.isChecked())
        self.preview_pill.show_state('listening', 'Recording overlay preview')
        self.preview_pill.level = .45
        self.preview_timer.start(1500)

    def finish_preview(self):
        if self.preview_pill is not None:
            self.preview_pill.show_state('done', 'Preview complete')

    def hideEvent(self, event):
        self.preview_timer.stop()
        if self.preview_pill is not None:
            self.preview_pill.hide()
        super().hideEvent(event)

    @Slot()
    def open_preferences(self):
        was_hidden = not self.isVisible()
        self.showNormal()
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is not None and (was_hidden or not screen.availableGeometry().intersects(self.frameGeometry())):
            bounds = screen.availableGeometry()
            self.move(bounds.center()-self.rect().center())
        self.raise_()
        self.activateWindow()
        logging.getLogger(__name__).info('Settings opened: visible=%s', self.isVisible())

    @staticmethod
    def model_name(arch):
        return {2: 'Tiny Streaming', 4: 'Small Streaming', 5: 'Medium Streaming'}.get(arch, 'Speech model')

    def update_footer(self, row):
        self.save.setVisible(row != 3)
        self.feedback.setText('Model changes are saved automatically.' if row == 3 else 'Changes apply when you save.')

    def update_model_description(self):
        self.model_description.setText({2: 'Fastest response. Lowest memory use.', 4: 'A balance of recognition quality and speed.', 5: 'Highest recognition quality. Uses more memory.'}[self.models.currentData()])

    def download_model(self):
        self.downloading_arch = self.models.currentData()
        self.download_button.setEnabled(False)
        self.download_button.setText('Downloading...')
        self.models.setEnabled(False)
        self.download_panel.show()
        self.download_status.setText('Preparing download')
        self.download_percent.setText('')
        self.download_progress.setRange(0, 0)
        self.download_detail.setText('Checking model files...')
        self.download_task = ModelDownload(self.downloading_arch, self)
        self.download_task.progress.connect(self.show_download_progress)
        self.download_task.ready.connect(self.model_downloaded)
        self.download_task.failed.connect(self.show_model_result)
        self.download_task.start()

    def show_download_progress(self, value, message):
        self.download_progress.setRange(0, 1000)
        self.download_progress.setValue(round(max(0, min(1, value)) * 1000))
        self.download_status.setText(f'Downloading {self.model_name(self.downloading_arch)}')
        self.download_percent.setText(f'{max(0, min(1, value)):.0%}')
        self.download_detail.setText('Keep SOHBAT open. Your current model stays available.')

    def model_downloaded(self, path, arch):
        self.download_progress.setRange(0, 0)
        self.download_percent.setText('')
        self.download_status.setText('Loading your model')
        self.download_detail.setText('The download is complete. Preparing offline dictation...')
        self.download_button.setText('Loading...')
        self.model_requested.emit(path, arch)

    def show_model_result(self, message):
        success = message.startswith('Model ready')
        self.download_progress.setRange(0, 1000)
        self.download_progress.setValue(1000 if success else 0)
        self.download_percent.setText('100%' if success else '')
        self.download_status.setText('Ready for dictation' if success else 'Could not switch models')
        self.download_detail.setText('Your model is saved and ready to use offline.' if success else message)
        if success:
            self.active_model.setText(f'Active model: {self.model_name(self.config.model_arch)}')
        self.models.setEnabled(True)
        self.download_button.setEnabled(True)
        self.download_button.setText('Download and use' if success else 'Try again')

    def submit(self):
        try:
            appearance = {'theme': self.theme.currentData(), 'reduced_motion': self.reduced_motion.isChecked(), 'reduced_transparency': self.reduced_transparency.isChecked()}
            self.apply_changes(self.shortcut.text(), self.mode.currentData(), self.mic.currentData(), self.paste.currentData(), self.fillers.isChecked(), self.autostart.isChecked(), self.compatibility.isChecked(), appearance)
            self.feedback.setText('Saved. Your preferences are active.')
        except Exception as error:
            logging.getLogger(__name__).exception('Could not save preferences')
            self.feedback.setText(f'Could not save: {error}')


class ModelDownload(QObject):
    finished = Signal()

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()
    progress = Signal(float, str)
    ready = Signal(str, int)
    failed = Signal(str)

    def __init__(self, arch, parent):
        super().__init__(parent)
        self.arch = arch

    def run(self):
        try:
            from moonshine_voice import ModelArch
            from moonshine_voice.download import get_model_for_language

            from sohbat.config import ROOT
            path, arch = get_model_for_language('en', ModelArch(self.arch), cache_root=ROOT/'models', on_progress=self.progress.emit)
            self.ready.emit(str(path), int(arch))
        except Exception as error:
            logging.getLogger(__name__).exception('Model download failed')
            self.failed.emit(f'Download failed: {error}')
        finally:
            self.finished.emit()
