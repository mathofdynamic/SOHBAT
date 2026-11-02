"""Generate Windows version resources from the app's single version source."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sohbat import __version__

parts = tuple(int(value) for value in __version__.split('.'))
version = (parts + (0, 0, 0, 0))[:4]
resource = f'''VSVersionInfo(
 ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r},
  mask=0x3f, flags=0, OS=0x40004, fileType=0x1, subtype=0, date=(0,0)),
 kids=[StringFileInfo([StringTable('040904B0', [
  StringStruct('CompanyName', 'Mohammad H Mohammady'),
  StringStruct('FileDescription', 'SOHBAT offline dictation'),
  StringStruct('FileVersion', '{__version__}'),
  StringStruct('InternalName', 'SOHBAT'),
  StringStruct('OriginalFilename', 'SOHBAT.exe'),
  StringStruct('ProductName', 'SOHBAT'),
  StringStruct('ProductVersion', '{__version__}'),
  StringStruct('LegalCopyright', 'Copyright 2026 Mohammad H Mohammady; MIT')
 ])]), VarFileInfo([VarStruct('Translation', [1033,1200])])])
'''
Path('build').mkdir(exist_ok=True)
Path('build/version-info.txt').write_text(resource, encoding='utf-8')
