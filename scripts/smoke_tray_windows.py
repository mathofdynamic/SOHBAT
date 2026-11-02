"""Drive the installed app's Qt 6.10 Windows tray callback and verify Settings."""
import ctypes
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sohbat.config import ROOT

user = ctypes.windll.user32
user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user.IsWindowVisible.argtypes = [wintypes.HWND]
user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
user.IsIconic.argtypes = [wintypes.HWND]
callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, ctypes.c_ssize_t)
user.EnumWindows.argtypes = [callback_type, ctypes.c_ssize_t]
pid = int((ROOT/'instance.lock').read_text(encoding='utf-8').splitlines()[0])


def windows():
    found = {}

    @callback_type
    def visit(hwnd, parameter):
        owner = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            text = ctypes.create_unicode_buffer(256)
            user.GetWindowTextW(hwnd, text, len(text))
            if text.value == 'QTrayIconMessageWindow':
                found['tray'] = hwnd
            elif text.value.startswith('SOHBAT Settings'):
                found['settings'] = hwnd
        return True
    user.EnumWindows(visit, 0)
    return found


before = windows()
assert 'tray' in before, 'Installed SOHBAT tray was not found'
# Qt 6.10.3 qwindowssystemtrayicon.cpp: WM_APP+101, icon id 0,
# NIN_SELECT=WM_USER. This exercises the installed native notification path.
user.PostMessageW(before['tray'], 0x8000+101, 0, 0x400)
time.sleep(.3)
after = windows()
settings = after.get('settings', 0)
report = {'pid': pid, 'settings_visible': bool(settings and user.IsWindowVisible(settings)),
          'settings_restored': bool(settings and not user.IsIconic(settings))}
print(json.dumps(report, indent=2))
assert report['settings_visible'] and report['settings_restored']
