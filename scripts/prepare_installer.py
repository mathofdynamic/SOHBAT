"""Validate and stage the offline model, artwork and notices for Inno Setup."""
import base64
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import google_crc32c
from moonshine_voice import ModelArch
from moonshine_voice.download import _stt_dependency_manifest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

from sohbat import __version__
from sohbat.config import Config

stage = Path('.perfection/installer-payload').resolve()
stage.mkdir(parents=True, exist_ok=True)
config = Config.load()
source = Path(config.model_path) if config.model_path else Path('models/tiny-streaming-en')
if not source.is_dir():
    raise SystemExit('English model missing. Run scripts/download-model.ps1 before building.')
manifest = _stt_dependency_manifest('en', ModelArch.TINY_STREAMING)
model_dest = stage/'models'/'tiny-streaming-en'
model_dest.mkdir(parents=True, exist_ok=True)
for item in manifest['groups'][0]['files']:
    path = source/item['name']
    payload = path.read_bytes()
    actual = base64.b64encode(google_crc32c.Checksum(payload).digest()).decode()
    if len(payload) != item['size'] or actual != item['checksum']:
        raise SystemExit(f'Model integrity mismatch: {item["name"]}')
    shutil.copy2(path, model_dest/path.name)
(stage/'model-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
banner = QImage('docs/assets/banner.png')
if banner.isNull() or not banner.scaledToWidth(1800, Qt.TransformationMode.SmoothTransformation).save(str(stage/'banner.bmp')):
    raise SystemExit('Could not prepare banner bitmap')
logo = QImage('sohbat/assets/brand/logo.png')
small = QImage(128, 128, QImage.Format.Format_RGB32)
small.fill(QColor('white'))
painter = QPainter(small)
painter.drawImage(small.rect(), logo)
painter.end()
if not small.save(str(stage/'logo.bmp')):
    raise SystemExit('Could not prepare wizard logo')
notices = stage/'licenses'
notices.mkdir(exist_ok=True)
for dist in importlib.metadata.distributions():
    package = dist.metadata.get('Name', 'unknown')
    for file in dist.files or []:
        name = Path(str(file)).name.lower()
        if name.startswith(('license', 'copying', 'notice')) or 'licenses' in str(file).lower().split('/'):
            actual_path = Path(dist.locate_file(file))
            if actual_path.is_file():
                destination = notices/package/str(file)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(actual_path, destination)
python_license = Path(sys.base_prefix)/'LICENSE.txt'
if python_license.is_file():
    shutil.copy2(python_license, notices/'Python-LICENSE.txt')
print(__version__)
