# Third-party software

SOHBAT is MIT-licensed. This distribution includes software with separate licenses, including Python, Qt/PySide6, Moonshine Voice and its English Tiny Streaming model, NumPy/SciPy, sounddevice/PortAudio, pynput, comtypes and Inter.

The `licenses` directory contains license/notice files collected from the build's installed distributions, including development packages whose code may not be present in the executable. Inter's OFL is also alongside the font. Moonshine's MIT notice is included separately.

Qt/PySide6 components are dynamically linked in the `_internal` directory. Their LGPL licenses and applicable exceptions remain in force; SOHBAT's MIT license does not replace them. The directory-based app layout allows the Qt/PySide6 DLLs to be replaced with compatible modified versions. The corresponding Qt 6.10.3 and PySide6 6.10.3 source releases are available from the Qt project:

- https://download.qt.io/archive/qt/6.10/6.10.3/single/
- https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.3-src/
- https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.10.3

Source code and build instructions for SOHBAT: https://github.com/mathofdynamic/SOHBAT
