"""Render preferences, overlay states and motion evidence to local PNGs."""
import runpy
import sys
from pathlib import Path

sys.argv = [__file__, '.perfection/screenshots']
runpy.run_path(str(Path(__file__).with_name('capture_ui.py')), run_name='__main__')
