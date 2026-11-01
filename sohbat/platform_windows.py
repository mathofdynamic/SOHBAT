"""Windows-specific startup registration."""
import subprocess
import sys
import winreg
from pathlib import Path


def set_autostart(enabled: bool) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                          r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
        try:
            winreg.DeleteValue(key, 'Flowlet')
        except FileNotFoundError:
            pass
        if enabled:
            args = [sys.executable] if getattr(sys, 'frozen', False) else [
                sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts' / 'launch.py')]
            command = subprocess.list2cmdline(args)
            winreg.SetValueEx(key, 'SOHBAT', 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, 'SOHBAT')
            except FileNotFoundError:
                pass
