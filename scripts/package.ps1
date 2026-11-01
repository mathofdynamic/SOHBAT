$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/.."
& .venv/Scripts/python -m pip install pyinstaller
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& .venv/Scripts/python -m PyInstaller --noconfirm --windowed --name SOHBAT --icon sohbat/assets/brand/app.ico --add-data "sohbat/assets;sohbat/assets" --collect-all moonshine_voice --collect-submodules comtypes.gen scripts/launch.py
exit $LASTEXITCODE
