import ctypes
import logging
import queue
import sys
import threading
import time
from dataclasses import replace
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QLockFile, QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from sohbat.audio import Microphone
from sohbat.config import ROOT, Config
from sohbat.hotkey import GlobalHotkey
from sohbat.inject import Injector, foreground
from sohbat.platform_windows import set_autostart
from sohbat.polish import polish
from sohbat.ui.pill import Pill
from sohbat.ui.settings import Settings
from sohbat.ui.tray import make_tray
from sohbat.ui.typography import install_font

logger = logging.getLogger(__name__)


class Events(QObject):
    state = Signal(str, str)
    result = Signal(str, object)
    level = Signal(float)
    reset = Signal()


class Worker(threading.Thread):
    def __init__(self, config, events):
        super().__init__(daemon=True)
        self.config, self.events = config, events
        self.commands: queue.Queue = queue.Queue()

    def run(self):
        engine = None
        mic = Microphone()
        active = False
        target = 0
        started = 0.0
        try:
            from sohbat.engine.moonshine_engine import MoonshineEngine
            engine = MoonshineEngine(self.config.model_path)
            logger.info("Model ready")
            while True:
                try:
                    command, value = self.commands.get(timeout=.02 if active else None)
                except queue.Empty:
                    command, value = "audio", None
                if command == "quit":
                    break
                try:
                    if command == "start" and not active:
                        target = value
                        mic.start(self.config.mic_device)
                        engine.start_stream()
                        active, started = True, time.monotonic()
                        self.events.state.emit("listening", "")
                    if active:
                        samples = mic.drain()
                        if len(samples):
                            engine.feed_audio(samples)
                        self.events.level.emit(mic.level)
                        if mic.error:
                            raise RuntimeError(mic.error)
                        self.events.state.emit("listening", engine.partial_text())
                        if time.monotonic() - started >= 300:
                            command = "stop"
                            self.events.reset.emit()
                            self.events.state.emit("error", "Five-minute limit reached")
                        if command in ("stop", "cancel"):
                            released = time.perf_counter()
                            mic.stop()
                            remaining = mic.drain()
                            if len(remaining):
                                engine.feed_audio(remaining)
                            active = False
                            self.events.state.emit("processing", "")
                            text = engine.finalize()
                            logger.info("Finalize %.1f ms", (time.perf_counter()-released)*1000)
                            if command == "stop":
                                self.events.result.emit(polish(text, self.config.strip_fillers), target)
                            else:
                                self.events.state.emit("done", "Short tap ignored")
                except Exception as error:
                    logger.exception("Dictation failed")
                    try:
                        mic.stop()
                    except Exception:
                        logger.exception("Microphone cleanup failed")
                    active = False
                    try:
                        engine.finalize()
                    except Exception:
                        logger.exception("Stream cleanup failed")
                    self.events.state.emit("error", str(error))
        except Exception as error:
            logger.exception("Startup failed")
            self.events.state.emit("error", str(error))
        finally:
            try:
                mic.stop()
            except Exception:
                logger.exception("Microphone shutdown failed")
            if engine:
                engine.close()


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(
        ROOT / "sohbat.log", maxBytes=1_000_000, backupCount=3)],
        format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    install_font(app)
    app.setQuitOnLastWindowClosed(False)
    pill = Pill()
    lock = QLockFile(str(ROOT / "instance.lock"))
    if not lock.tryLock(0):
        pill.show_state("error", "SOHBAT is already running")
        QTimer.singleShot(4500, app.quit)
        return app.exec()
    try:
        config = Config.load()
    except Exception:
        logger.exception("Invalid configuration")
        config = Config()
    pill.configure(config.reduced_motion, config.reduced_transparency)
    events = Events()
    events.state.connect(pill.show_state)
    events.level.connect(lambda value: setattr(pill, "level", value))
    worker = Worker(config, events)
    injector = Injector()
    paused = False

    def command(action):
        if not paused:
            worker.commands.put((action, foreground()))

    try:
        hotkey = GlobalHotkey(config.hotkey, config.mode, command)
    except Exception:
        logger.exception("Invalid hotkey; reverting to default")
        hotkey = GlobalHotkey(Config().hotkey, "hold", command)
        pill.show_state("error", "Hotkey reset to Ctrl+Alt+Space")
    events.reset.connect(lambda: hotkey.reset())

    def insert(text, target):
        if any(ctypes.windll.user32.GetAsyncKeyState(key) & 0x8000 for key in (0x11, 0x12, 0x10, 0x5B, 0x5C)):
            QTimer.singleShot(30, lambda: insert(text, target))
            return
        try:
            injector.insert(text, target, config.paste_method, config.compatibility)
            pill.show_state("done", "Inserted" if text else "No speech detected")
        except Exception as error:
            logger.exception("Insertion failed")
            pill.show_state("error", str(error))
    events.result.connect(insert)

    def apply(chord, mode, mic, paste, fillers, autostart, compatibility, appearance=None):
        nonlocal hotkey
        replacement = None
        try:
            candidate = replace(config, hotkey=chord, mode=mode, mic_device=mic,
                                paste_method=paste, strip_fillers=fillers,
                                autostart=autostart, compatibility=compatibility, **(appearance or {}))
            replacement = GlobalHotkey(chord, mode, command)
            set_autostart(autostart)
            candidate.save()
        except Exception:
            logger.exception("Settings failed")
            if replacement is not None:
                replacement.close()
            set_autostart(config.autostart)
            raise
        worker.commands.put(("cancel", None))
        hotkey.close()
        hotkey = replacement
        config.__dict__.update(candidate.__dict__)
        pill.configure(config.reduced_motion, config.reduced_transparency)
    settings = Settings(config, apply, pill)

    def pause():
        nonlocal paused
        paused = not paused
        hotkey.reset()
        worker.commands.put(("cancel", None))
        pill.show_state("done", "Paused" if paused else "Resumed")
    _tray, _menu = make_tray(settings.open_preferences, pause, app.quit)
    worker.start()
    result = app.exec()
    hotkey.close()
    worker.commands.put(("quit", None))
    worker.join(10)
    lock.unlock()
    return result
